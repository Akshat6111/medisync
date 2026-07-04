from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config.settings import settings

# Creates the connection to PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    echo=True
)

# Creates a new database session for every request
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Parent class for all database models
Base = declarative_base()


# Dependency used in FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()