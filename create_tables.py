# create_tables.py
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from models import Base  # ensure models.py same folder me ho aur Base defined ho

USERNAME = "postgres"
PASSWORD = "kali1294$"    # tumne abhi set kiya hua password
DB_NAME = "mini_cloud_db" # agar DB name alag hai to yahan change kar dena
HOST = "localhost"
PORT = "5432"

DATABASE_URL = f"postgresql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

try:
    Base.metadata.create_all(engine)
    print("✅ Tables created successfully!")
except OperationalError as e:
    print("❌ Error connecting to database:")
    print(e)
