import logging
from app.services.crawler.client import NaverSportClient
from app.services.crawler.parser import ScheduleParser

logger = logging.getLogger(__name__)

class ScheduleCrawlerService:

    def __init__(
        self,
        client: NaverSportClient | None = None,
        parser: ScheduleParser | None = None,
    ):
        self.client = client or NaverSportClient()
        self.parser = parser or ScheduleParser()

    def get_today_game_ids(self) -> list[str]:
        logger.info("오늘 경기 일정 크롤링 시작")

        data = self.client.get_schedule()
        if data is None:
            logger.error("스케줄 조회 실패")
            return []

        game_ids = self.parser.parse_today_game_ids(data)
        logger.info(f"오늘 경기 {len(game_ids)}개 발견 : {game_ids}")

        return game_ids
