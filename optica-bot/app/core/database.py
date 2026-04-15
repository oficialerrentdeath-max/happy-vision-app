# app/core/database.py
try:
    from sqlalchemy import create_engine # type: ignore
    from sqlalchemy.orm import declarative_base, sessionmaker # type: ignore
    SQLALCHEMY_AVAILABLE = True
except ModuleNotFoundError:
    SQLALCHEMY_AVAILABLE = False

    def create_engine(*args, **kwargs):
        return None

    def sessionmaker(*args, **kwargs):
        return None

    def declarative_base():
        class DummyBase:
            class metadata:
                @staticmethod
                def create_all(bind=None):
                    return None
        return DummyBase

Base = declarative_base()
engine = None
SessionLocal = None
DB_MODE = "memory"

if SQLALCHEMY_AVAILABLE:
    try:
        DATABASE_URL = "postgresql://usuario:password@localhost/happy_vision"
        engine = create_engine(DATABASE_URL)
        _ = engine.dialect
        DB_MODE = "postgresql"
    except Exception:
        engine = create_engine("sqlite:///:memory:")
        DB_MODE = "sqlite-memory"

    if engine:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
