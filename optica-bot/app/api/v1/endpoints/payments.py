from datetime import datetime
from dataclasses import asdict
from app.core.config import APIRouter, HTTPException
from app.schemas.payment import PagoConfirmacion
from app.models.order import EstadoPedido
from app.crud.order import pedidos, estados_pedido
from app.crud.lab_order import ordenes_lab
from app.crud.payment import pagos
from app.services.laboratory_router import seleccionar_laboratorio

router = APIRouter()

@router.post("/pago/confirmar")
def confirmar_pago(data: PagoConfirmacion):
    pedido = next((p for p in pedidos if p["id"] == data.pedido_id), None)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    # Actualizar saldos
    data.monto = float(data.monto)
    pedido["monto_pagado"] += data.monto
    pedido["saldo"] = max(0, pedido["total_cliente"] - pedido["monto_pagado"])
    
    # Determinar nuevo estado del pedido
    if pedido["saldo"] == 0:
        pedido["estado"] = "PAGADO"
    else:
        pedido["estado"] = "ABONADO"

    # Verificar si se debe enviar al laboratorio (Mínimo 50% y solo una vez)
    ya_enviado = any(o["pedido_id"] == pedido["id"] for o in ordenes_lab)
    umbral_laboratorio = pedido["total_cliente"] * 0.50
    
    orden_lab = None
    if not ya_enviado and pedido["monto_pagado"] >= umbral_laboratorio:
        laboratorio = seleccionar_laboratorio(
            pedido["tipo_lente"], 
            pedido.get("tratamiento")
        )
        
        orden_lab = {
            "id": len(ordenes_lab) + 1,
            "pedido_id": pedido["id"],
            "laboratorio": laboratorio,
            "estado": "ENVIADO",
            "costo": round(pedido["total_cliente"] * 0.35, 2), # Costo estimado para el dashboard
            "fecha_envio": datetime.now().isoformat(),
        }
        ordenes_lab.append(orden_lab)
        estados_pedido.append(
            EstadoPedido(pedido["id"], "ENVIADO_LABORATORIO", datetime.now().isoformat())
        )

    pagos.append(asdict(data))
    
    return {
        "mensaje": "Pago registrado con éxito",
        "pedido_estado": pedido["estado"],
        "saldo_restante": pedido["saldo"],
        "orden_laboratorio": orden_lab
    }
