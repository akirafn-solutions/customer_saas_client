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

# Products endpoints
@router.get("/")
async def list_products():
    return True

@router.get("/featured", response_model=List[FeaturedProductResponse])
async def list_featured_products():
    products = [
    {
        "name": "Kit Presente Premium",
        "price": "R$ 299,90",
        "image": ["https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=800&auto=format&fit=crop","https://images.unsplash.com/photo-1511381939415-e44015466834?w=800&auto=format&fit=crop"],
        "category": "Presentes"
    },
    {
        "name": "Chocolate Belga Artesanal",
        "price": "R$ 89,90",
        "image": "https://images.unsplash.com/photo-1511381939415-e44015466834?w=800&auto=format&fit=crop",
        "category": "Doces"
    },
    {
        "name": "Fones de Ouvido Premium",
        "price": "R$ 1.299,90",
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop",
        "category": "Eletrônicos"
    },
    {
        "name": "Whisky Escocês 12 Anos",
        "price": "R$ 449,90",
        "image": "https://images.unsplash.com/photo-1527281400683-1aae777175f8?w=800&auto=format&fit=crop",
        "category": "Bebidas"
    },
    {
        "name": "Caixa de Bombons Importados",
        "price": "R$ 159,90",
        "image": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=800&auto=format&fit=crop",
        "category": "Doces"
    },
    {
        "name": "Smartwatch Ultra",
        "price": "R$ 2.499,90",
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&auto=format&fit=crop",
        "category": "Eletrônicos"
    },
    {
        "name": "Vinho Tinto Reserva",
        "price": "R$ 349,90",
        "image": "https://images.unsplash.com/photo-1547595628-c61a29f496f0?w=800&auto=format&fit=crop",
        "category": "Bebidas"
    },
    {
        "name": "Kit Presente Especial",
        "price": "R$ 499,90",
        "image": "https://images.unsplash.com/photo-1513885535751-8b9238bd345a?w=800&auto=format&fit=crop",
        "category": "Presentes"
    }
    ]
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