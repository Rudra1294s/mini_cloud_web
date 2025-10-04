from sqlalchemy import Column, Integer, String, Text, BigInteger, ForeignKey, TIMESTAMP, func
from database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "cloud_schema"}

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)  # store hashed password
    created_at = Column(TIMESTAMP, server_default=func.now())

class File(Base):
    __tablename__ = "files"
    __table_args__ = {"schema": "cloud_schema"}

    file_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("cloud_schema.users.user_id", ondelete="CASCADE"))
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(BigInteger)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())

class Device(Base):
    __tablename__ = "devices"
    __table_args__ = {"schema": "cloud_schema"}

    device_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("cloud_schema.users.user_id", ondelete="CASCADE"))
    device_name = Column(String(100), nullable=False)
    device_ip = Column(String(45))
    registered_at = Column(TIMESTAMP, server_default=func.now())
