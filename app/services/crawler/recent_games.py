import logging
from datetime import date, datetime, timedelta

from app.constants import KST
from app.schemas.game import DaySchedule, GameSchedule, RecentGamesResponse
from app.services.crawler.client import NaverSportClient
from app.services.crawler.parser import PreviewParser, ScheduleParser

logger = logging.getLogger(__name__)


class RecentGamesService:

    def __init__(
        self,
        client: NaverSportClient | None = None,
        schedule_parser: ScheduleParser | None = None,
        preview_parser: PreviewParser | None = None,
    ):
        self.client = client or NaverSportClient()
        self.schedule_parser = schedule_parser or ScheduleParser()
        self.preview_parser = preview_parser or PreviewParser()

    def _get_today(self) -> date:
        return datetime.now(KST).date()

    def get_recent_games(self) -> RecentGamesResponse:
        logger.info("최근 3일 경기 일정 조회 시작")

        today = self._get_today()
        target_dates = [today, today - timedelta(days=1), today - timedelta(days=2)]

        schedule_data_by_month: dict[str, dict] = {}
        schedules: list[DaySchedule] = []

        for target_date in target_dates:
            day_schedule = self._get_day_schedule(target_date, schedule_data_by_month)
            schedules.append(day_schedule)

        logger.info("최근 3일 경기 일정 조회 완료")
        return RecentGamesResponse(schedules=schedules)

    def _get_day_schedule(
        self,
        target_date: date,
        schedule_cache: dict[str, dict],
    ) -> DaySchedule:
        date_str = target_date.strftime("%Y-%m-%d")
        month_key = target_date.strftime("%Y-%m")

        if month_key not in schedule_cache:
            data = self.client.get_schedule(target_date)
            if data is not None:
                schedule_cache[month_key] = data

        schedule_data = schedule_cache.get(month_key)
        if schedule_data is None:
            logger.warning(f"스케줄 조회 실패: {date_str}")
            return DaySchedule(date=date_str, games=[])

        naver_date_str = target_date.strftime("%Y-%m-%d")
        game_ids = self.schedule_parser.parse_game_ids_by_date(schedule_data, naver_date_str)

        if not game_ids:
            return DaySchedule(date=date_str, games=[])

        games: list[GameSchedule] = []
        for game_id in game_ids:
            preview_data = self.client.get_game_preview(game_id)
            if preview_data is None:
                logger.warning(f"프리뷰 조회 실패: {game_id}")
                continue

            summary = self.preview_parser.parse_game_summary(preview_data)
            if summary is None:
                logger.warning(f"프리뷰 파싱 실패: {game_id}")
                continue

            games.append(GameSchedule(
                homeTeamCode=summary.home_team_code,
                awayTeamCode=summary.away_team_code,
                homeStarterPitcherName=summary.home_starter_name,
                awayStarterPitcherName=summary.away_starter_name,
            ))

        logger.info(f"{date_str}: {len(games)}개 경기")
        return DaySchedule(date=date_str, games=games)
