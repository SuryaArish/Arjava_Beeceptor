import os
import requests
from fastapi import Header, HTTPException
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

COGNITO_REGION = os.getenv("AWS_REGION", "ap-south-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")

_jwks_cache: dict = {}

def _get_jwks() -> dict:
    if _jwks_cache:
        return _jwks_cache
    url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    _jwks_cache.update(resp.json())
    return _jwks_cache


async def verify_token(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    token = authorization[len("Bearer "):]
    try:
        jwks = _get_jwks()
        headers = jwt.get_unverified_header(token)
        key = next((k for k in jwks["keys"] if k["kid"] == headers["kid"]), None)
        if not key:
            raise HTTPException(status_code=401, detail="Public key not found")
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="sub not found in token")
        return user_id
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")
