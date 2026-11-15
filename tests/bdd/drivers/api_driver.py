"""HTTP API protocol driver for ChronoQuest BDD acceptance tests."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from httpx import Response


class ChronoQuestApiDriver:
    """Thin HTTP protocol adapter encapsulating REST API calls without test assertions."""

    def __init__(self, client: TestClient) -> None:
        self._client = client

    def list_eras(self) -> Response:
        """Fetch all canonical historical eras from GET /api/v1/eras."""
        return self._client.get("/api/v1/eras")

    def list_events(self, era: str | None = None) -> Response:
        """Fetch historical events ordered chronologically from GET /api/v1/events."""
        params: dict[str, str] = {}
        if era is not None:
            params["era"] = era
        return self._client.get("/api/v1/events", params=params)

    def start_session(
        self,
        player_name: str,
        difficulty: str = "explorer",
        era: str | None = None,
        seed: int | None = 42,
    ) -> Response:
        """Create a new timeline game session via POST /api/v1/sessions."""
        payload: dict[str, Any] = {
            "player_name": player_name,
            "difficulty": difficulty,
            "era": era,
            "seed": seed,
        }
        return self._client.post("/api/v1/sessions", json=payload)

    def get_session(self, session_id: str) -> Response:
        """Fetch a timeline session by ID via GET /api/v1/sessions/{session_id}."""
        return self._client.get(f"/api/v1/sessions/{session_id}")

    def place_event(
        self,
        session_id: str,
        event_id: str,
        position_index: int,
    ) -> Response:
        """Submit a chronological slot placement via POST /api/v1/sessions/{id}/placements."""
        return self._client.post(
            f"/api/v1/sessions/{session_id}/placements",
            json={"event_id": event_id, "position_index": position_index},
        )

    def get_leaderboard(
        self,
        difficulty: str | None = None,
        limit: int = 10,
    ) -> Response:
        """Fetch Hall of Records leaderboard entries via GET /api/v1/leaderboard."""
        params: dict[str, Any] = {"limit": limit}
        if difficulty is not None:
            params["difficulty"] = difficulty
        return self._client.get("/api/v1/leaderboard", params=params)

    @staticmethod
    def find_valid_position_index(
        timeline_cards: list[dict[str, Any]],
        target_year: int,
    ) -> int:
        """Compute the chronologically valid slot index for target_year on the timeline."""
        timeline_years = [int(card["year"]) for card in timeline_cards]
        for idx, placed_year in enumerate(timeline_years):
            if target_year < placed_year:
                return idx
        return len(timeline_years)

    @classmethod
    def find_invalid_position_index(
        cls,
        timeline_cards: list[dict[str, Any]],
        target_year: int,
    ) -> int:
        """Compute a chronologically invalid slot index for target_year on the timeline."""
        valid_idx = cls.find_valid_position_index(timeline_cards, target_year)
        if valid_idx == 0:
            return len(timeline_cards)
        return 0
