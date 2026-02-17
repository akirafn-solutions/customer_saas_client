import logging
from fastapi import APIRouter
from slowapi import Limiter
from slowapi.util import get_remote_address
#from .endpoints import auth

# Middleware de rate limit
limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"])

router = APIRouter()
logger = logging.getLogger("fastapi_app")

# Incluir rotas de autenticação
#router.include_router(auth.router)

