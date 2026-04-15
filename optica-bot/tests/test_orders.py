import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import HTTPException
from app.core.database import DB_MODE
from app.schemas.prescription import Receta
from app.schemas.order import PedidoCreate
from app.schemas.payment import PagoConfirmacion
from app.crud.patient import clientes
from app.crud.product import productos
from app.crud.order import pedidos
from app.crud.payment import pagos
from app.crud.lab_order import ordenes_lab

from app.api.v1.endpoints.orders import crear_pedido, dashboard_utilidad, obtener_trazabilidad
from app.api.v1.endpoints.payments import confirmar_pago

def test_run_smoke_tests():
    clientes.clear()
    productos.clear()
    pedidos.clear()
    pagos.clear()
    ordenes_lab.clear()

    receta = Receta(
        od_esfera=-1.0, od_cilindro=-0.5, od_eje=180,
        oi_esfera=-1.25, oi_cilindro=-0.75, oi_eje=170,
        dp=62
    )
    pedido = PedidoCreate(
        paciente_nombre="Juan",
        telefono="0999999999",
        montura="Ray-Ban",
        tipo_lente="progresivo premium",
        total_cliente=120.0,
        receta=receta,
    )
    creado = crear_pedido(pedido)
    assert len(clientes) == 1
    assert creado["id"] == 1
    assert creado["paciente_nombre"] == "Juan"

    orden = confirmar_pago(PagoConfirmacion(1, "transferencia", "ABC123", 120.0))
    assert orden["laboratorio"] == "Laboratorio Premium Vision"
    assert orden["costo"] == 42.0

    utilidad = dashboard_utilidad()
    assert utilidad["utilidad"] == 78.0
    assert utilidad["db_mode"] in {"memory", "postgresql", "sqlite-memory"}

    trazabilidad = obtener_trazabilidad(1)
    assert len(trazabilidad) == 2
    assert trazabilidad[0]["estado"] == "PENDIENTE_PAGO"
    assert trazabilidad[1]["estado"] == "ENVIADO_LABORATORIO"

    try:
        confirmar_pago(PagoConfirmacion(999, "transferencia", "X", 1.0))
        raise AssertionError("Debió lanzar HTTPException")
    except HTTPException:
        pass

if __name__ == "__main__":
    test_run_smoke_tests()
    print("Pruebas ejecutadas con éxito.")
