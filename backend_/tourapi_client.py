import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TOURAPI_KEY = os.getenv("TOURAPI_KEY")
BASE_URL = "https://apis.data.go.kr/B551011/KorService2"


async def call_tourapi(operation: str, **params):
    query = {
        "serviceKey": TOURAPI_KEY,
        "MobileOS": "ETC",
        "MobileApp": "LocalHub",
        "_type": "json",
        **params,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(f"{BASE_URL}/{operation}", params=query)

    res.raise_for_status()
    data = res.json()
    body = data.get("response", {}).get("body")
    if not body:
        return None
    items = body.get("items")
    if not items:
        return None
    item = items.get("item")
    if isinstance(item, list):
        return item[0] if item else None
    return item
