from typing import Optional
from dataclasses import dataclass

@dataclass
class Producto:
    id: int
    montura: str
    tipo_lente: str
    tratamiento: Optional[str]
    precio: float
