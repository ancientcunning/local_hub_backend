from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, UniqueConstraint
from database import Base
import datetime


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    password = Column(String(50), nullable=False)
    category = Column(String(20), nullable=False, default="spot")
    author = Column(String(50), nullable=False, default="익명")
    image = Column(String(500), nullable=True)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    password = Column(String(50), nullable=False)
    author = Column(String(50), nullable=False, default="익명")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PostLike(Base):
    __tablename__ = "post_likes"
    __table_args__ = (UniqueConstraint("post_id", "ip_address", name="uq_post_like_ip"),)

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PostView(Base):
    __tablename__ = "post_views"
    __table_args__ = (UniqueConstraint("post_id", "ip_address", name="uq_post_view_ip"),)

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
