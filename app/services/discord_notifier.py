import logging
from datetime import datetime

import httpx

from app.config import settings
from app.constants import KST, TEAM_NAMES
from app.schemas.crawl import CrawlResult, NewPlayerInfo
from app.services.crawler.parser import ScheduledGame

logger = logging.getLogger(__name__)


class DiscordNotifier:

    def __init__(self, webhook_url: str | None = None, timeout: float = 10.0):
        self._webhook_url = webhook_url if webhook_url is not None else settings.discord_webhook_url
        self._timeout = timeout

    def _is_enabled(self) -> bool:
        return bool(self._webhook_url)

    def send_daily_schedule(self, games: list[ScheduledGame]) -> None:
        if not self._is_enabled():
            return

        now = datetime.now(KST)
        date_str = now.strftime("%Y-%m-%d (%a)")

        if not games:
            embed = self._build_embed(
                title="KBO 오늘의 경기",
                description=f"{date_str}\n\n경기 없음",
                color=0x808080,
            )
        else:
            lines = []
            for game in games:
                away = TEAM_NAMES.get(game.away_team_code, game.away_team_code)
                home = TEAM_NAMES.get(game.home_team_code, game.home_team_code)
                time_str = game.start_time.strftime("%H:%M")
                lines.append(f"**{away}** vs **{home}** - {time_str}")

            embed = self._build_embed(
                title="KBO 오늘의 경기",
                description=f"{date_str}\n\n" + "\n".join(lines),
                color=0x3498DB,
                footer=f"총 {len(games)}경기",
            )

        self._send(embeds=[embed])

    def send_lineup_result(self, result: CrawlResult) -> None:
        if not self._is_enabled():
            return

        if result.success:
            home = TEAM_NAMES.get(result.home_team_code or "", result.home_team_code or "")
            away = TEAM_NAMES.get(result.away_team_code or "", result.away_team_code or "")
            embed = self._build_embed(
                title="라인업 크롤링 완료",
                description=(
                    f"**{away}** vs **{home}**\n\n"
                    f"저장된 선수: {result.players_saved}명\n"
                    f"신규 선수: {len(result.new_players)}명"
                ),
                color=0x2ECC71,
                footer=f"Game ID: {result.game_id}",
            )
        else:
            embed = self._build_embed(
                title="라인업 크롤링 실패",
                description=(
                    f"Game ID: `{result.game_id}`\n"
                    f"오류: {result.error_message or '알 수 없는 오류'}"
                ),
                color=0xE74C3C,
            )

        self._send(embeds=[embed])

    def send_new_players(self, new_players: list[NewPlayerInfo]) -> None:
        if not self._is_enabled() or not new_players:
            return

        lines = []
        for p in new_players:
            team = TEAM_NAMES.get(p.team_code, p.team_code)
            lines.append(f"**{p.name}** ({team}) #{p.back_number} {p.position}")

        embed = self._build_embed(
            title="신규 선수 등록",
            description="\n".join(lines),
            color=0xF39C12,
            footer=f"총 {len(new_players)}명 신규 등록",
        )

        self._send(embeds=[embed])

    def _build_embed(
        self,
        title: str,
        description: str,
        color: int,
        footer: str | None = None,
    ) -> dict:
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.now(KST).isoformat(),
        }
        if footer:
            embed["footer"] = {"text": footer}
        return embed

    def _send(self, embeds: list[dict]) -> None:
        payload = {
            "username": "Cheerlot Crawler",
            "embeds": embeds,
        }
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(self._webhook_url, json=payload)
                response.raise_for_status()
            logger.info(f"Discord 알림 전송 완료: {embeds[0].get('title', '')}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Discord 웹훅 전송 실패 (HTTP {e.response.status_code})")
        except httpx.RequestError as e:
            logger.error(f"Discord 웹훅 연결 실패: {e}")
