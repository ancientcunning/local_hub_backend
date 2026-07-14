from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base
import datetime


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    password = Column(String(50), nullable=False)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
