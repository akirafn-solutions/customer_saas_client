# app/schemas/client.py
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
#from enum import StrEnum
import enum

class ClientPlanEnum(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    HYBRID = "hybrid"

class AuthModeEnum(str, enum.Enum):
    OPEN = "open"
    STRIPE = "stripe"

class ClientStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELED = "canceled"

client_status_enum_type = PG_ENUM(
    ClientStatusEnum, 
    name='client_status', 
    create_type=False,
    values_callable=lambda x: [item.value for item in x]
)

client_plan_enum_type = PG_ENUM(
    ClientPlanEnum, 
    name='client_plan', 
    create_type=False,
    values_callable=lambda x: [item.value for item in x]
)

auth_mode_enum_type = PG_ENUM(
    AuthModeEnum, 
    name='auth_mode', 
    create_type=False,
    values_callable=lambda x: [item.value for item in x]
)

# ===== SCHEMAS DE CRIAÇÃO =====
class ClientCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    document: Optional[str] = Field(None, pattern=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$')
    phone: Optional[str] = None
    # Use Field para definir o valor padrão
    plan: ClientPlanEnum = Field(default=ClientPlanEnum.FREE) 
    auth_mode: AuthModeEnum = Field(default=AuthModeEnum.OPEN)
    allowed_origins: List[str] = Field(default_factory=list) # Melhor prática para tipos mutáveis
    webhook_url: Optional[str] = None

    @validator('webhook_url')
    def validate_webhook(cls, v):
        if v and not v.startswith(('http://', 'https://' )):
            raise ValueError('URL deve começar com http:// ou https://' )
        return v

class ClientResponse(BaseModel):
    id: UUID
    client_id: str
    name: str
    email: str
    plan: ClientPlanEnum
    auth_mode: AuthModeEnum
    status: ClientStatusEnum
    site_key: str
    api_key: Optional[str]
    webhook_url: Optional[str]
    webhook_secret: Optional[str]
    allowed_origins: List[str]
    rate_limit: int
    daily_quota: int
    daily_used: int
    monthly_quota: int
    monthly_used: int
    settings: Dict[str, Any]
    created_at: datetime
    last_request_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ===== SCHEMAS DE AUTENTICAÇÃO =====
class ClientAuth(BaseModel):
    site_key: str
    api_key: Optional[str] = None
    signature: Optional[str] = None
    timestamp: Optional[int] = None

class ClientQuota(BaseModel):
    client_id: UUID
    daily_limit: int
    daily_remaining: int
    monthly_limit: int
    monthly_remaining: int
    rate_limit: int
    rate_remaining: int

# ===== SCHEMAS DE CRIAÇÃO DE CREDENCIAIS =====
class CredentialCreate(BaseModel):
    label: str
    expires_in_days: Optional[int] = 365

class CredentialResponse(BaseModel):
    id: UUID
    api_key: str
    api_secret: str  # SÓ APARECE UMA VEZ!
    label: str
    expires_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True