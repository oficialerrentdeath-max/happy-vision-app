"""
utils/__init__.py — Punto de entrada del paquete utils

Re-exporta todas las funciones públicas para que los imports existentes
en vistas/ y app.py sigan funcionando sin ningún cambio:

    from utils import guardar_datos, wa_link, generar_pdf_historia ...
"""

# Datos de prueba
from utils.datos import generate_sample_data

# Persistencia (guardar CSV + SQLite)
from utils.persistencia import guardar_datos

# WhatsApp
from utils.whatsapp import (
    wa_link,
    generar_msg_factura,
    generar_msg_hc,
    generar_msg_indicaciones,
)

# PDF
from utils.pdf import (
    _s,
    generar_pdf_historia,
)

__all__ = [
    "generate_sample_data",
    "guardar_datos",
    "wa_link",
    "generar_msg_factura",
    "generar_msg_hc",
    "generar_msg_indicaciones",
    "_s",
    "generar_pdf_historia",
]
