from unittest.mock import patch, MagicMock

import httpx
import pytest

from app.services.crawler.client import NaverSportClient


class TestRequestWithRetry:

    @patch("app.services.crawler.client.httpx.Client")
    def test_success_on_first_attempt(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "ok"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.request = MagicMock(return_value=mock_response)
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        client = NaverSportClient(max_retries=3)
        result = client._request_with_retry("GET", "http://test.com/api")

        assert result == {"result": "ok"}
        assert mock_client.request.call_count == 1

    @patch("app.services.crawler.client.httpx.Client")
    def test_retry_on_timeout_then_success(self, mock_client_cls):
        success_response = MagicMock()
        success_response.json.return_value = {"result": "ok"}
        success_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.request = MagicMock(
            side_effect=[
                httpx.RequestError("The read operation timed out", request=MagicMock()),
                success_response,
            ]
        )
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        client = NaverSportClient(max_retries=3)
        result = client._request_with_retry("GET", "http://test.com/api")

        assert result == {"result": "ok"}
        assert mock_client.request.call_count == 2

    @patch("app.services.crawler.client.httpx.Client")
    def test_all_retries_fail_returns_none(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.request = MagicMock(
            side_effect=httpx.RequestError("Connection refused", request=MagicMock())
        )
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        client = NaverSportClient(max_retries=3)
        result = client._request_with_retry("GET", "http://test.com/api")

        assert result is None
        assert mock_client.request.call_count == 3

    @patch("app.services.crawler.client.httpx.Client")
    def test_retry_on_http_status_error(self, mock_client_cls):
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=error_response
        )

        success_response = MagicMock()
        success_response.json.return_value = {"result": "ok"}
        success_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.request = MagicMock(
            side_effect=[error_response, success_response]
        )
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        client = NaverSportClient(max_retries=3)
        result = client._request_with_retry("GET", "http://test.com/api")

        assert result == {"result": "ok"}
        assert mock_client.request.call_count == 2


class TestGetGamePreview:

    @patch("app.services.crawler.client.httpx.Client")
    def test_calls_correct_url(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "preview"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.request = MagicMock(return_value=mock_response)
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        client = NaverSportClient()
        result = client.get_game_preview("20260317HTNC0")

        call_args = mock_client.request.call_args
        assert call_args[0][1] == "https://api-gw.sports.naver.com/schedule/games/20260317HTNC0/preview"
        assert result == {"data": "preview"}
