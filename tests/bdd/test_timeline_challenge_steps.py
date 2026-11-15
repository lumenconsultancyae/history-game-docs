"""Step definitions for World History Timeline Placement Challenge BDD scenarios."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from history_game.api.app import create_app
from history_game.config.settings import Settings
from .drivers.api_driver import ChronoQuestApiDriver

FEATURE_PATH = Path(__file__).resolve().parents[2] / "features" / "timeline_challenge.feature"
scenarios(str(FEATURE_PATH))


@dataclass
class ScenarioContext:
    """Typed per-scenario state container for BDD steps."""

    events_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    eras_response: list[dict[str, Any]] = field(default_factory=list)
    filtered_events: list[dict[str, Any]] = field(default_factory=list)
    session: dict[str, Any] = field(default_factory=dict)
    last_attempt: dict[str, Any] = field(default_factory=dict)
    lives_before_placement: int = 0


@pytest.fixture
def context() -> ScenarioContext:
    """Provide an isolated ScenarioContext instance per scenario."""
    return ScenarioContext()


@pytest.fixture
def api_driver(tmp_path: Path) -> Iterator[ChronoQuestApiDriver]:
    """Provide a ChronoQuestApiDriver backed by an isolated temporary SQLite database."""
    db_file = tmp_path / "bdd_history_game.db"
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{db_file}",
        seed_on_startup=True,
        static_dir=str(tmp_path / "nonexistent_static"),
    )
    app = create_app(settings=settings)
    with TestClient(app) as client:
        yield ChronoQuestApiDriver(client=client)


@given("the canonical World History catalog of 24 events across 6 historical eras is available")
def given_canonical_catalog_available(
    api_driver: ChronoQuestApiDriver,
    context: ScenarioContext,
) -> None:
    """Verify the seeded 24-event catalog across 6 eras and index events by ID."""
    eras_resp = api_driver.list_eras()
    assert eras_resp.status_code == 200
    eras = eras_resp.json()
    assert len(eras) == 6

    events_resp = api_driver.list_events()
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) == 24
    context.events_by_id = {event["id"]: event for event in events}


@when("the player requests the catalog of historical eras")
def when_player_requests_eras(
    api_driver: ChronoQuestApiDriver,
    context: ScenarioContext,
) -> None:
    """Request the catalog of historical eras."""
    resp = api_driver.list_eras()
    assert resp.status_code == 200
    context.eras_response = resp.json()


@then("6 historical eras are returned in chronological order:")
def then_six_eras_returned_in_order(
    context: ScenarioContext,
    datatable: list[list[str]],
) -> None:
    """Verify the 6 returned eras match the expected chronological table."""
    headers = datatable[0]
    expected_rows = [dict(zip(headers, row, strict=True)) for row in datatable[1:]]
    assert len(context.eras_response) == len(expected_rows) == 6
    actual_rows = [
        {"era": item["era"], "label": item["label"]}
        for item in context.eras_response
    ]
    assert actual_rows == expected_rows


@when(parsers.parse('the player browses historical events filtered by era "{era}"'))
def when_player_browses_events_by_era(
    api_driver: ChronoQuestApiDriver,
    context: ScenarioContext,
    era: str,
) -> None:
    """Request historical events filtered by a specific era."""
    resp = api_driver.list_events(era=era)
    assert resp.status_code == 200
    context.filtered_events = resp.json()


@then(parsers.parse('every returned historical event belongs to era "{era}"'))
def then_every_event_belongs_to_era(
    context: ScenarioContext,
    era: str,
) -> None:
    """Verify non-empty results and that all returned events match the requested era."""
    assert len(context.filtered_events) >= 4
    assert all(ev["era"] == era for ev in context.filtered_events)


@then("the events are ordered chronologically with formatted BCE or CE year labels")
def then_events_ordered_with_year_labels(context: ScenarioContext) -> None:
    """Verify chronological sorting and formatted BCE/CE year labels."""
    years = [int(ev["year"]) for ev in context.filtered_events]
    assert years == sorted(years)
    assert all(
        ev["year_label"].endswith("BCE") or ev["year_label"].endswith("CE")
        for ev in context.filtered_events
    )


@when(
    parsers.parse(
        'player "{player_name}" starts a new timeline session on difficulty "{difficulty}"'
    )
)
@given(
    parsers.parse(
        'player "{player_name}" has an active "{difficulty}" timeline session'
    )
)
def start_active_timeline_session(
    api_driver: ChronoQuestApiDriver,
    context: ScenarioContext,
    player_name: str,
    difficulty: str,
) -> None:
    """Start a new timeline session for the given player and difficulty."""
    resp = api_driver.start_session(
        player_name=player_name,
        difficulty=difficulty,
        seed=42,
    )
    assert resp.status_code == 201
    context.session = resp.json()


@given(
    parsers.parse(
        'player "{player_name}" has an active "{difficulty}" timeline session with a current streak of {streak:d}'
    )
)
def given_active_session_with_streak(
    api_driver: ChronoQuestApiDriver,
    context: ScenarioContext,
    player_name: str,
    difficulty: str,
    streak: int,
) -> None:
    """Start a session and place cards accurately until the desired streak is reached."""
    resp = api_driver.start_session(
        player_name=player_name,
        difficulty=difficulty,
        seed=42,
    )
    assert resp.status_code == 201
    context.session = resp.json()

    for _ in range(streak):
        drawn = context.session["current_event"]
        assert drawn is not None
        target_year = int(context.events_by_id[drawn["id"]]["year"])
        valid_pos = api_driver.find_valid_position_index(
            context.session["timeline"],
            target_year,
        )
        place_resp = api_driver.place_event(
            session_id=context.session["id"],
            event_id=drawn["id"],
            position_index=valid_pos,
        )
        assert place_resp.status_code == 200
        outcome = place_resp.json()
        context.last_attempt = outcome["attempt"]
        context.session = outcome["session"]

    assert context.session["streak"] == streak


@given(
    parsers.parse(
        'player "{player_name}" has an active "{difficulty}" timeline session with {lives:d} lives remaining'
    )
)
def given_active_session_with_lives(
    api_driver: ChronoQuestApiDriver,
    context: ScenarioContext,
    player_name: str,
    difficulty: str,
    lives: int,
) -> None:
    """Start a session on the specified difficulty and verify initial lives remaining."""
    resp = api_driver.start_session(
        player_name=player_name,
        difficulty=difficulty,
        seed=42,
    )
    assert resp.status_code == 201
    context.session = resp.json()
    assert context.session["lives_remaining"] == lives


@then(parsers.parse('a new timeline session is created with status "{status}"'))
def then_session_created_with_status(
    context: ScenarioContext,
    status: str,
) -> None:
    """Verify the created session has the expected status."""
    assert context.session["id"]
    assert context.session["status"] == status


@then(
    parsers.parse(
        "the session starts with score {score:d}, streak {streak:d}, and {lives:d} lives remaining"
    )
)
def then_session_initial_counters(
    context: ScenarioContext,
    score: int,
    streak: int,
    lives: int,
) -> None:
    """Verify initial score, streak, and lives remaining on the session."""
    assert context.session["score"] == score
    assert context.session["streak"] == streak
    assert context.session["lives_remaining"] == lives


@then(
    "the timeline board contains 1 initial anchor card with its year and significance revealed"
)
def then_timeline_contains_one_revealed_anchor(context: ScenarioContext) -> None:
    """Verify the timeline starts with 1 anchor card containing year and significance."""
    timeline = context.session["timeline"]
    assert len(timeline) == 1
    anchor = timeline[0]
    assert isinstance(anchor["year"], int)
    assert anchor["year_label"]
    assert anchor["significance"]


@then("the session presents 1 drawn historical event card to place with its year hidden")
def then_session_presents_drawn_card_with_hidden_year(
    context: ScenarioContext,
) -> None:
    """Verify current_event is present and does not leak year or significance."""
    drawn = context.session["current_event"]
    assert drawn is not None
    assert drawn["id"]
    assert drawn["title"]
    assert drawn["summary"]
    assert "year" not in drawn
    assert "year_label" not in drawn
    assert "significance" not in drawn


@when("the player places the drawn historical event in its chronologically valid position_index")
def when_player_places_event_correctly(
    api_driver: ChronoQuestApiDriver,
    context: ScenarioContext,
) -> None:
    """Submit a chronologically valid placement for the active drawn card."""
    drawn = context.session["current_event"]
    assert drawn is not None
    target_year = int(context.events_by_id[drawn["id"]]["year"])
    valid_pos = api_driver.find_valid_position_index(
        context.session["timeline"],
        target_year,
    )
    context.lives_before_placement = int(context.session["lives_remaining"])
    resp = api_driver.place_event(
        session_id=context.session["id"],
        event_id=drawn["id"],
        position_index=valid_pos,
    )
    assert resp.status_code == 200
    outcome = resp.json()
    context.last_attempt = outcome["attempt"]
    context.session = outcome["session"]


@then("the placement attempt is recorded as correct")
def then_attempt_recorded_as_correct(context: ScenarioContext) -> None:
    """Verify the placement attempt is marked correct."""
    assert context.last_attempt["is_correct"] is True
    assert (
        context.last_attempt["submitted_position"]
        == context.last_attempt["correct_position"]
    )


@then(
    parsers.parse(
        "the session score increases by {points:d} points and the current streak becomes {streak:d}"
    )
)
def then_score_increases_and_streak_becomes(
    context: ScenarioContext,
    points: int,
    streak: int,
) -> None:
    """Verify points awarded, updated session score, and streak."""
    assert context.last_attempt["points_awarded"] == points
    assert context.session["score"] == points
    assert context.session["streak"] == streak


@then("the placed event reveals its historical year and significance on the timeline")
def then_placed_event_reveals_year_and_significance(context: ScenarioContext) -> None:
    """Verify the placed event is now revealed in the attempt and on the timeline."""
    placed = context.last_attempt["placed_event"]
    assert isinstance(placed["year"], int)
    assert placed["year_label"]
    assert placed["significance"]
    timeline_ids = [card["id"] for card in context.session["timeline"]]
    assert placed["id"] in timeline_ids


@then(
    parsers.parse(
        "the timeline board contains {count:d} cards sorted in non-decreasing chronological order"
    )
)
def then_timeline_contains_sorted_cards(
    context: ScenarioContext,
    count: int,
) -> None:
    """Verify timeline length and non-decreasing chronological order."""
    timeline = context.session["timeline"]
    assert len(timeline) == count
    years = [int(card["year"]) for card in timeline]
    assert years == sorted(years)


@when("the player places the drawn historical event in an incorrect chronological position_index")
def when_player_places_event_incorrectly(
    api_driver: ChronoQuestApiDriver,
    context: ScenarioContext,
) -> None:
    """Submit a chronologically invalid placement for the active drawn card."""
    drawn = context.session["current_event"]
    assert drawn is not None
    target_year = int(context.events_by_id[drawn["id"]]["year"])
    invalid_pos = api_driver.find_invalid_position_index(
        context.session["timeline"],
        target_year,
    )
    context.lives_before_placement = int(context.session["lives_remaining"])
    resp = api_driver.place_event(
        session_id=context.session["id"],
        event_id=drawn["id"],
        position_index=invalid_pos,
    )
    assert resp.status_code == 200
    outcome = resp.json()
    context.last_attempt = outcome["attempt"]
    context.session = outcome["session"]


@then("the placement attempt is recorded as incorrect with 0 points awarded")
def then_attempt_recorded_as_incorrect(context: ScenarioContext) -> None:
    """Verify the placement attempt is marked incorrect and awards 0 points."""
    assert context.last_attempt["is_correct"] is False
    assert context.last_attempt["points_awarded"] == 0


@then("the session lives_remaining decrements by 1 and the current streak resets to 0")
def then_lives_decrement_and_streak_resets(context: ScenarioContext) -> None:
    """Verify lives_remaining decremented by 1 and streak reset to 0."""
    assert context.session["lives_remaining"] == context.lives_before_placement - 1
    assert context.session["streak"] == 0


@then(
    "the misplaced event is inserted into its true chronological slot on the timeline with its year and significance revealed"
)
def then_misplaced_event_inserted_into_true_slot(context: ScenarioContext) -> None:
    """Verify the misplaced event is placed at correct_position and the timeline remains sorted."""
    correct_pos = int(context.last_attempt["correct_position"])
    placed_event = context.last_attempt["placed_event"]
    timeline = context.session["timeline"]
    assert timeline[correct_pos]["id"] == placed_event["id"]
    assert isinstance(timeline[correct_pos]["year"], int)
    assert timeline[correct_pos]["significance"]
    years = [int(card["year"]) for card in timeline]
    assert years == sorted(years)


@when("the player places all remaining drawn cards in their correct chronological slots")
def when_player_places_all_remaining_cards_correctly(
    api_driver: ChronoQuestApiDriver,
    context: ScenarioContext,
) -> None:
    """Place every remaining card in the session deck into its valid chronological slot."""
    while context.session["status"] == "in_progress":
        drawn = context.session["current_event"]
        assert drawn is not None
        target_year = int(context.events_by_id[drawn["id"]]["year"])
        valid_pos = api_driver.find_valid_position_index(
            context.session["timeline"],
            target_year,
        )
        resp = api_driver.place_event(
            session_id=context.session["id"],
            event_id=drawn["id"],
            position_index=valid_pos,
        )
        assert resp.status_code == 200
        outcome = resp.json()
        context.last_attempt = outcome["attempt"]
        context.session = outcome["session"]


@then(
    parsers.parse(
        'the timeline session transitions to status "{status}" with no remaining card to place'
    )
)
def then_session_transitions_with_no_remaining_card(
    context: ScenarioContext,
    status: str,
) -> None:
    """Verify session status is completed and current_event is None."""
    assert context.session["status"] == status
    assert context.session["current_event"] is None
    assert context.session["cards_remaining"] == 0


@then(
    parsers.parse(
        'the Hall of Records leaderboard includes player "{player_name}" ranked by score'
    )
)
def then_leaderboard_includes_player(
    api_driver: ChronoQuestApiDriver,
    context: ScenarioContext,
    player_name: str,
) -> None:
    """Verify the finished session appears on the Hall of Records leaderboard."""
    resp = api_driver.get_leaderboard()
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) >= 1
    matching = [entry for entry in entries if entry["player_name"] == player_name]
    assert len(matching) == 1
    assert matching[0]["score"] == context.session["score"]
    assert matching[0]["rank"] == 1


@when(
    parsers.parse(
        "the player misplaces {count:d} consecutive drawn historical events"
    )
)
def when_player_misplaces_consecutive_events(
    api_driver: ChronoQuestApiDriver,
    context: ScenarioContext,
    count: int,
) -> None:
    """Misplace the specified number of consecutive drawn events."""
    for _ in range(count):
        drawn = context.session["current_event"]
        assert drawn is not None
        target_year = int(context.events_by_id[drawn["id"]]["year"])
        invalid_pos = api_driver.find_invalid_position_index(
            context.session["timeline"],
            target_year,
        )
        resp = api_driver.place_event(
            session_id=context.session["id"],
            event_id=drawn["id"],
            position_index=invalid_pos,
        )
        assert resp.status_code == 200
        outcome = resp.json()
        context.last_attempt = outcome["attempt"]
        context.session = outcome["session"]


@then(
    parsers.parse(
        'the timeline session transitions to status "{status}" with {lives:d} lives remaining'
    )
)
def then_session_transitions_with_lives_remaining(
    context: ScenarioContext,
    status: str,
    lives: int,
) -> None:
    """Verify session status and lives remaining after losing all lives."""
    assert context.session["status"] == status
    assert context.session["lives_remaining"] == lives
    assert context.session["current_event"] is None
