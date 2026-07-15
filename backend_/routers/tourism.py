import httpx
from fastapi import APIRouter, HTTPException, Query
from tourapi_client import call_tourapi, TOURAPI_KEY

router = APIRouter()

# 콘텐츠 타입별로 detailIntro2 응답 필드명이 달라서 타입별 매핑이 필요하다.
HOURS_FIELD = {
    "12": "usetime",
    "14": "usetimeculture",
    "15": "usetimefestival",
    "28": "usetimeleports",
    "38": "opentime",
}
CONTACT_FIELD = {
    "12": "infocenter",
    "14": "infocenterculture",
    "25": "infocentertourcourse",
    "28": "infocenterleports",
    "32": "infocenterlodging",
    "38": "infocentershopping",
}
REST_DATE_FIELD = {
    "12": "restdate",
    "14": "restdateculture",
    "28": "restdateleports",
    "38": "restdateshopping",
}
PARKING_FIELD = {
    "12": "parking",
    "14": "parkingculture",
    "28": "parkingleports",
    "32": "parkinglodging",
    "38": "parkingshopping",
}


@router.get("/detail")
async def get_tourism_detail(
    content_id: str = Query(...),
    content_type_id: str = Query(...),
):
    if not TOURAPI_KEY:
        raise HTTPException(status_code=503, detail="TourAPI 키가 설정되지 않았습니다.")

    try:
        # detailCommon2는 contentTypeId를 같이 보내면 오류가 나서 contentId만 사용한다.
        common = await call_tourapi("detailCommon2", contentId=content_id)
        intro = await call_tourapi(
            "detailIntro2", contentId=content_id, contentTypeId=content_type_id
        )
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="TourAPI 요청에 실패했습니다.")

    common = common or {}
    intro = intro or {}

    hours = intro.get(HOURS_FIELD.get(content_type_id, ""))
    if content_type_id == "32":
        checkin = intro.get("checkintime")
        checkout = intro.get("checkouttime")
        if checkin or checkout:
            hours = f"체크인 {checkin or '-'} / 체크아웃 {checkout or '-'}"

    return {
        "overview": common.get("overview") or None,
        "homepage": common.get("homepage") or None,
        "hours": hours or None,
        "rest_date": intro.get(REST_DATE_FIELD.get(content_type_id, "")) or None,
        "parking": intro.get(PARKING_FIELD.get(content_type_id, "")) or None,
        "contact": intro.get(CONTACT_FIELD.get(content_type_id, "")) or None,
    }
