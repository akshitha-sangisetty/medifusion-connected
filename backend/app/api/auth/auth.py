"""Legacy compatibility helpers. New routes use ``api.auth.routes`` directly."""

from datetime import timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import JWT_ISSUER, SECRET_KEY
from app.api.auth.routes import ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token as _create_access_token

# Password hashing
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))

# JWT token creation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    return _create_access_token(data, expires_delta)

# JWT token verification
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], issuer=JWT_ISSUER)
        return payload
    except JWTError:
        return None
