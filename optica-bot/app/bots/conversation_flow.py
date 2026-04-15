# app/bots/conversation_flow.py
from enum import Enum
from typing import Dict, Any, Optional
from app.bots import responses
from app.schemas.prescription import Receta
from app.schemas.order import PedidoCreate
from app.schemas.payment import PagoConfirmacion
from app.api.v1.endpoints.payments import confirmar_pago
from app.services import order_service
import re

class BotState(Enum):
    START = "START"
    AWAITING_NAME = "AWAITING_NAME"
    AWAITING_MONTURA = "AWAITING_MONTURA"
    AWAITING_LENTE = "AWAITING_LENTE"
    AWAITING_RECETA = "AWAITING_RECETA"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"

class ConversationManager:
    def __init__(self):
        # En memoria para este MVP
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_session(self, phone: str) -> Dict[str, Any]:
        if phone not in self.sessions:
            self.sessions[phone] = {
                "state": BotState.START,
                "data": {}
            }
        return self.sessions[phone]

    def process_message(self, phone: str, message: str) -> str:
        session = self.get_session(phone)
        state = session["state"]
        msg = message.strip()

        if state == BotState.START:
            session["state"] = BotState.AWAITING_NAME
            return responses.BIENVENIDA

        elif state == BotState.AWAITING_NAME:
            session["data"]["nombre"] = msg
            session["state"] = BotState.AWAITING_MONTURA
            return responses.PEDIR_MONTURA.format(nombre=msg)

        elif state == BotState.AWAITING_MONTURA:
            session["data"]["montura"] = msg
            session["state"] = BotState.AWAITING_LENTE
            return responses.PEDIR_LENTE

        elif state == BotState.AWAITING_LENTE:
            lente_map = {"1": "Monofocal básico", "2": "Progresivo Premium", "3": "Alto índice (1.67)"}
            tipo = lente_map.get(msg) or msg
            session["data"]["tipo_lente"] = tipo
            session["state"] = BotState.AWAITING_RECETA
            return responses.PEDIR_RECETA

        elif state == BotState.AWAITING_RECETA:
            # Mock de parseo de receta simple
            session["data"]["receta"] = Receta(
                od_esfera=-1.0, od_cilindro=-0.5, od_eje=180,
                oi_esfera=-1.0, oi_cilindro=-0.5, oi_eje=180,
                dp=62
            )
            session["state"] = BotState.AWAITING_CONFIRMATION
            total = 120.0 if "progresivo" in session["data"]["tipo_lente"].lower() else 60.0
            session["data"]["total"] = total
            
            return responses.RESUMEN_PEDIDO.format(
                nombre=session["data"]["nombre"],
                montura=session["data"]["montura"],
                lente=session["data"]["tipo_lente"],
                total=total
            )

        elif state == BotState.AWAITING_CONFIRMATION:
            if "si" in msg.lower():
                # Crear el pedido real en el sistema
                data = session["data"]
                pedido_obj = PedidoCreate(
                    paciente_nombre=data["nombre"],
                    telefono=phone,
                    montura=data["montura"],
                    tipo_lente=data["tipo_lente"],
                    total_cliente=data["total"],
                    receta=data["receta"]
                )
                pedido = order_service.crear_nuevo_pedido(pedido_obj)
                session["data"]["pedido_id"] = pedido["id"]
                
                session["state"] = BotState.AWAITING_PAYMENT
                return responses.INSTRUCCIONES_PAGO.format(total=session["data"]["total"])
            else:
                return "Si hay algún error, dime qué quieres cambiar. O responde 'SÍ' si todo está bien."

        elif state == BotState.AWAITING_PAYMENT:
            # Simulación: Extraer un número del mensaje como si fuera el monto abonado
            # En producción, esto vendría de una validación de comprobante
            monto_match = re.search(r"(\d+(\.\d+)?)", msg)
            if not monto_match:
                return "Por favor, indica el monto que has transferido y el número de operación."
            
            monto_abonado = float(monto_match.group(1))
            pedido_id = session["data"]["pedido_id"]
            
            # Llamar a la lógica de pagos
            pago_data = PagoConfirmacion(
                pedido_id=pedido_id,
                metodo="whatsapp_transfer",
                referencia=msg, # Usamos el texto como referencia
                monto=monto_abonado
            )
            resultado = confirmar_pago(pago_data)
            
            # Preparar respuesta basada en el resultado
            if resultado["pedido_estado"] == "PAGADO":
                session["state"] = BotState.START
                return responses.GRACIAS_PAGO
            else:
                msg_lab = "🚀 Tu pedido ha sido enviado al laboratorio." if resultado["orden_laboratorio"] else "⏳ Tu pedido se enviará al laboratorio cuando alcances el 50% del pago."
                return responses.CONFIRMACION_ABONO.format(
                    monto=monto_abonado,
                    saldo=resultado["saldo_restante"],
                    mensaje_adicional=msg_lab
                )

        return "Lo siento, no entendí eso. ¿Podemos empezar de nuevo? Di 'Hola'."

# Instancia única para el bot
manager = ConversationManager()
