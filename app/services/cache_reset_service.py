import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 3


class CacheResetService:

    def __init__(
        self,
        cache_reset_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self._cache_reset_url = (
            cache_reset_url if cache_reset_url is not None else settings.cache_reset_url
        )
        self._timeout = timeout
        self._max_retries = max_retries

    def _is_enabled(self) -> bool:
        return bool(self._cache_reset_url)

    def reset(self) -> bool:
        if not self._is_enabled():
            return False

        for attempt in range(1, self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(self._cache_reset_url)
                    response.raise_for_status()
                logger.info("캐시 리셋 API 호출 성공")
                return True
            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"캐시 리셋 API 실패 (HTTP {e.response.status_code}), "
                    f"시도 {attempt}/{self._max_retries}"
                )
            except httpx.RequestError as e:
                logger.warning(
                    f"캐시 리셋 API 연결 실패: {e}, "
                    f"시도 {attempt}/{self._max_retries}"
                )

            if attempt < self._max_retries:
                wait = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                time.sleep(wait)

        logger.error(f"캐시 리셋 API 호출 실패 ({self._max_retries}회 재시도 모두 실패)")
        return False
