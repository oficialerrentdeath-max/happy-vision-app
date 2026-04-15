# tests/test_full_cycle.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.schemas.prescription import Receta
from app.schemas.order import PedidoCreate
from app.schemas.payment import PagoConfirmacion
from app.api.v1.endpoints.orders import crear_pedido_endpoint
from app.api.v1.endpoints.payments import confirmar_pago
from app.crud.order import pedidos, estados_pedido
from app.crud.lab_order import ordenes_lab
from app.crud.payment import pagos

def test_abono_logic_50_percent():
    # Limpiar datos
    pedidos.clear()
    estados_pedido.clear()
    ordenes_lab.clear()
    pagos.clear()

    # 1. Crear pedido de $120
    receta = Receta(od_esfera=-1.0, od_cilindro=0, od_eje=0, oi_esfera=-1.0, oi_cilindro=0, oi_eje=0, dp=60)
    pedido_in = PedidoCreate(
        paciente_nombre="Test Abono",
        telefono="123456",
        montura="Test",
        tipo_lente="Monofocal",
        total_cliente=120.0,
        receta=receta
    )
    pedido = crear_pedido_endpoint(pedido_in)
    pedido_id = pedido["id"]

    # 2. Primer abono de $30 (25% - No debe disparar lab)
    res1 = confirmar_pago(PagoConfirmacion(pedido_id, "transf", "ref1", 30.0))
    assert res1["pedido_estado"] == "ABONADO"
    assert res1["saldo_restante"] == 90.0
    assert res1["orden_laboratorio"] is None
    assert len(ordenes_lab) == 0

    # 3. Segundo abono de $40 (Total $70 > 50% - Debe disparar lab)
    res2 = confirmar_pago(PagoConfirmacion(pedido_id, "transf", "ref2", 40.0))
    assert res2["pedido_estado"] == "ABONADO"
    assert res2["saldo_restante"] == 50.0
    assert res2["orden_laboratorio"] is not None
    assert res2["orden_laboratorio"]["laboratorio"] == "Laboratorio Local CR39"
    assert len(ordenes_lab) == 1

    # 4. Pago final de $50 (Total $120 - Debe ser PAGADO y no duplicar lab)
    res3 = confirmar_pago(PagoConfirmacion(pedido_id, "transf", "ref3", 50.0))
    assert res3["pedido_estado"] == "PAGADO"
    assert res3["saldo_restante"] == 0.0
    assert res3["orden_laboratorio"] is None # No se crea otra
    assert len(ordenes_lab) == 1

    print("SUCCESS: Prueba de ciclo completo de abonos (50%) exitosa.")

if __name__ == "__main__":
    test_abono_logic_50_percent()
