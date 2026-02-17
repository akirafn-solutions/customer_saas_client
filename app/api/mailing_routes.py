from fastapi import APIRouter, Form, File, UploadFile, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"])

router = APIRouter()
logger = logging.getLogger("fastapi_app")

# --- Middleware de Token ---
async def verificar_token(request: Request):
    return True

# --- Função auxiliar para envio de e-mail ---
def enviar_email(nome, email, telefone, cargo, mensagem, curriculo: UploadFile = None):
    return True

@router.post("/trabalheconosco", dependencies=[Depends(verificar_token)])
@limiter.limit("5/minute")
async def enviar_email_api():

    return True
