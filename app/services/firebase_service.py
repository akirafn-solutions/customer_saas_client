# app/services/firebase_service.py
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from app.core.config import settings

logger = logging.getLogger("fastapi_app")

def initialize_firebase():
    """
    Inicializa o Firebase Admin SDK de forma segura, se ainda não foi inicializado.
    """
    if not firebase_admin._apps:
        try:
            cred_path = settings.FIREBASE_API_SDK_PATH
            if not cred_path:
                raise ValueError("Caminho para credenciais do Firebase não definido em .env (FIREBASE_API_SDK_PATH)")
            
            cred = credentials.Certificate(cred_path)
            
            firebase_config = {
                'databaseURL': settings.FIREBASE_DATABASE_URL,
                'storageBucket': settings.FIREBASE_STORAGE_BUCKET
            }
            
            firebase_admin.initialize_app(cred, firebase_config)
            logger.info("Firebase Admin SDK inicializado com sucesso para a aplicação FastAPI.")
        except Exception as e:
            logger.critical(f"ERRO CRÍTICO: Falha ao inicializar Firebase Admin SDK na API: {e}", exc_info=True)
            # Em um cenário de produção, você pode querer que a aplicação pare se o Firebase for essencial.
            # raise RuntimeError("Não foi possível conectar ao Firebase.") from e
    else:
        logger.info("Firebase Admin SDK já estava inicializado.")

def get_db():
    """ Retorna uma instância do cliente Firestore. """
    if not firebase_admin._apps:
        initialize_firebase()
    return firestore.client()
