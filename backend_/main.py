import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import routers.community as community
import routers.chatbot as chatbot
import routers.festivals as festivals
import routers.tourism as tourism

# DB 테이블 자동 생성 (localhub.db 파일이 생김)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LocalHub API")

# 프론트엔드(Vue)에서 백엔드로 통신할 수 있게 문을 열어줌(CORS)
# FRONTEND_ORIGIN 환경변수에 배포된 Netlify 도메인을 넣으면 그 도메인만 허용되고,
# 안 넣으면 전체 허용(*)으로 개발 때와 동일하게 동작한다.
_frontend_origin = os.getenv("FRONTEND_ORIGIN")
_allow_origins = [_frontend_origin] if _frontend_origin else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(community.router, prefix="/api/posts", tags=["Community"])
app.include_router(chatbot.router, prefix="/api/chat", tags=["Chatbot"])
app.include_router(festivals.router, prefix="/api/festivals", tags=["Festivals"])
app.include_router(tourism.router, prefix="/api/tourism", tags=["Tourism"])