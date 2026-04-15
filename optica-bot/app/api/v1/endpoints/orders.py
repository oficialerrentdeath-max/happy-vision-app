from datetime import datetime
from dataclasses import asdict
from app.core.config import APIRouter
from app.schemas.order import PedidoCreate
from app.models.patient import Cliente
from app.models.order import EstadoPedido
from app.crud.patient import clientes
from app.crud.order import pedidos, estados_pedido
from app.crud.lab_order import ordenes_lab

from app.services.order_service import crear_nuevo_pedido

router = APIRouter()

@router.post("/pedido")
def crear_pedido_endpoint(data: PedidoCreate):
    return crear_nuevo_pedido(data)

@router.get("/dashboard/utilidad")
def dashboard_utilidad():
    from app.core.database import DB_MODE
    ingresos = sum(p["total_cliente"] for p in pedidos if p["estado"] == "PAGADO")
    costos = sum(o["costo"] for o in ordenes_lab)
    return {
        "ingresos": ingresos,
        "costos_laboratorio": costos,
        "utilidad": ingresos - costos,
        "db_mode": DB_MODE,
    }

@router.get("/trazabilidad")
def obtener_trazabilidad(pedido_id: int):
    return [asdict(e) for e in estados_pedido if e.pedido_id == pedido_id]
