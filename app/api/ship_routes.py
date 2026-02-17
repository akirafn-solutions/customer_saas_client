import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import APIRouter

#from .endpoints import ship_calc_list

# Middleware de rate limit
limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"])

router = APIRouter()
logger = logging.getLogger("fastapi_app")

#router.include_router(ship_calc_list.router)