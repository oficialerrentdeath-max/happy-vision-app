from dataclasses import dataclass

@dataclass
class PagoConfirmacion:
    pedido_id: int
    metodo: str
    referencia: str
    monto: float
