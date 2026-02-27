from app.api.endpoints import google_wms
from fastapi import APIRouter
import logging

router = APIRouter()
logger = logging.getLogger("fastapi_app")

router.include_router(google_wms.router)