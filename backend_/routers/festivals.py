import json
import os
from typing import List
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class FestivalItem(BaseModel):
    title: str
    addr1: str | None = None
    contentid: str | None = None
    eventstartdate: str | None = None
    eventenddate: str | None = None


@router.get("/", response_model=List[FestivalItem])
def get_festivals(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'public', '부산', '부산_축제공연행사.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data.get('items', [])

    if start_date and end_date:
        filtered = []
        for item in items:
            item_start = item.get('eventstartdate', '')
            item_end = item.get('eventenddate', '')
            if not item_start and not item_end:
                filtered.append(item)
                continue
            if item_start and item_end and start_date <= item_end and end_date >= item_start:
                filtered.append(item)
            elif item_start and start_date <= item_start <= end_date:
                filtered.append(item)
            elif item_end and start_date <= item_end <= end_date:
                filtered.append(item)
        items = filtered

    if not items:
        return [
            FestivalItem(
                title=item.get('title', ''),
                addr1=item.get('addr1'),
                contentid=item.get('contentid'),
                eventstartdate=item.get('eventstartdate'),
                eventenddate=item.get('eventenddate'),
            )
            for item in data.get('items', [])[:10]
        ]

    return [
        FestivalItem(
            title=item.get('title', ''),
            addr1=item.get('addr1'),
            contentid=item.get('contentid'),
            eventstartdate=item.get('eventstartdate'),
            eventenddate=item.get('eventenddate'),
        )
        for item in items[:30]
    ]
