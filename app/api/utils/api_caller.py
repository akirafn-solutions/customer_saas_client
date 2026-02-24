import httpx
import hmac
import hashlib
import random
import string
from datetime import datetime, timezone
from app.core.config import settings

BACKEND_URL=settings.API_WMS_URL

def generate_alleatory_string():
    base36=string.digits + string.ascii_lowercase[:26]
    response = ''.join(random.choices(base36,k=13))
    return response

def generate_hmac_sha256(secret_key, message):
    key_bytes = bytes(secret_key, 'utf-8')
    msg_bytes = bytes(message, 'utf-8')
    hash_obj = hmac.new(key_bytes, msg_bytes, hashlib.sha256)
    return hash_obj.hexdigest()

async def api_request(
    endpoint: str,
    method: str = "GET",
    params: dict = None,
    body: dict = None,
    extra_headers: dict = None
):
    appId = str(settings.API_APP_ID)
    appKey = str(settings.API_APP_KEY)
    appSecret = str(settings.API_APP_SECRET)
    string1 = generate_alleatory_string()

    string2 = generate_alleatory_string()
    nonce = str(string1 + string2)
    timestamp = str(int(datetime.now(timezone.utc).timestamp()))

    payload = body.decode('utf-8') if body else {}
    message = f"{appId}{timestamp}{nonce}{payload}"

    signature = generate_hmac_sha256(appSecret, message)

    base_headers = {
        "Authorization": f"Bearer {appSecret}",
        'Content-Type': 'application/json',
        'X-App-ID': f"{appId}",
        'X-App-KEY': f"{appKey}",
        'X-Timestamp': f"{timestamp}",
        'X-Nonce': f"{nonce}",
        'X-Signature': f"{signature}",
        **(extra_headers or {})
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=method,
                url=f"{BACKEND_URL}{endpoint}",
                params=params,
                json=payload,
                headers=base_headers
            )

            print("STATUS:", response.status_code)
            print("BODY:", response.text)  # <- vai mostrar o erro real da API
            
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            print("CONEXÃO FALHOU:", e)
            raise
        except httpx.TimeoutException as e:
            print("TIMEOUT:", e)
            raise