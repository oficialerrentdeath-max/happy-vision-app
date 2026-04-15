from typing import Optional
from dataclasses import dataclass
from app.schemas.prescription import Receta

@dataclass
class PedidoCreate:
    paciente_nombre: str
    telefono: str
    montura: str
    tipo_lente: str
    total_cliente: float
    receta: Receta
    tratamiento: Optional[str] = None
