import logging
from fastapi import APIRouter

from app.services.crawl_service import CrawlService
from app.schemas.crawl import GameCrawlResponse, TodayCrawlResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawl", tags=["crawl"])


@router.post("/game/{game_id}", response_model=GameCrawlResponse)
def crawl_game(game_id: str):
    logger.info(f"API 호출 : /crawl/game/{game_id}")

    service = CrawlService()
    result = service.crawl_game(game_id)

    return GameCrawlResponse.from_result(result)


@router.post("/today", response_model=TodayCrawlResponse)
def crawl_today():
    logger.info("API 호출 : /crawl/today")

    service = CrawlService()
    results = service.crawl_today_games()

    success_count = sum(1 for r in results if r.success)

    return TodayCrawlResponse(
        total_games=len(results),
        success_count=success_count,
        fail_count=len(results) - success_count,
        results=[GameCrawlResponse.from_result(r) for r in results],
    )
