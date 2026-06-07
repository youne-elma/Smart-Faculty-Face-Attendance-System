from app.auth.admin_repository import AdminRepository
from app.models.auth import AdminUserPublic
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token


class AuthenticationError(RuntimeError):
    pass


class InactiveAdminError(RuntimeError):
    pass


class AdminAuthService:
    def __init__(self, repository: AdminRepository | None = None) -> None:
        self.repository = repository or AdminRepository()

    def create_admin(self, username: str, password: str) -> AdminUserPublic:
        admin = self.repository.create_or_update(username, hash_password(password))
        return self._to_public_admin(admin)

    def login(self, username: str, password: str) -> str:
        admin = self.repository.get_by_username(username)

        if admin is None or not verify_password(password, admin["password_hash"]):
            raise AuthenticationError("Invalid username or password")

        if not bool(admin["is_active"]):
            raise InactiveAdminError("Admin user is inactive")

        return create_access_token(str(admin["id"]))

    def get_admin_by_id(self, admin_id: int) -> AdminUserPublic:
        admin = self.repository.get_by_id(admin_id)

        if admin is None:
            raise AuthenticationError("Admin user not found")

        if not bool(admin["is_active"]):
            raise InactiveAdminError("Admin user is inactive")

        return self._to_public_admin(admin)

    def _to_public_admin(self, admin) -> AdminUserPublic:
        return AdminUserPublic(
            id=int(admin["id"]),
            username=str(admin["username"]),
            is_active=bool(admin["is_active"]),
        )
