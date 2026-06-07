from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_admin
from app.auth.service import AdminAuthService, AuthenticationError, InactiveAdminError
from app.models.auth import AdminUserPublic, LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    service = AdminAuthService()

    try:
        token = service.login(payload.username, payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except InactiveAdminError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return TokenResponse(access_token=token)


@router.get("/me", response_model=AdminUserPublic)
def me(current_admin: AdminUserPublic = Depends(get_current_admin)) -> AdminUserPublic:
    return current_admin
