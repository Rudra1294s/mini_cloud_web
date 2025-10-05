import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL connection (Render DB credentials)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rudrav_cloud:M1pqzgpKCJ7es0eOHwU8fK9zdHxEOHyv@dpg-d3h1rr0gjchc73a50uig-a:5432/mini_cloud_db"
)

# Optional: Schema name (Render DB me default public schema hi chalega, ya agar chahiye to cloud_schema)
SCHEMA_NAME = os.getenv("SCHEMA_NAME", "cloud_schema")

# Engine and Session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for ORM models
metadata = MetaData(schema=SCHEMA_NAME)
Base = declarative_base(metadata=metadata)
