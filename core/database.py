from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings
from sqlalchemy.pool import NullPool

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables that don't exist yet."""
    from models import activity_log, collection, customer, customer_address, customer_contact, customer_import_row, customer_loan, user, va_data, va_request, customer_archive, field_setting, field_category  # noqa
    Base.metadata.create_all(engine, checkfirst=True)
