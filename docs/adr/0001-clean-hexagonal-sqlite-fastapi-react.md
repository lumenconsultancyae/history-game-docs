# ADR 0001: Clean/Hexagonal Architecture with FastAPI, SQLAlchemy 2.0 + SQLite WAL, and React 19 + Vite

- **Status**: Accepted
- **Date**: 2026-11-15

---

## Context

**ChronoQuest** requires a responsive, self-contained World History Timeline Placement Challenge and Era Atlas that enforces rich domain invariants (BCE/CE chronological comparison, streak multipliers, life decrements, true-slot educational correction on misplacement, and deterministic deck sampling) while remaining simple to deploy in single-container local or cloud environments without external API keys or multi-node database clusters.

---

## Decision Drivers

1. **Pure Domain Testability**: Chronological placement invariants (`HistoricalYear`, `TimelineSession.place_event`, `PlacementAttempt`) must be unit-testable in milliseconds with zero database or HTTP framework coupling.
2. **Zero-Config Local & Container Persistence**: The service must boot cleanly from an empty volume on Day-0, apply schema migrations, and idempotently seed the 24-event World History catalog while supporting concurrent read/write sessions.
3. **Strict API Contract & Error Ergonomics**: Clients and automated BDD acceptance suites require OpenAPI 3.1 schema validation and RFC 9457 `application/problem+json` error envelopes.
4. **Accessible, Low-Friction UI**: Players must be able to place drawn historical cards into chronological slots using either mouse clicks or keyboard navigation (`<button>` slot targets) without brittle drag-and-drop timing issues.

---

## Considered Options

### Option 1: Clean/Hexagonal Python 3.12 + FastAPI + SQLAlchemy 2.0 Async (SQLite WAL) + React 19 SPA (Recommended)
- Strict 7-package backend layout (`domain`, `application`, `infrastructure`, `api`, `config`, `utils`, `injection`) with an embedded React 19 + TypeScript + Vite frontend served by FastAPI in production builds.

### Option 2: Monolithic Django / Server-Rendered Templates
- Couples ORM models directly to domain logic (`Active Record` pattern), violating pure domain isolation and making interactive timeline card transitions less fluid.

### Option 3: Client-Only Browser Game with LocalStorage
- Cannot provide a shared multi-player Hall of Records leaderboard, server-authoritative chronological validation (preventing client-side year inspection before placement), or backend API BDD verification.

---

## Decision Outcome

Chosen option: **Option 1 — Clean/Hexagonal Python 3.12 + FastAPI + SQLAlchemy 2.0 Async (SQLite WAL) + React 19 SPA**.

1. **`domain/` Isolation**: `HistoricalYear`, `HistoricalEra`, `Difficulty`, `HistoricalEvent`, `PlacementAttempt`, and `TimelineSession` live in `src/history_game/domain/` with zero outward imports.
2. **Server-Authoritative Unplaced Card Redaction**: `GET /api/v1/sessions/{id}` and `POST /api/v1/sessions` serialize `current_event` via `UnplacedEventCardResponse` (omitting `year` and `significance` until `POST /api/v1/sessions/{id}/placements` evaluates the turn).
3. **SQLite WAL + Alembic**: `infrastructure/persistence/database.py` enables `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON` on every connection, paired with Alembic migrations and idempotent startup seeding of the 24-event catalog.
4. **Explicit Slot Selection UI**: The React 19 frontend renders explicit **"Place Here (Slot #N)"** insertion buttons before, between, and after timeline cards alongside Era Atlas and Hall of Records views.

---

## Consequences

### Positive
- Complete separation between domain invariants (`domain/`) and persistence/HTTP adapters (`infrastructure/`, `api/`), verified automatically by `check_architecture_gates.sh`.
- Misplaced events immediately teach the player by revealing the card's true chronological slot, year (`BCE`/`CE`), and historical significance.
- Fast startup and zero external service dependencies.

### Negative / Trade-offs
- Storing `timeline_event_ids_json` and `remaining_deck_ids_json` as JSON-encoded lists on `timeline_sessions` trades normalized join-table complexity on transient deck queues for single-row aggregate read/write atomicity, while keeping completed turn history normalized in `placement_attempts`.
