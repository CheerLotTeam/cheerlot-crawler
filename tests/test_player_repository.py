from unittest.mock import MagicMock

from app.repositories.player_repository import PlayerRepository


class TestResetStarters:

    def _create_repository(self, mock_client):
        repo = PlayerRepository.__new__(PlayerRepository)
        repo._client = mock_client
        repo._mapper = MagicMock()
        return repo

    def test_resets_existing_starters(self):
        mock_client = MagicMock()
        mock_client.query_database.return_value = [
            {"id": "page-1", "properties": {}},
            {"id": "page-2", "properties": {}},
        ]

        repo = self._create_repository(mock_client)
        repo.database_id  # trigger property
        count = repo.reset_starters("hh")

        assert count == 2
        assert mock_client.update_page.call_count == 2
        mock_client.update_page.assert_any_call(
            "page-1",
            {"is_starter": {"checkbox": False}, "batting_order": {"number": None}},
        )
        mock_client.update_page.assert_any_call(
            "page-2",
            {"is_starter": {"checkbox": False}, "batting_order": {"number": None}},
        )

    def test_no_starters_returns_zero(self):
        mock_client = MagicMock()
        mock_client.query_database.return_value = []

        repo = self._create_repository(mock_client)
        count = repo.reset_starters("kt")

        assert count == 0
        mock_client.update_page.assert_not_called()

    def test_query_filter_uses_team_code_and_is_starter(self):
        mock_client = MagicMock()
        mock_client.query_database.return_value = []

        repo = self._create_repository(mock_client)
        repo.reset_starters("lg")

        call_args = mock_client.query_database.call_args
        filter_arg = call_args.kwargs.get("filter") or call_args[1].get("filter")

        assert filter_arg["and"][0]["property"] == "team_code"
        assert filter_arg["and"][0]["rich_text"]["equals"] == "lg"
        assert filter_arg["and"][1]["property"] == "is_starter"
        assert filter_arg["and"][1]["checkbox"]["equals"] is True


class TestResetStartersKeepCodes:

    def _repository_with_pages(self, pages, player_codes):
        mock_client = MagicMock()
        mock_client.query_database.return_value = pages

        mapper = MagicMock()
        mapper.to_model.side_effect = [
            MagicMock(player_code=code) for code in player_codes
        ]

        repo = PlayerRepository.__new__(PlayerRepository)
        repo._client = mock_client
        repo._mapper = mapper
        return repo, mock_client

    def test_skips_players_in_current_lineup(self):
        pages = [{"id": "page-1"}, {"id": "page-2"}]
        repo, mock_client = self._repository_with_pages(pages, ["hh10", "hh20"])

        count = repo.reset_starters("hh", keep_codes={"hh10"})

        assert count == 1
        mock_client.update_page.assert_called_once_with(
            "page-2",
            {"is_starter": {"checkbox": False}, "batting_order": {"number": None}},
        )

    def test_resets_all_when_keep_codes_empty(self):
        pages = [{"id": "page-1"}, {"id": "page-2"}]
        repo, mock_client = self._repository_with_pages(pages, ["hh10", "hh20"])

        count = repo.reset_starters("hh", keep_codes=set())

        assert count == 2
        assert mock_client.update_page.call_count == 2
