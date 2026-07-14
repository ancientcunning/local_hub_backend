from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import routers.community as community
import routers.chatbot as chatbot
import routers.festivals as festivals

# DB 테이블 자동 생성 (localhub.db 파일이 생김)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LocalHub API")

# 프론트엔드(Vue)에서 백엔드로 통신할 수 있게 문을 열어줌(CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 배포 시 프론트 도메인으로 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(community.router, prefix="/api/posts", tags=["Community"])
app.include_router(chatbot.router, prefix="/api/chat", tags=["Chatbot"])
app.include_router(festivals.router, prefix="/api/festivals", tags=["Festivals"])