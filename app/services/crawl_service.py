import logging
from datetime import date, datetime, timezone

from app.models import Player, Team
from app.repositories import PlayerRepository, TeamRepository
from app.schemas.crawl import CrawlResult
from app.services.crawler.schedule import ScheduleCrawlerService
from app.services.crawler.lineup import LineupCrawlerService
from app.services.crawler.parser import GameLineup, LineupPlayer

logger = logging.getLogger(__name__)

TEAM_NAMES = {
    "hh": "한화 이글스",
    "kt": "KT 위즈",
    "lg": "LG 트윈스",
    "nc": "NC 다이노스",
    "ob": "두산 베어스",
    "sk": "SSG 랜더스",
    "ss": "삼성 라이온즈",
    "wo": "키움 히어로즈",
    "ht": "KIA 타이거즈",
    "lt": "롯데 자이언츠",
}


class CrawlService:

    def __init__(
        self,
        schedule_crawler: ScheduleCrawlerService | None = None,
        lineup_crawler: LineupCrawlerService | None = None,
        player_repository: PlayerRepository | None = None,
        team_repository: TeamRepository | None = None,
    ):
        self._schedule_crawler = schedule_crawler or ScheduleCrawlerService()
        self._lineup_crawler = lineup_crawler or LineupCrawlerService()
        self._player_repository = player_repository or PlayerRepository()
        self._team_repository = team_repository or TeamRepository()

    def crawl_game(self, game_id: str) -> CrawlResult:
        logger.info(f"게임 크롤링 시작 : {game_id}")

        lineup = self._lineup_crawler.crawl_lineup(game_id)
        if lineup is None:
            logger.warning(f"라인업 조회 실패 또는 미발표 : {game_id}")
            return CrawlResult(
                game_id=game_id,
                success=False,
                error_message="라인업 조회 실패 또는 미발표",
            )

        saved_count = self._save_lineup(lineup)
        self._update_teams(lineup)

        logger.info(f"게임 크롤링 완료 : {game_id}, 저장된 선수 : {saved_count}명")
        return CrawlResult(
            game_id=game_id,
            success=True,
            home_team_code=lineup.home_team_code.lower(),
            away_team_code=lineup.away_team_code.lower(),
            players_saved=saved_count,
        )

    def crawl_today_games(self) -> list[CrawlResult]:
        logger.info("오늘 경기 크롤링 시작")

        game_ids = self._schedule_crawler.get_today_game_ids()
        if not game_ids:
            logger.info("오늘 예정된 경기 없음")
            return []

        logger.info(f"오늘 경기 {len(game_ids)}개 발견")

        results = []
        for game_id in game_ids:
            try:
                result = self.crawl_game(game_id)
                results.append(result)
            except Exception as e:
                logger.exception(f"게임 처리 중 예외 발생 : {game_id}")
                results.append(CrawlResult(
                    game_id=game_id,
                    success=False,
                    error_message=str(e),
                ))

        success_count = sum(1 for r in results if r.success)
        logger.info(f"오늘 경기 크롤링 완료 : {success_count} / {len(game_ids)} 성공")

        return results

    def _save_lineup(self, lineup: GameLineup) -> int:
        saved_count = 0

        for lineup_player in lineup.home_players:
            player = self._convert_to_player(lineup_player, lineup.home_team_code)
            self._player_repository.upsert(player)
            saved_count += 1

        for lineup_player in lineup.away_players:
            player = self._convert_to_player(lineup_player, lineup.away_team_code)
            self._player_repository.upsert(player)
            saved_count += 1

        return saved_count

    def _convert_to_player(self, lineup_player: LineupPlayer, team_code: str) -> Player:
        back_number_str = lineup_player.back_number or "00"
        try:
            back_number = int(back_number_str)
        except ValueError:
            back_number = 0

        team_code_lower = team_code.lower()
        player_code = f"{team_code_lower}{back_number_str}"

        return Player(
            player_code=player_code,
            team_code=team_code_lower,
            name=lineup_player.name,
            back_number=back_number,
            position=lineup_player.position,
            bat_throw=lineup_player.bats_throws or "",
            batting_order=lineup_player.bat_order,
            is_starter=True,
        )

    def _update_teams(self, lineup: GameLineup) -> None:
        home_team_code = lineup.home_team_code.lower()
        away_team_code = lineup.away_team_code.lower()
        game_date = lineup.game_date or date.today()
        now = datetime.now(timezone.utc)

        self._update_single_team(
            team_code=home_team_code,
            opponent_code=away_team_code,
            starter_name=lineup.home_starter_name,
            game_date=game_date,
            updated_at=now,
        )
        logger.info(f"홈 팀 정보 업데이트 : {home_team_code}")

        self._update_single_team(
            team_code=away_team_code,
            opponent_code=home_team_code,
            starter_name=lineup.away_starter_name,
            game_date=game_date,
            updated_at=now,
        )
        logger.info(f"원정 팀 정보 업데이트 : {away_team_code}")

    def _update_single_team(
        self,
        team_code: str,
        opponent_code: str,
        starter_name: str | None,
        game_date: date,
        updated_at: datetime,
    ) -> None:
        team_name = TEAM_NAMES.get(team_code, team_code)

        team = Team(
            team_code=team_code,
            team_name=team_name,
            has_today_game=True,
            opponent_team_code=opponent_code,
            starter_pitcher_name=starter_name,
            last_game_date=game_date,
            updated_at=updated_at,
        )
        self._team_repository.upsert(team)
