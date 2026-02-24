import hashlib
import hmac
import json
import redis.asyncio as redis
import uuid
from app.api.utils.auth_client import find_by_site_key
from app.core.config import settings as config
from app.core.logging_config import setup_logging
from app.database.database import get_async_session, SessionLocal
from app.models.client import Client, AuditLog
from app.schemas.client import AuthModeEnum
from datetime import datetime, timezone
from fastapi import Request, HTTPException, Request, Depends
from fastapi.security import HTTPBearer
from jose import jwt
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

logger = setup_logging("fastapi_app", config.LOG_FILE_PATH) 

NONCE_CACHE = {}

async def bloquear_sql_injection(request: Request, call_next):

    corpo = await request.body()
    conteudo = corpo.decode(errors="ignore").lower()
    if any(palavra in conteudo for palavra in ["drop table", "insert into", "delete from", "<script>"]):
        return JSONResponse(status_code=400, content={"erro": "Conteúdo potencialmente malicioso detectado."})
    
    if request.method == "POST":
        body = await request.form()
        for key, value in body.items():
            if isinstance(value, str):
                if len(value) > 5000:
                    return JSONResponse(status_code=400, content={"erro": f"Campo {key} muito longo."})
    return await call_next(request)

security = HTTPBearer()

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis = None
        self.blocked_ips = set()
        
    async def dispatch(self, request: Request, call_next):
        try:
            if request.method == "OPTIONS":
                return await call_next(request)

            client_ip = request.client.host
            if await self.is_ip_blocked(client_ip):
                raise HTTPException(
                    status_code=403,
                    detail="IP bloqueado por atividade suspeita"
                )
            
            site_key = request.headers.get("X-Site-Key")
            if not site_key:
                raise HTTPException(
                    status_code=401,
                    detail="Site Key é obrigatória"
                )
            
            async with SessionLocal() as db_session:
                client = await find_by_site_key(site_key, db_session)
                if not client:
                    raise HTTPException(
                        status_code=403,
                        detail="Site Key inválida"
                    )
            
                if client.auth_mode == AuthModeEnum.OPEN:
                    await self.validate_google_auth(request, client)
                else:
                    await self.validate_enterprise_auth(request, client)
                
                await self.check_rate_limit(client)
                
                await self.check_quota(client)
                
                # ADICIONA CLIENTE NO REQUEST
                request.state.client = client
                
                await self.audit_log(request, client, db_session)
            
            response = await call_next(request)
            
            # HEADERS DE SEGURANÇA
            response.headers["X-App-ID"] = str(config.API_APP_ID)
            response.headers["X-API-Version"] = config.API_VERSION
            response.headers["X-RateLimit-Limit"] = str(client.rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(
                await self.get_remaining_quota(client)
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno: {str(e)}"
            )
    
    async def validate_google_auth(self, request: Request, client: Client):
        origin = request.headers.get("origin")
        if client.allowed_origins and origin not in client.allowed_origins:
            raise HTTPException(
                status_code=403,
                detail=f"Invalid Req"
            )
        
        timestamp = int(request.headers.get("X-Timestamp"))
        if timestamp:
            now = datetime.now(timezone.utc).timestamp()
            if abs(now - int(timestamp)) > 300:  # 5 minutos
                raise HTTPException(
                    status_code=403,
                    detail="Request expirado"
                )
        else:
            raise HTTPException(
                status_code=403,
                detail=f"Invalid Header"
            )
    
    async def validate_enterprise_auth(self, request: Request, client: Client):
        # 1. Valida API Key
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != client.api_key:
            raise HTTPException(
                status_code=401,
                detail="API Key inválida"
            )
        
        # 2. Valida HMAC Signature
        signature = request.headers.get("X-Signature")
        timestamp = request.headers.get("X-Timestamp")
        
        if not signature or not timestamp:
            raise HTTPException(
                status_code=401,
                detail="Assinatura HMAC obrigatória"
            )
        
        # 3. Anti-replay attack
        now = int(datetime.now(timezone.utc).timestamp())
        if abs(now - int(timestamp)) > config.HMAC_EXPIRY_SECONDS:
            raise HTTPException(
                status_code=403,
                detail="Request expirado ou replay attack detectado"
            )
        
        # 4. Pega body
        body = await request.body()
        payload = body.decode() if body else "{}"
        
        # 5. Verifica HMAC
        message = f"{timestamp}:{payload}"
        expected_signature = hmac.new(
            client.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_signature, signature):
            raise HTTPException(
                status_code=403,
                detail="Assinatura HMAC inválida"
            )
        
        # 6. Valida JWT token (se enviado)
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.replace("Bearer ", "")
            try:
                payload = jwt.decode(
                    token,
                    config.JWT_SECRET_KEY,
                    algorithms=[config.JWT_ALGORITHM]
                )
                request.state.user = payload
            except:
                raise HTTPException(
                    status_code=401,
                    detail="Token JWT inválido"
                )
    
    async def check_rate_limit(self, client: Client):
        if not self.redis:
            self.redis = await redis.from_url(config.REDIS_URL)
        
        key = f"ratelimit:{client.id}:{datetime.now(timezone.utc).timestamp()}"
        current = await self.redis.incr(key)
        
        if current == 1:
            await self.redis.expire(key, 60)
        
        if current > client.rate_limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit excedido",
                    "limit": client.rate_limit,
                    "current": current,
                    "reset_in": 60
                }
            )
    
    async def check_quota(self, client: Client):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"quota:{client.id}:{today}"
        
        if not self.redis:
            self.redis = await redis.from_url(config.REDIS_URL)
        
        current = await self.redis.get(key) or 0
        current = int(current)
        
        if current >= client.daily_quota:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Quota diária excedida",
                    "limit": client.daily_quota,
                    "reset": "amanhã",
                    "upgrade": "https://akirafn.com.br/contact"
                }
            )
        
        await self.redis.incr(key)
        await self.redis.expire(key, 86400)
    
    async def get_remaining_quota(self, client: dict) -> int:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"quota:{client.id}:{today}"
        
        current = await self.redis.get(key) or 0
        quota = client.daily_quota
        
        return max(0, quota - int(current))
    
    async def is_ip_blocked(self, ip: str) -> bool:
        return await self.redis.sismember("blocked_ips", ip)
    
    async def audit_log(self, request: Request, client: Client, db_session: AsyncSession = Depends(get_async_session)):
        headers_dict = dict(request.headers)
        headers_dict.pop("authorization", None)
        headers_dict.pop("cookie", None)

        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8") if body_bytes else None

        log_entry = {
            "created_at": datetime.now(),
            "client_id": client.id,
            "site_key_used": client.site_key,
            "request_headers": headers_dict,
            "request_body": body_str,
            "ip_address": request.client.host,
            "request_method": request.method,
            "request_path": request.url.path,
            "user_agent": request.headers.get("user-agent"),
            "origin": request.headers.get("origin"),
            "success": True,
            "auth_mode": client.auth_mode.value
        }
        
        if self.redis:
            redis_payload = json.dumps(log_entry, default=str)
            key = f"audit:{client.id}"
            await self.redis.lpush(key, redis_payload)
            await self.redis.ltrim(key, 0, 999)
        
        stmt = insert(AuditLog).values(**log_entry)
        await db_session.execute(stmt)
        await db_session.commit()
    
    async def is_ip_blocked(self, ip: str) -> bool:
        if not self.redis:
            self.redis = await redis.from_url(config.REDIS_URL)
        
        return await self.redis.sismember("blocked_ips", ip)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now(timezone.utc)
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        process_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time, 2))
        if process_time > 1000:
            print(f"⚠️ Request lento: {request.url.path} - {process_time}ms")
        
        return response