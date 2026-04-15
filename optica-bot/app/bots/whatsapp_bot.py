# app/bots/whatsapp_bot.py
from app.core.config import APIRouter
from app.core.config import APIRouter, BaseModel
from app.bots.conversation_flow import manager

router = APIRouter()

class WhatsAppMessage(BaseModel):
    From: str
    Body: str

@router.post("/whatsapp/webhook")
async def whatsapp_webhook(data: WhatsAppMessage):
    """
    Endpoint que recibe los mensajes de WhatsApp (simulado).
    Identifica al usuario por su número y procesa la respuesta.
    """
    phone = data.From
    message = data.Body
    
    response_text = manager.process_message(phone, message)
    
    # En un escenario real, aquí llamaríamos a la API de WhatsApp para ENVIAR el mensaje
    return {
        "to": phone,
        "message": response_text
    }
