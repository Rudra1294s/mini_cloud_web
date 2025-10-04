import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:kali1294$@localhost:5432/mini_cloud_db"
)

# Schema name
SCHEMA_NAME = "cloud_schema"

# Engine and Session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for ORM models
metadata = MetaData(schema=SCHEMA_NAME)
Base = declarative_base(metadata=metadata)
