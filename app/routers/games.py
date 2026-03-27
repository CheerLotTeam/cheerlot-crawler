import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.game import RecentGamesResponse
from app.services.crawler.recent_games import RecentGamesService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("/recent", response_model=RecentGamesResponse)
def get_recent_games():
    logger.info("API 호출 : /api/games/recent")

    try:
        service = RecentGamesService()
        return service.get_recent_games()
    except Exception as e:
        logger.error(f"최근 경기 조회 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )
