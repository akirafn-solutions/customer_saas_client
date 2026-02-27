
import logging
from app.api import auth_routes, ship_routes, product_routes, google_routes
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.middlewares.auth_middleware import SecurityMiddleware, LoggingMiddleware
from app.services.firebase_service import initialize_firebase
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# --- Configuração Inicial ---
setup_logging("fastapi_app", settings.LOG_FILE_PATH) 
logger = logging.getLogger("fastapi_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Iniciando a aplicação: {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    initialize_firebase()

    yield
    logger.info("Encerrando a aplicação.")
    print("\nRotas registradas:")
    for route in app.routes:
        print(f"{route.path} -> {route.methods}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)

# --- Middlewares ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "x-api-token"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityMiddleware)

#@app.middleware("http" )
#async def middleware_autenticacao_wrapper(request: Request, call_next):
#    return await middleware_autenticacao(request, call_next)

app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(ship_routes.router, prefix="/api/v1/shipping", tags=["Shipping Services"])
app.include_router(product_routes.router, prefix="/api/v1/products", tags=["Products Services"])
app.include_router(google_routes.router, prefix="/api/v1/google", tags=["Google Backend Services"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Bem-vindo à {settings.PROJECT_NAME}!"}

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "healthy"}

@app.get("/secure-data/")
def get_secure_data():
    return {"data": "Este ambiente é protegido por Akira FN Solutions!"}
