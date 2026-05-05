"""
utils/__init__.py — Punto de entrada del paquete utils
"""

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
    generar_pdf_ticket,
)

__all__ = [
    "wa_link",
    "generar_msg_factura",
    "generar_msg_hc",
    "generar_msg_indicaciones",
    "_s",
    "generar_pdf_historia",
    "generar_pdf_ticket",
]
