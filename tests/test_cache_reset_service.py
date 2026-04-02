from unittest.mock import patch, MagicMock

import httpx
import pytest

from app.services.cache_reset_service import CacheResetService, BACKOFF_BASE_SECONDS

TEST_URL = "http://localhost:8080/api/cache/reset"


class TestIsEnabled:

    def test_enabled_with_url(self):
        service = CacheResetService(cache_reset_url=TEST_URL)
        assert service._is_enabled() is True

    def test_disabled_without_url(self):
        service = CacheResetService(cache_reset_url="")
        assert service._is_enabled() is False


class TestReset:

    @patch("app.services.cache_reset_service.httpx.Client")
    def test_success_returns_true(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=MagicMock(
            post=MagicMock(return_value=mock_response)
        ))
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        service = CacheResetService(cache_reset_url=TEST_URL)
        assert service.reset() is True

    def test_disabled_returns_false(self):
        service = CacheResetService(cache_reset_url="")
        assert service.reset() is False

    @patch("app.services.cache_reset_service.time.sleep")
    @patch("app.services.cache_reset_service.httpx.Client")
    def test_retry_on_http_error_then_success(self, mock_client_cls, mock_sleep):
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=error_response
        )

        success_response = MagicMock()
        success_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post = MagicMock(side_effect=[error_response, success_response])
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        service = CacheResetService(cache_reset_url=TEST_URL, max_retries=3)
        assert service.reset() is True
        mock_sleep.assert_called_once_with(BACKOFF_BASE_SECONDS)

    @patch("app.services.cache_reset_service.time.sleep")
    @patch("app.services.cache_reset_service.httpx.Client")
    def test_all_retries_fail_returns_false(self, mock_client_cls, mock_sleep):
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=error_response
        )

        mock_client = MagicMock()
        mock_client.post = MagicMock(return_value=error_response)
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        service = CacheResetService(cache_reset_url=TEST_URL, max_retries=3)
        assert service.reset() is False
        assert mock_sleep.call_count == 2

    @patch("app.services.cache_reset_service.time.sleep")
    @patch("app.services.cache_reset_service.httpx.Client")
    def test_request_error_retries(self, mock_client_cls, mock_sleep):
        mock_client = MagicMock()
        mock_client.post = MagicMock(
            side_effect=httpx.RequestError("Connection refused", request=MagicMock())
        )
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        service = CacheResetService(cache_reset_url=TEST_URL, max_retries=2)
        assert service.reset() is False
        mock_sleep.assert_called_once_with(BACKOFF_BASE_SECONDS)

    @patch("app.services.cache_reset_service.time.sleep")
    @patch("app.services.cache_reset_service.httpx.Client")
    def test_backoff_timing(self, mock_client_cls, mock_sleep):
        error_response = MagicMock()
        error_response.status_code = 503
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Service Unavailable", request=MagicMock(), response=error_response
        )

        mock_client = MagicMock()
        mock_client.post = MagicMock(return_value=error_response)
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        service = CacheResetService(cache_reset_url=TEST_URL, max_retries=4)
        service.reset()

        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        b = BACKOFF_BASE_SECONDS
        assert sleep_calls == [b, b * 2, b * 4]
