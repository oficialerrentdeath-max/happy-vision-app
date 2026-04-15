# app/bots/responses.py

BIENVENIDA = """¡Hola! Bienvenido a Happy Vision 👓.
Soy tu asistente virtual. ¿Cómo te llamas para empezar con tu pedido?"""

PEDIR_MONTURA = """Mucho gusto, {nombre}. ¿Qué montura te gustaría comprar hoy? (Ej: Ray-Ban, Oakley, o una montura propia)"""

PEDIR_LENTE = """¡Excelente elección! Ahora, ¿qué tipo de lente necesitas?
1. Monofocal básico
2. Progresivo Premium
3. Alto índice (1.67)"""

PEDIR_RECETA = """Necesito los datos de tu receta. Por favor, indícalos así: 
OD: Esf -1.00 Cil -0.50 Eje 180
OI: Esf -1.25 Cil -0.75 Eje 170
DP: 62"""

RESUMEN_PEDIDO = """Aquí tienes el resumen de tu pedido:
- Paciente: {nombre}
- Montura: {montura}
- Lente: {lente}
- Total a pagar: ${total}

¿Está todo correcto? Responde 'SÍ' para proceder al pago."""

INSTRUCCIONES_PAGO = """Perfecto. Por favor realiza la transferencia a la cuenta:
BCP: 191-XXXXXXXX-0-XX
Monto: ${total}

Envía el número de operación cuando hayas terminado."""

GRACIAS_PAGO = """¡Gracias! Hemos recibido tu pago total. Tu pedido ya está en manos del laboratorio. 🚀"""

CONFIRMACION_ABONO = """¡Abono recibido correctamente! ✅
- Monto abonado: ${monto}
- Saldo restante: ${saldo}

{mensaje_adicional}"""
