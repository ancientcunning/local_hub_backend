import logging
from fastapi import APIRouter
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from local_data import search_local_data

load_dotenv()

logger = logging.getLogger("chatbot")

router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    client = None


class ChatRequest(BaseModel):
    message: str


@router.post("/")
async def chat_with_bot(req: ChatRequest):
    system_prompt = (
        "너는 부울경(부산, 울산, 경남) 지역 정보와 관광, 축제를 안내하는 친절한 어시스턴트야. "
        "답변은 2~3문장, 최대 3줄 이내로 핵심만 간단히 말해. "
        "목록, 번호, 마크다운 서식, 여러 항목 나열은 쓰지 말고 자연스러운 문장으로만 답해. "
        "더 자세한 정보가 필요하면 사용자가 되물을 거라고 생각하고, 먼저 장황하게 설명하지 마."
    )

    matches = search_local_data(req.message)
    if matches:
        context_lines = "\n".join(
            f"- {m['title']} ({m['category']}) - {m['addr1']}" + (f" - 문의 {m['tel']}" if m["tel"] else "")
            for m in matches
        )
        system_prompt += (
            "\n\n아래는 실제 보유 중인 부산 지역 데이터에서 이 질문과 관련해 찾은 장소 목록이야. "
            "질문과 관련 있으면 이 목록에 있는 실제 이름과 정보를 근거로 답변하고, "
            "목록에 없는 내용은 지어내지 마:\n" + context_lines
        )

    if client is None:
        return {"reply": "현재 OpenAI 키가 없어 로컬 데모 응답으로 안내합니다. 예: '부산에서 가볼 만한 곳 추천해줘'처럼 질문해보세요."}

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message}
            ],
            max_completion_tokens=200,
            reasoning_effort="minimal",
        )
        return {"reply": response.choices[0].message.content}
    except Exception:
        logger.exception("OpenAI 챗봇 응답 생성 실패")
        return {"reply": "챗봇 응답 생성 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."}