import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from app.services.crawl_service import CrawlService
from app.services.crawler.schedule import ScheduleCrawlerService

logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")


class SchedulerService:

    def __init__(
        self,
        schedule_crawler: ScheduleCrawlerService | None = None,
        crawl_service: CrawlService | None = None,
    ):
        self._schedule_crawler = schedule_crawler or ScheduleCrawlerService()
        self._crawl_service = crawl_service or CrawlService()
        self._scheduler = BackgroundScheduler(timezone=KST)

    def start(self) -> None:
        self._scheduler.add_job(
            func=self._schedule_daily_games,
            trigger=CronTrigger(hour=6, minute=0),
            id="daily_schedule",
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info("스케줄러 시작")

        self._schedule_daily_games()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("스케줄러 종료")

    def _schedule_daily_games(self) -> None:
        games = self._schedule_crawler.get_today_games()
        if not games:
            logger.info("오늘 경기 없음")
            return

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
        except Exception:
            logger.exception(f"라인업 크롤링 오류: {game_id}")
