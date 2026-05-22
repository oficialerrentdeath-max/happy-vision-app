import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def enviar_factura_correo(destinatario, cliente_nombre, ruta_xml, ruta_pdf):
    """
    Envía la factura (XML y RIDE en PDF) por correo electrónico.
    """
    remitente = "tu_correo@gmail.com"
    password = "tu_password_app"
    
    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario
    msg['Subject'] = "Happy Vision - Factura Electrónica"
    
    cuerpo = f"""
    Estimado(a) {cliente_nombre},
    
    Adjunto encontrará su factura electrónica en formato XML y PDF (RIDE).
    Gracias por preferir Happy Vision.
    
    Atentamente,
    El equipo de Happy Vision
    """
    msg.attach(MIMEText(cuerpo, 'plain'))
    
    # Adjuntar XML
    try:
        with open(ruta_xml, "rb") as f:
            adjunto_xml = MIMEApplication(f.read(), _subtype="xml")
            adjunto_xml.add_header('Content-Disposition', 'attachment', filename="factura.xml")
            msg.attach(adjunto_xml)
    except Exception as e:
        print(f"Error adjuntando XML: {e}")
        
    # Adjuntar PDF
    try:
        with open(ruta_pdf, "rb") as f:
            adjunto_pdf = MIMEApplication(f.read(), _subtype="pdf")
            adjunto_pdf.add_header('Content-Disposition', 'attachment', filename="factura.pdf")
            msg.attach(adjunto_pdf)
    except Exception as e:
        print(f"Error adjuntando PDF: {e}")
        
    # Enviar correo (Se asume servidor Gmail para el ejemplo)
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        # server.login(remitente, password) # Descomentar y configurar con credenciales reales
        # server.send_message(msg)
        server.quit()
        return True, "Correo enviado simulado (falta configuración de credenciales)."
    except Exception as e:
        return False, str(e)
