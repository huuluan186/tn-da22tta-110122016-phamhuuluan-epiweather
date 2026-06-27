"""
Fixtures dùng chung cho toàn bộ test suite.

Chiến lược DB:
- Dùng SQLite in-memory để test — nhanh, không cần PostgreSQL chạy.
- Override FastAPI dependency get_db() để inject session SQLite thay vì Postgres.
- Mỗi test function nhận db_session mới (rollback sau test → không có side effect).

Chiến lược App:
- TestClient wrap app object trực tiếp — không cần server thật.
- Lifespan (load models) chạy 1 lần khi client khởi động.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
import app.db.base  # noqa: F401 — register all ORM models
from app.db.session import get_db
from app.main import app

# SQLite in-memory — mỗi lần test suite chạy tạo schema mới
SQLITE_URL = "sqlite://"

_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def create_test_schema():
    """Tạo tất cả bảng trong SQLite in-memory một lần cho cả session."""
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def db_session():
    """SQLAlchemy session với rollback sau mỗi test — không để lại data."""
    connection = _engine.connect()
    transaction = connection.begin()
    session = _TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient với get_db() override dùng SQLite session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def client_with_real_db():
    """TestClient dùng DB thật (PostgreSQL) — chỉ dùng cho integration tests.
    Cần PostgreSQL đang chạy và có data seed.
    """
    with TestClient(app) as c:
        yield c
