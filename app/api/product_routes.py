from app.api.utils.api_caller import api_request
from app.core.config import settings as config
from app.schemas.schemas import PaginatedProductsResponse, ProductResponse, CategoryResponse, ContactFormCreate, ContactFormResponse, MainPageContentResponse, FeaturedProductResponse
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

router = APIRouter()
logger = logging.getLogger("fastapi_app")

BACKEND_URL = config.API_WMS_URL
ENDPOINT_WMS_FEAT_PROD = config.ENDPOINT_WMS_FEAT_PROD
ENDPOINT_WMS_PROD_LIST = config.ENDPOINT_WMS_PROD_LIST

# Incluir rotas de produtos
#router.include_router(products_wms.router)

def validate_search_query(q: Optional[str] = Query(None, min_length=2, max_lenght=100)) -> Optional[str]:
    if any(c in q for c in ['(', ')', '=', ';', '&', '|', '"', "'"]):
        raise HTTPException(status_code=400, detail="Invalid search query")
    return q

def formatar_preco(valor) -> str:
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# dependencies.py
from fastapi import Request, HTTPException

def get_app_id_from_request(request: Request) -> int:
    client = getattr(request.state, "client", None)

    if not client:
        raise HTTPException(
            status_code=401,
            detail="Cliente não autenticado"
        )

    app_id = getattr(client, "app_id", None)  # ajuste para o campo correto do seu model Client

    if not app_id:
        raise HTTPException(
            status_code=403,
            detail="app_id não encontrado para este cliente"
        )

    return app_id

# Products endpoints
@router.get("")
async def list_products(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    app_id: Optional[int] = 0
):
    client = getattr(request.state, "client", None)
    if not client:
        raise HTTPException(status_code=401, detail="Cliente não autenticado")
    
    #app_id = getattr(client, "app_id", None)
    app_id = str(config.API_APP_ID)

    if not app_id:
        raise HTTPException(status_code=403, detail="app_id não encontrado para este cliente")

    params = {
        "page": page,
        "per_page": per_page,
        "app_id": app_id,
    }
    if search:     params["search"]    = search
    if category:   params["category"]  = category
    if sort:       params["sort"]      = sort
    if price_min is not None: params["price_min"] = price_min
    if price_max is not None: params["price_max"] = price_max

    return await api_request(endpoint=ENDPOINT_WMS_PROD_LIST,method="GET",params=params)

@router.get("/featured", response_model=List[FeaturedProductResponse])
async def list_featured_products():
    limit: int = 6
    response = await api_request(endpoint=ENDPOINT_WMS_FEAT_PROD,method="GET",params={"limit": limit})
    products = response

    return [
        {
            "id":       p.get("id_produto"),
            "name":     p.get("nome_comercial"),
            "price":    formatar_preco(p.get("preco_venda")),
            "image":    p.get("imagem_principal"),
            "category": p.get("categoria_nome"),
            "is_active": p.get("ativo"),
            "created_at": p.get("data_criacao")
        }
        for p in products
    ]

@router.get("/search")
async def search_products_endpoint():
    return True

@router.get("/{product_id}")
async def get_product():
    return True

@router.get("/categories")
async def list_categories():
    return True

@router.get("/categories/{category_id}/products")
async def list_products_by_category():
    return True

@router.post("/contact")
async def submit_contact_form():
    return True

@router.get("/main-page/content")
async def get_main_page_content_endpoint():
    return True

@router.get("/app/{path:path}")
async def serve_frontend(path: str):
    return True