from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from database import get_db
import models
from pydantic import BaseModel, ConfigDict
from typing import List


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class PostUpdate(BaseModel):
    title: str
    content: str
    password: str
    category: str = "spot"
    image: str | None = None

router = APIRouter()

# 요청/응답 데이터 검증용 스키마
class PostCreate(BaseModel):
    title: str
    content: str
    password: str
    category: str = "spot"
    author: str = "익명"
    image: str | None = None

class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    category: str
    author: str
    image: str | None = None
    views: int
    likes: int
    comments: int
    created_at: datetime
    is_liked: bool = False
    # 보안상 password는 응답에서 제외

class PasswordVerify(BaseModel):
    password: str

class CommentCreate(BaseModel):
    content: str
    password: str

class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    content: str
    author: str
    created_at: datetime
    # 보안상 password는 응답에서 제외

# 1. 목록 조회 (검색 + 페이지네이션)
@router.get("/", response_model=dict)
def get_posts(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
):
    query = db.query(models.Post)
    if search:
        query = query.filter(models.Post.title.contains(search) | models.Post.content.contains(search))
    if category and category != "all":
        query = query.filter(models.Post.category == category)

    total = query.count()
    posts = query.order_by(models.Post.id.desc()).offset((page - 1) * limit).limit(limit).all()
    serialized_posts = [PostResponse.model_validate(post) for post in posts]
    return {"items": serialized_posts, "page": page, "limit": limit, "total": total}

# 2. 글 작성
@router.post("/", response_model=PostResponse)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    new_post = models.Post(
        title=post.title,
        content=post.content,
        password=post.password,
        category=post.category,
        author=post.author,
        image=post.image,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.get("/health")
def health_check():
    return {"status": "ok"}

# 3. 상세 조회 (IP당 조회수 1회 증가)
@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    ip = get_client_ip(request)
    already_viewed = (
        db.query(models.PostView)
        .filter(models.PostView.post_id == post_id, models.PostView.ip_address == ip)
        .first()
    )
    if not already_viewed:
        db.add(models.PostView(post_id=post_id, ip_address=ip))
        post.views += 1

    already_liked = (
        db.query(models.PostLike)
        .filter(models.PostLike.post_id == post_id, models.PostLike.ip_address == ip)
        .first()
        is not None
    )

    db.commit()
    db.refresh(post)

    response = PostResponse.model_validate(post)
    response.is_liked = already_liked
    return response

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
    post.category = payload.category
    post.image = payload.image
    db.commit()
    db.refresh(post)
    return post

# 4-1. 비밀번호 확인 (수정/삭제 진입 전 확인용, 데이터는 변경하지 않음)
@router.post("/{post_id}/verify-password")
def verify_password(post_id: int, payload: PasswordVerify, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return {"valid": post.password == payload.password}

# 5. 좋아요 토글 (IP당 좋아요 상태 반전)
@router.post("/{post_id}/like", response_model=PostResponse)
def like_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    ip = get_client_ip(request)
    existing_like = (
        db.query(models.PostLike)
        .filter(models.PostLike.post_id == post_id, models.PostLike.ip_address == ip)
        .first()
    )
    if existing_like:
        db.delete(existing_like)
        if post.likes > 0:
            post.likes -= 1
        is_liked = False
    else:
        db.add(models.PostLike(post_id=post_id, ip_address=ip))
        post.likes += 1
        is_liked = True

    db.commit()
    db.refresh(post)

    response = PostResponse.model_validate(post)
    response.is_liked = is_liked
    return response

# 6. 삭제 (비밀번호 확인)
@router.delete("/{post_id}")
def delete_post(post_id: int, password: str, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.password != password:
        raise HTTPException(status_code=403, detail="비밀번호가 틀렸습니다.")

    db.query(models.Comment).filter(models.Comment.post_id == post_id).delete()
    db.query(models.PostLike).filter(models.PostLike.post_id == post_id).delete()
    db.query(models.PostView).filter(models.PostView.post_id == post_id).delete()
    db.delete(post)
    db.commit()
    return {"message": "삭제 완료"}

# 7. 댓글 목록 조회
@router.get("/{post_id}/comments", response_model=List[CommentResponse])
def get_comments(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return (
        db.query(models.Comment)
        .filter(models.Comment.post_id == post_id)
        .order_by(models.Comment.id.asc())
        .all()
    )

# 8. 댓글 작성 (익명)
@router.post("/{post_id}/comments", response_model=CommentResponse)
def create_comment(post_id: int, payload: CommentCreate, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    comment = models.Comment(post_id=post_id, content=payload.content, password=payload.password)
    db.add(comment)
    post.comments += 1
    db.commit()
    db.refresh(comment)
    return comment

# 9. 댓글 삭제 (비밀번호 확인)
@router.delete("/{post_id}/comments/{comment_id}")
def delete_comment(post_id: int, comment_id: int, password: str, db: Session = Depends(get_db)):
    comment = (
        db.query(models.Comment)
        .filter(models.Comment.id == comment_id, models.Comment.post_id == post_id)
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if comment.password != password:
        raise HTTPException(status_code=403, detail="비밀번호가 틀렸습니다.")

    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    db.delete(comment)
    if post and post.comments > 0:
        post.comments -= 1
    db.commit()
    return {"message": "삭제 완료"}
