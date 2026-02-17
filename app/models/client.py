# app/models/client.py
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    Enum, UUID, JSON, ARRAY, Text, Index, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, INET, ARRAY as PG_ARRAY, ENUM as PG_ENUM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from enum import StrEnum
from ..schemas.client import client_plan_enum_type, auth_mode_enum_type, client_status_enum_type, ClientPlanEnum, AuthModeEnum, ClientStatusEnum
Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'
    
    # Identificação
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    document = Column(String(20))
    phone = Column(String(20))
    
    # Plano e Autenticação
    plan = Column(client_plan_enum_type, default=ClientPlanEnum.FREE, nullable=False)
    auth_mode = Column(auth_mode_enum_type, default=AuthModeEnum.OPEN, nullable=False)
    status = Column(client_status_enum_type, default=ClientStatusEnum.TRIAL, nullable=False)
    #plan = Column(PG_ENUM(ClientPlanEnum, name='client_plan', values_callable=lambda obj: [e.value for e in obj]), default=ClientPlanEnum.FREE.value, nullable=False)
    #auth_mode = Column(PG_ENUM(AuthModeEnum, name='auth_mode', values_callable=lambda obj: [e.value for e in obj]), default=AuthModeEnum.OPEN.value, nullable=False)
    #status = Column(PG_ENUM(ClientStatusEnum, name='client_status', values_callable=lambda obj: [e.value for e in obj]), default=ClientStatusEnum.TRIAL.value, nullable=False)
    
    # Chaves - Google Style
    site_key = Column(String(100), unique=True, nullable=False)
    
    # Chaves - Stripe Style
    api_key = Column(String(100), unique=True)
    api_secret_hash = Column(Text)
    api_secret_salt = Column(Text)
    
    # Webhooks
    webhook_url = Column(Text)
    webhook_secret = Column(String(100))
    
    # Restrições
    allowed_origins = Column(ARRAY(String))
    allowed_ips = Column(ARRAY(INET))
    blocked_ips = Column(ARRAY(INET))
    
    # Limites
    rate_limit = Column(Integer, nullable=False, default=60)
    daily_quota = Column(Integer, nullable=False, default=1000)
    daily_used = Column(Integer, nullable=False, default=0)
    last_daily_reset = Column(DateTime, default=datetime.utcnow)
    monthly_quota = Column(Integer, nullable=False, default=30000)
    monthly_used = Column(Integer, nullable=False, default=0)
    last_monthly_reset = Column(DateTime, default=datetime.utcnow)
    
    # Configurações
    settings = Column(JSON, default={})
    #metadata = Column(JSON, default={})
    tags = Column(ARRAY(String))
    
    # Relacionamentos
    audit_logs = relationship("AuditLog", back_populates="client")
    credentials = relationship("ClientCredential", back_populates="client")
    
    # Controle
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    last_request_at = Column(DateTime)
    deleted_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_clients_api_key', api_key, unique=True, postgresql_where=(api_key != None)),
        Index('idx_clients_site_key', site_key),
        Index('idx_clients_email', email),
        Index('idx_clients_status_plan', status, plan),
    )

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    # Identificação
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"))
    request_id = Column(String(100), nullable=False)
    request_method = Column(String(10), nullable=False)
    request_path = Column(Text, nullable=False)
    request_headers = Column(JSON, nullable=False)
    request_body = Column(Text, nullable=False)
    response_status = Column(Integer, nullable=False)
    ip_address = Column(INET)
    user_agent = Column(Text)
    origin = Column(String(255))
    auth_mode = Column(auth_mode_enum_type, default=AuthModeEnum.OPEN, nullable=False)
    api_key_used = Column(String(100))
    site_key_used = Column(String(100), nullable=False)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    created_at = Column(DateTime)

    __table_args__ = (
        Index('idx_audit_logs_client_created', client_id),
        Index('idx_audit_logs_ip_created', created_at),
        Index('idx_audit_logs_requested_id', request_id),
    )

    client = relationship("Client", back_populates="audit_logs")

class ClientCredential(Base):
    __tablename__ = 'client_credentials'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"))
    api_key = Column(String(100), unique=True)
    api_secret_hash = Column(Text)
    api_secret_salt = Column(Text)
    label = Column(String(100), unique=True)
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime)
    revoked_at = Column(DateTime)

    client = relationship("Client", back_populates="credentials")
