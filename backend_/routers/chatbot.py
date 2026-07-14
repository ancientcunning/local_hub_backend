from fastapi import APIRouter
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

try:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
except Exception:
    openai = None


class ChatRequest(BaseModel):
    message: str


@router.post("/")
async def chat_with_bot(req: ChatRequest):
    system_prompt = (
        "너는 부울경(부산, 울산, 경남) 지역 정보와 관광, 축제를 안내하는 친절한 어시스턴트야. "
        "짧고 실용적으로 답변해줘."
    )

    if openai is None:
        return {"reply": "현재 OpenAI 키가 없어 로컬 데모 응답으로 안내합니다. 예: '부산에서 가볼 만한 곳 추천해줘'처럼 질문해보세요."}

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message}
            ],
        )
        return {"reply": response.choices[0].message.content}
    except Exception:
        return {"reply": "챗봇 응답 생성 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."}