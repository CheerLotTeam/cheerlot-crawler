import logging
from app.services.crawler.client import NaverSportClient
from app.services.crawler.parser import PreviewParser, GameLineup

logger = logging.getLogger(__name__)

class LineupCrawlerService:
    def __init__(
            self,
            client: NaverSportClient | None = None,
            parser: PreviewParser | None = None,
    ):

        self.client = client or NaverSportClient()
        self.parser = parser or PreviewParser()

    def crawl_lineup(self, game_id: str) -> GameLineup | None:
        """단일 게임 라인업 크롤링"""
        logger.info(f"게임 라인업 크롤링 시작 : {game_id}")

        data = self.client.get_game_preview(game_id)
        if data is None:
            logger.error(f"게임 프리뷰 조회 실패 : {game_id}")
            return None

        lineup = self.parser.parse(data)
        if lineup is None:
            logger.warning(f"라인업 파싱 실패 또는 미발표 : {game_id}")
            return None

        logger.info(
            f"라인업 크롤링 완료 : {game_id} "
            f"(홈 : {len(lineup.home_players)}명, 원정 : {len(lineup.away_players)}명)"
        )
        return lineup

    def crawl_lineups(self, game_ids: list[str]) -> list[GameLineup]:
        """여러 게임 라인업 크롤링"""
        results = []

        for game_id in game_ids:
            try:
                lineup = self.crawl_lineup(game_id)
                if lineup:
                    results.append(lineup)
            except Exception as e:
                logger.exception(f"게임 처리 중 예외 발생 : {game_id}")
                continue

        logger.info(f"전체 크롤링 완료 : {len(results)} / {len(game_ids)} 게임 라인업 크롤링 성공")
        return results
