from typing import Optional
from dataclasses import dataclass

@dataclass
class EstadoPedido:
    pedido_id: int
    estado: str
    fecha: str
    observacion: Optional[str] = None
