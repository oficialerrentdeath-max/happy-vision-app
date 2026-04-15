from typing import Optional
from dataclasses import dataclass

@dataclass
class Laboratorio:
    id: int
    nombre: str
    tipo_lente: str
    costo_base: float
    telefono: Optional[str] = None
