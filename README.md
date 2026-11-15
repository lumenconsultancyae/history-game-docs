# ChronoQuest Documentation & Acceptance Suite (`history-game-docs`)

Companion documentation, local `docker-compose.yml` environment, and Behavior-Driven Development (BDD) end-to-end acceptance repository for **ChronoQuest** ([`history-game`](https://github.com/lumenconsultancyae/history-game)).

## Documentation Index

1. **Domain-Driven Design (DDD) & Event Storming**: [`docs/ddd/domain-model-and-event-storming.md`](./docs/ddd/domain-model-and-event-storming.md) — Bounded Contexts (`HistoricalCatalog`, `TimelineGameplay`), Ubiquitous Language glossary, Aggregate Roots (`HistoricalEvent`, `TimelineSession`), Value Objects (`HistoricalYear`, `HistoricalEra`, `Difficulty`), Commands, and Domain Events.
2. **BDD Acceptance Specifications**: [`features/timeline_challenge.feature`](./features/timeline_challenge.feature) — Declarative Gherkin scenarios for era browsing, session initialization, correct and misplaced chronological placements, session completion, and leaderboard rankings.
3. **Product Requirements Document (PRD)**: [`docs/prd/history-game-prd.md`](./docs/prd/history-game-prd.md) — Target personas, core user stories, difficulty/scoring matrix, and Day-0 / Cold-Start / Zero-Data operational use cases.
4. **Software Design Document (SDD)**: [`docs/sdd/history-game-sdd.md`](./docs/sdd/history-game-sdd.md) — Clean/Hexagonal layer boundaries, OpenAPI 3.1 REST endpoints, RFC 9457 Problem Details error contract, and SQLite WAL persistence schema.
5. **Architecture Decision Records (ADR)**: [`docs/adr/0001-clean-hexagonal-sqlite-fastapi-react.md`](./docs/adr/0001-clean-hexagonal-sqlite-fastapi-react.md) — MADR record for the Clean/Hexagonal FastAPI + SQLAlchemy 2.0 + SQLite WAL + React 19 architecture.
6. **Player User Guide**: [`docs/user-guide/getting-started.md`](./docs/user-guide/getting-started.md) — End-user guide to the Timeline Challenge, Era Atlas, and Hall of Records.
7. **Release Notes**: [`docs/release-notes.md`](./docs/release-notes.md) — Customer-facing v0.1.0 release notes.

## Local Container Stack (`docker-compose.yml`)

```bash
docker compose up -d --build
```
