import logging
import threading
from datetime import datetime, time, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from app.constants import KST
from app.repositories.team_repository import TeamRepository
from app.schemas.crawl import CrawlResult
from app.services.cache_reset_service import CacheResetService
from app.services.crawl_service import CrawlService
from app.services.crawler.schedule import ScheduleCrawlerService
from app.services.discord_notifier import DiscordNotifier

logger = logging.getLogger(__name__)


class SchedulerService:

    def __init__(
        self,
        schedule_crawler: ScheduleCrawlerService | None = None,
        crawl_service: CrawlService | None = None,
        discord_notifier: DiscordNotifier | None = None,
        team_repository: TeamRepository | None = None,
        cache_reset_service: CacheResetService | None = None,
    ):
        self._schedule_crawler = schedule_crawler or ScheduleCrawlerService()
        self._crawl_service = crawl_service or CrawlService()
        self._discord_notifier = discord_notifier or DiscordNotifier()
        self._team_repository = team_repository or TeamRepository()
        self._cache_reset_service = cache_reset_service or CacheResetService()
        self._scheduler = BackgroundScheduler(timezone=KST)

    def start(self) -> None:
        self._scheduler.add_job(
            func=self._schedule_daily_games,
            trigger=CronTrigger(hour=0, minute=5, timezone=KST),
            id="daily_schedule",
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info("스케줄러 시작")

        threading.Thread(target=self._schedule_daily_games, daemon=True).start()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("스케줄러 종료")

    def _schedule_daily_games(self) -> None:
        reset_count = self._team_repository.reset_today_game_status()
        if reset_count > 0:
            self._cache_reset_service.reset()
        games = self._schedule_crawler.get_today_games()
        self._discord_notifier.send_daily_schedule(games)

        if not games:
            logger.info("오늘 경기 없음")
            return

        self._mark_today_game_teams(games)
        self._cache_reset_service.reset()

        now = datetime.now(KST)
        scheduled_count = 0

        for game in games:
            game_datetime = datetime.combine(now.date(), game.start_time, tzinfo=KST)
            pre_crawl_datetime = game_datetime - timedelta(minutes=30)

            # 경기 시작 30분 전
            if pre_crawl_datetime > now:
                self._scheduler.add_job(
                    func=self._crawl_lineup,
                    trigger=DateTrigger(run_date=pre_crawl_datetime),
                    args=[game.game_id],
                    id=f"pre_{game.game_id}",
                    replace_existing=True,
                )
                scheduled_count += 1

            # 경기 시작 시점
            if game_datetime > now:
                self._scheduler.add_job(
                    func=self._crawl_lineup,
                    trigger=DateTrigger(run_date=game_datetime),
                    args=[game.game_id],
                    id=f"start_{game.game_id}",
                    replace_existing=True,
                )
                scheduled_count += 1

        logger.info(f"{scheduled_count}개 크롤링 스케줄 등록 완료")

    def _crawl_lineup(self, game_id: str) -> None:
        try:
            result = self._crawl_service.crawl_game(game_id)
            if not result.success:
                logger.warning(f"라인업 크롤링 실패: {game_id}")
        except Exception as e:
            logger.exception(f"라인업 크롤링 오류: {game_id}")
            error_result = CrawlResult(
                game_id=game_id,
                success=False,
                error_message=str(e),
            )
            self._discord_notifier.send_lineup_result(error_result)

    def _mark_today_game_teams(self, games: list) -> None:
        team_codes = set()
        for game in games:
            team_codes.add(game.home_team_code)
            team_codes.add(game.away_team_code)

        for team_code in team_codes:
            self._team_repository.set_today_game_status(team_code, True)

        logger.info(f"{len(team_codes)}개 팀 has_today_game 설정 완료")
