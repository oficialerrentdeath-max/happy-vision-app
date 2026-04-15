from typing import Optional
from dataclasses import dataclass, asdict

@dataclass
class Receta:
    od_esfera: float
    od_cilindro: float
    od_eje: int
    oi_esfera: float
    oi_cilindro: float
    oi_eje: int
    add: Optional[float] = None
    dp: float = 0
    altura: Optional[float] = None

    def dict(self):
        return asdict(self)
