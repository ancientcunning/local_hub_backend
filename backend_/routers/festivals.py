import asyncio
import json
import os
from fastapi import APIRouter
from tourapi_client import call_tourapi

router = APIRouter()

DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "부산_축제공연행사.json"
)

_cache = None
_cache_lock = asyncio.Lock()
_request_semaphore = asyncio.Semaphore(10)


async def enrich_festival(item: dict) -> dict:
    try:
        async with _request_semaphore:
            intro = await call_tourapi("detailIntro2", contentId=item.get("contentid"), contentTypeId="15")
    except Exception:
        intro = None
    intro = intro or {}

    return {
        "contentid": item.get("contentid"),
        "title": item.get("title"),
        "addr1": item.get("addr1"),
        "image": item.get("firstimage") or item.get("firstimage2"),
        "tel": item.get("tel"),
        "mapx": item.get("mapx"),
        "mapy": item.get("mapy"),
        "eventstartdate": intro.get("eventstartdate") or None,
        "eventenddate": intro.get("eventenddate") or None,
        "eventplace": intro.get("eventplace") or None,
    }


async def build_festival_list():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    results = await asyncio.gather(*(enrich_festival(item) for item in items))
    # 실제 축제 기간 정보(eventstartdate)가 있는 항목만 캘린더에 의미가 있다.
    return [r for r in results if r["eventstartdate"]]


@router.get("/")
async def get_festivals():
    global _cache
    if _cache is None:
        async with _cache_lock:
            if _cache is None:
                _cache = await build_festival_list()
    return _cache
