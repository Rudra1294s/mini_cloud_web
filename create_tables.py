from database import engine, Base
import models
from sqlalchemy import text

# Ensure schema exists and create tables
with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS cloud_schema"))

Base.metadata.create_all(bind=engine)
print("✅ Schema and tables created/verified in mini_cloud_db")
