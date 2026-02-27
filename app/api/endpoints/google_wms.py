from app.core.config import settings as config
from app.schemas.schemas import UploadPicturePayload, UploadPictureResponse

import requests
from firebase_admin import storage, auth
from fastapi import APIRouter, HTTPException, Depends, status, Header
import logging

router = APIRouter()
logger = logging.getLogger("fastapi_app")

async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cabeçalho de autorização inválido.",
        )
    
    id_token = authorization.split("Bearer ")[1]
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido."
        )

@router.post("/updloadpicprofile", response_model=UploadPictureResponse)
async def upload_profile_picture(
    payload: UploadPicturePayload,
    current_user = Depends(get_current_user)
):
    uid = current_user['uid']
    photo_url = str(payload.photo_url)

    try:
        # 1. Baixar a imagem
        response = requests.get(photo_url, stream=True, timeout=10)
        response.raise_for_status()

        # 2. Salvar no Storage
        bucket = storage.bucket()
        file_path = f"kidts_shop/profile_picture/{uid}.png"
        blob = bucket.blob(file_path)
        blob.upload_from_string(response.content, content_type='image/png')
        blob.make_public()

        return {
            "message": f"Foto de perfil salva com sucesso em {file_path}",
            "success": True
        }

    except requests.exceptions.RequestException as e:
        return {
            "message": f"Erro ao baixar a imagem: {str(e)}",
            "success": False
        }
    except Exception as e:
        return {
            "message": f"Erro ao salvar no Storage: {str(e)}",
            "success": False
        }