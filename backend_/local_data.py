import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

CATEGORY_FILES = {
    "관광지": "부산_관광지.json",
    "문화시설": "부산_문화시설.json",
    "축제공연행사": "부산_축제공연행사.json",
    "여행코스": "부산_여행코스.json",
    "레포츠": "부산_레포츠.json",
    "숙박": "부산_숙박.json",
    "쇼핑": "부산_쇼핑.json",
}

_cache = None


def _load_all():
    global _cache
    if _cache is not None:
        return _cache

    items = []
    for category, filename in CATEGORY_FILES.items():
        path = os.path.join(DATA_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            continue
        for raw in data.get("items", []):
            items.append(
                {
                    "category": category,
                    "title": raw.get("title", ""),
                    "addr1": raw.get("addr1", ""),
                    "tel": raw.get("tel") or None,
                }
            )
    _cache = items
    return items


def _tokenize(text: str):
    # 형태소 분석기 없이, 조사가 안 붙었을 2글자 이상 어절 단위로 대충 쪼갠다.
    return [t for t in re.split(r"[\s,.\?!]+", text) if len(t) >= 2]


def search_local_data(query: str, limit: int = 5):
    items = _load_all()
    tokens = _tokenize(query)
    if not tokens:
        return []

    scored = []
    for item in items:
        haystack = f"{item['title']} {item['addr1']}"
        score = sum(1 for t in tokens if t in haystack)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:limit]]
