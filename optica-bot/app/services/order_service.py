from datetime import datetime
from typing import Optional
from app.schemas.order import PedidoCreate
from app.models.patient import Cliente
from app.models.order import EstadoPedido
from app.crud.patient import clientes
from app.crud.order import pedidos, estados_pedido

def crear_nuevo_pedido(data: PedidoCreate) -> dict:
    """
    Crea un pedido en el sistema a partir de datos validados.
    """
    cliente_id = len(clientes) + 1
    cliente = Cliente(cliente_id, data.paciente_nombre, data.telefono)
    clientes.append(cliente)

    pedido_id = len(pedidos) + 1
    pedido = {
        "id": pedido_id,
        "paciente_nombre": data.paciente_nombre,
        "telefono": data.telefono,
        "montura": data.montura,
        "tipo_lente": data.tipo_lente,
        "tratamiento": data.tratamiento,
        "total_cliente": data.total_cliente,
        "receta": data.receta.dict() if hasattr(data.receta, "dict") else data.receta,
        "monto_pagado": 0.0,
        "saldo": data.total_cliente,
        "estado": "PENDIENTE_PAGO",
        "fecha": datetime.now().isoformat(),
    }
    pedidos.append(pedido)
    
    # Registrar el estado inicial
    estados_pedido.append(
        EstadoPedido(pedido_id, "PENDIENTE_PAGO", datetime.now().isoformat())
    )
    
    return pedido

def obtener_pedido_por_id(pedido_id: int) -> Optional[dict]:
    return next((p for p in pedidos if p["id"] == pedido_id), None)
