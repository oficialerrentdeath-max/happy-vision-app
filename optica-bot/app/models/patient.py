from typing import Optional
from dataclasses import dataclass

@dataclass
class Cliente:
    id: int
    nombre: str
    telefono: str
    correo: Optional[str] = None
    direccion: Optional[str] = None
