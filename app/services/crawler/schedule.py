import logging
from app.services.crawler.client import NaverSportClient
from app.services.crawler.parser import ScheduleParser, PreviewParser, ScheduledGame

logger = logging.getLogger(__name__)


class ScheduleCrawlerService:

    def __init__(
        self,
        client: NaverSportClient | None = None,
        parser: ScheduleParser | None = None,
        preview_parser: PreviewParser | None = None,
    ):
        self.client = client or NaverSportClient()
        self.parser = parser or ScheduleParser()
        self.preview_parser = preview_parser or PreviewParser()

    def get_today_game_ids(self) -> list[str]:
        logger.info("오늘 경기 일정 크롤링 시작")

        data = self.client.get_schedule()
        if data is None:
            logger.error("스케줄 조회 실패")
            return []

        game_ids = self.parser.parse_today_game_ids(data)
        logger.info(f"오늘 경기 {len(game_ids)}개 발견 : {game_ids}")

        return game_ids

    def get_today_games(self) -> list[ScheduledGame]:
        logger.info("오늘 경기 일정 조회 (시간 정보 포함)")

        game_ids = self.get_today_game_ids()
        if not game_ids:
            return []

        games = []
        for game_id in game_ids:
            preview_data = self.client.get_game_preview(game_id)
            if preview_data is None:
                logger.warning(f"프리뷰 조회 실패: {game_id}")
                continue

            scheduled_game = self.preview_parser.parse_scheduled_game(game_id, preview_data)
            if scheduled_game is None:
                logger.warning(f"경기 시간 파싱 실패: {game_id}")
                continue

            games.append(scheduled_game)
            logger.info(
                f"  {scheduled_game.away_team_code} vs {scheduled_game.home_team_code} "
                f"@ {scheduled_game.start_time.strftime('%H:%M')}"
            )

        logger.info(f"총 {len(games)}개 경기 조회 완료")
        return games
