from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
import models
from pydantic import BaseModel, ConfigDict
from typing import List


class PostUpdate(BaseModel):
    title: str
    content: str
    password: str

router = APIRouter()

# 요청/응답 데이터 검증용 스키마
class PostCreate(BaseModel):
    title: str
    content: str
    password: str

class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    views: int
    likes: int
    # 보안상 password는 응답에서 제외

# 1. 목록 조회 (검색 + 페이지네이션)
@router.get("/", response_model=dict)
def get_posts(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
):
    query = db.query(models.Post)
    if search:
        query = query.filter(models.Post.title.contains(search) | models.Post.content.contains(search))

    total = query.count()
    posts = query.order_by(models.Post.id.desc()).offset((page - 1) * limit).limit(limit).all()
    serialized_posts = [
        PostResponse(
            id=post.id,
            title=post.title,
            content=post.content,
            views=post.views,
            likes=post.likes,
        )
        for post in posts
    ]
    return {"items": serialized_posts, "page": page, "limit": limit, "total": total}

# 2. 글 작성
@router.post("/", response_model=PostResponse)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    new_post = models.Post(title=post.title, content=post.content, password=post.password)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.get("/health")
def health_check():
    return {"status": "ok"}

# 3. 상세 조회 (조회수 1 증가)
@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    post.views += 1
    db.commit()
    db.refresh(post)
    return post

# 4. 수정 (비밀번호 확인)
@router.put("/{post_id}", response_model=PostResponse)
def update_post(post_id: int, payload: PostUpdate, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.password != payload.password:
        raise HTTPException(status_code=403, detail="비밀번호가 틀렸습니다.")

    post.title = payload.title
    post.content = payload.content
    db.commit()
    db.refresh(post)
    return post

# 5. 좋아요
@router.post("/{post_id}/like", response_model=PostResponse)
def like_post(post_id: int, payload: dict | None = None, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    post.likes += 1
    db.commit()
    db.refresh(post)
    return post

# 6. 삭제 (비밀번호 확인)
@router.delete("/{post_id}")
def delete_post(post_id: int, password: str, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.password != password:
        raise HTTPException(status_code=403, detail="비밀번호가 틀렸습니다.")

    db.delete(post)
    db.commit()
    return {"message": "삭제 완료"}
