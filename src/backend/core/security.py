import logging
import os
from typing import Any, Dict, List

import aiohttp
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from jose.exceptions import JWTError

from app_config import config

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


class TokenValidator:
    def __init__(self):
        self.tenant_id = config.AZURE_TENANT_ID
        self.client_id = config.AZURE_CLIENT_ID
        self.jwks_uri = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
        self.issuer = f"https://sts.windows.net/{self.tenant_id}/"

    async def get_jwks(self) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.jwks_uri) as resp:
                if resp.status != 200:
                    logger.error("Failed to fetch JWKS: %s", resp.status)
                    raise HTTPException(status_code=500, detail="Unable to fetch JWKS")
                return await resp.json()

    async def validate_token(self, token: str) -> Dict[str, Any]:
        try:
            jwks = await self.get_jwks()
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            rsa_key = None
            for key in jwks["keys"]:
                if key["kid"] == kid:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"],
                    }
                    break

            if rsa_key is None:
                logger.error("No matching JWKS key found")
                raise HTTPException(status_code=401, detail="Invalid token")

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.issuer,
            )
            return payload

        except JWTError as e:
            logger.error("Token validation failed: %s", e)
            raise HTTPException(status_code=401, detail="Invalid token")


token_validator = TokenValidator()


async def get_current_user_claims(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid",
        )
    token = credentials.credentials
    return await token_validator.validate_token(token)


async def get_current_user_groups(
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> List[str]:
    groups = claims.get("groups", [])
    if not groups:
        logger.info(f"User {claims.get('oid')} has no group claims.")
    return groups
