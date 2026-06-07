from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.service import AdminAuthService, AuthenticationError, InactiveAdminError
from app.models.auth import AdminUserPublic
from app.security.tokens import TokenError, decode_access_token


bearer_scheme = HTTPBearer()


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> AdminUserPublic:
    try:
        admin_id = int(decode_access_token(credentials.credentials))
        return AdminAuthService().get_admin_by_id(admin_id)
    except (TokenError, ValueError, AuthenticationError, InactiveAdminError) as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
