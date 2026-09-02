import logging
from datetime import date, datetime, timezone

from app.constants import TEAM_NAMES
from app.models import Player, Team
from app.repositories import PlayerRepository, TeamRepository
from app.schemas.crawl import CrawlResult, NewPlayerInfo
from app.services.crawler.schedule import ScheduleCrawlerService
from app.services.crawler.lineup import LineupCrawlerService
from app.services.crawler.parser import GameLineup, LineupPlayer
from app.services.cache_reset_service import CacheResetService
from app.services.discord_notifier import DiscordNotifier

logger = logging.getLogger(__name__)


class CrawlService:

    def __init__(
        self,
        schedule_crawler: ScheduleCrawlerService | None = None,
        lineup_crawler: LineupCrawlerService | None = None,
        player_repository: PlayerRepository | None = None,
        team_repository: TeamRepository | None = None,
        discord_notifier: DiscordNotifier | None = None,
        cache_reset_service: CacheResetService | None = None,
    ):
        self._schedule_crawler = schedule_crawler or ScheduleCrawlerService()
        self._lineup_crawler = lineup_crawler or LineupCrawlerService()
        self._player_repository = player_repository or PlayerRepository()
        self._team_repository = team_repository or TeamRepository()
        self._discord_notifier = discord_notifier or DiscordNotifier()
        self._cache_reset_service = cache_reset_service or CacheResetService()

    def crawl_game(self, game_id: str) -> CrawlResult:
        logger.info(f"게임 크롤링 시작 : {game_id}")

        lineup = self._lineup_crawler.crawl_lineup(game_id)
        if lineup is None:
            logger.warning(f"라인업 조회 실패 또는 미발표 : {game_id}")
            result = CrawlResult(
                game_id=game_id,
                success=False,
                error_message="라인업 조회 실패 또는 미발표",
            )
            self._notify(result)
            return result

        saved_count, new_players = self._save_lineup(lineup)
        self._update_teams(lineup)

        logger.info(
            f"게임 크롤링 완료 : {game_id}, "
            f"저장된 선수 : {saved_count}명, "
            f"신규 선수 : {len(new_players)}명"
        )
        result = CrawlResult(
            game_id=game_id,
            success=True,
            home_team_code=lineup.home_team_code.lower(),
            away_team_code=lineup.away_team_code.lower(),
            players_saved=saved_count,
            new_players=new_players,
        )
        self._notify(result)
        if result.players_saved > 0:
            self._cache_reset_service.reset()
        return result

    def _notify(self, result: CrawlResult) -> None:
        self._discord_notifier.send_lineup_result(result)
        if result.new_players:
            self._discord_notifier.send_new_players(result.new_players)

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

    def _save_lineup(self, lineup: GameLineup) -> tuple[int, list[NewPlayerInfo]]:
        saved_count = 0
        new_players: list[NewPlayerInfo] = []
        saved_codes: dict[str, set[str]] = {}

        all_entries = [
            (lineup.home_players, lineup.home_team_code),
            (lineup.away_players, lineup.away_team_code),
        ]

        for players, team_code in all_entries:
            player_codes = saved_codes.setdefault(team_code.lower(), set())
            for lineup_player in players:
                player = self._convert_to_player(lineup_player, team_code)
                upsert_result = self._player_repository.upsert(player)
                player_codes.add(player.player_code)
                saved_count += 1
                if upsert_result.created:
                    new_players.append(self._to_new_player_info(player))

        # 새 라인업 저장 후 이전 선발을 해제한다 (중간 실패 시 선발이 비는 것 방지)
        for team_code, player_codes in saved_codes.items():
            self._player_repository.reset_starters(team_code, keep_codes=player_codes)

        return saved_count, new_players

    def _to_new_player_info(self, player: Player) -> NewPlayerInfo:
        return NewPlayerInfo(
            player_code=player.player_code,
            name=player.name,
            team_code=player.team_code,
            back_number=player.back_number,
            position=player.position,
        )

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
            is_lineup_updated_today=True,
            opponent_team_code=opponent_code,
            starter_pitcher_name=starter_name,
            last_game_date=game_date,
            updated_at=updated_at,
        )
        self._team_repository.upsert(team)
