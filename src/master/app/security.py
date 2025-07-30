
import os
from fastapi import HTTPException, Security
from starlette.status import HTTP_403_FORBIDDEN
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME: str = "X-API-Key"
API_KEY: str = os.environ["MASTER_API_KEY"]

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header_value: str = Security(api_key_header)):
    if api_key_header_value == API_KEY:
        return api_key_header_value
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key",
        )
