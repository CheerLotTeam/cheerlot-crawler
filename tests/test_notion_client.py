from unittest.mock import patch, MagicMock

import httpx
import pytest

from app.infrastructure.notion.client import NotionClient, NotionClientError


class TestRequestWithRetry:

    @patch("app.infrastructure.notion.client.httpx.Client")
    def test_success_on_first_attempt(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": [{"id": "page1"}]}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        client = NotionClient(api_key="test-key")
        result = client.query_database("db-id", filter={"property": "Name"})

        assert result == [{"id": "page1"}]

    @patch("app.infrastructure.notion.client.time.sleep")
    @patch("app.infrastructure.notion.client.httpx.Client")
    def test_retry_on_timeout_then_success(self, mock_client_cls, mock_sleep):
        success_response = MagicMock()
        success_response.json.return_value = {"results": []}
        success_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.request.side_effect = [
            httpx.ReadTimeout("The read operation timed out", request=MagicMock()),
            success_response,
        ]
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        client = NotionClient(api_key="test-key", max_retries=3)
        result = client.query_database("db-id")

        assert result == []
        mock_sleep.assert_called_once_with(1)

    @patch("app.infrastructure.notion.client.time.sleep")
    @patch("app.infrastructure.notion.client.httpx.Client")
    def test_all_retries_fail_raises_error(self, mock_client_cls, mock_sleep):
        mock_client = MagicMock()
        mock_client.request.side_effect = httpx.ReadTimeout(
            "The read operation timed out", request=MagicMock()
        )
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        client = NotionClient(api_key="test-key", max_retries=3)

        with pytest.raises(NotionClientError, match="최종 실패"):
            client.query_database("db-id")

        assert mock_sleep.call_count == 2

    @patch("app.infrastructure.notion.client.httpx.Client")
    def test_http_status_error_no_retry(self, mock_client_cls):
        error_response = MagicMock()
        error_response.status_code = 400
        error_response.text = "Bad Request"

        mock_client = MagicMock()
        mock_client.request.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=error_response
        )
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        client = NotionClient(api_key="test-key", max_retries=3)

        with pytest.raises(NotionClientError, match="HTTP 400"):
            client.query_database("db-id")

        assert mock_client.request.call_count == 1


class TestCreatePage:

    @patch("app.infrastructure.notion.client.httpx.Client")
    def test_create_page_success(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "new-page"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        client = NotionClient(api_key="test-key")
        result = client.create_page("db-id", {"Name": {"title": [{"text": {"content": "Test"}}]}})

        assert result == {"id": "new-page"}


class TestUpdatePage:

    @patch("app.infrastructure.notion.client.httpx.Client")
    def test_update_page_success(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "page-1"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        client = NotionClient(api_key="test-key")
        result = client.update_page("page-1", {"Status": {"checkbox": True}})

        assert result == {"id": "page-1"}
