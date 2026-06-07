import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth.service import AdminAuthService
from app.config.settings import settings
from app.database.service import DatabaseService


def main() -> None:
    DatabaseService().initialize()
    admin = AdminAuthService().create_admin(
        username=settings.admin_username,
        password=settings.admin_password,
    )
    print(f"Admin user ready: {admin.username} (id={admin.id})")


if __name__ == "__main__":
    main()
