from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
class CatalogoRequest(BaseModel):
    """ Modelo para a requisição de geração de catálogo. """
    tipo_catalogo: str = Field(
        default="N",
        description="Tipo de catálogo a ser gerado (J, Y, ou N para normal).",
        max_length=1
    )

class PDFRequest(BaseModel):
    id: str
    request_date: datetime
    status: str
    filename: str
    requester_uid: str
    requester_name: str
    download_url: str = None
    progress: int = 0

# Base models
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    slug: str

class UploadPicturePayload(BaseModel):
    photo_url: str
    
    @field_validator('photo_url')
    def validate_url(cls, v):
        if not v.startswith('http' ):
            raise ValueError('URL deve começar com http ou https' )
        return v

class UploadPictureResponse(BaseModel):
    message: str
    success: bool

class CategoryResponse(CategoryBase):
    id: int
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductImageResponse(BaseModel):
    id: int
    image_url: str
    alt_text: Optional[str] = None
    order_index: int
    is_primary: bool
    
    class Config:
        from_attributes = True

class ProductVideoResponse(BaseModel):
    id: int
    youtube_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    is_featured: bool = False
    slug: str
    sku: Optional[str] = None
    product_code: str

class ProductResponse(ProductBase):
    id: int
    is_active: bool
    category_id: Optional[int] = None
    category: Optional[CategoryResponse] = None
    images: List[ProductImageResponse] = []
    videos: List[ProductVideoResponse] = []
    product_code: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class FeaturedProductResponse(BaseModel):
    id: int
    name: str
    price: str
    image: str | None = None
    category: str | None = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ContactFormCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: EmailStr
    cpf_cnpj: Optional[str] = None
    request_type: Optional[str] = None
    relationship_type: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None

class ContactFormResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    email: str
    cpf_cnpj: Optional[str] = None
    request_type: Optional[str] = None
    relationship_type: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class MainPageContentResponse(BaseModel):
    id: int
    content_type: str
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    order_index: int
    is_active: bool
    
    class Config:
        from_attributes = True

class PaginatedProductsResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: Optional[int] = None
    pages: Optional[int] = None

class TrabalheConoscoRequest(BaseModel):
    nome: str
    email: str
    telefone: str
    cargo: str
    mensagem: str
    curriculo_nome: Optional[str] = None
    curriculo_base64: Optional[str] = None
