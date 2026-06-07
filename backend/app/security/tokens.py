from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config.settings import settings


ALGORITHM = "HS256"


class TokenError(RuntimeError):
    pass


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": subject,
        "exp": expires_at,
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise TokenError("Invalid or expired access token") from exc

    subject = payload.get("sub")
    token_type = payload.get("type")

    if not subject or token_type != "access":
        raise TokenError("Invalid access token payload")

    return str(subject)
