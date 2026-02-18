"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Build engine kwargs based on database type
_engine_kwargs = {
    "echo": settings.log_level == "DEBUG",
}

if settings.database_type == "sqlite":
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL / MySQL: enable connection health checks
    _engine_kwargs["pool_pre_ping"] = True

# Create database engine
DATABASE_URL = settings.effective_database_url
engine = create_engine(DATABASE_URL, **_engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session.

    Usage in FastAPI endpoints:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
