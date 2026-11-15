# Product Requirements Document (PRD): ChronoQuest World History Timeline Challenge

## 1. Product Vision & Overview

**ChronoQuest** is an interactive educational world history application combining a curated **World History Era Atlas** (`HistoricalCatalog`) with an interactive **Timeline Placement Challenge** (`TimelineGameplay`). Rather than testing rote date memorization in isolation, ChronoQuest challenges players to reason about cause, effect, and historical era context to place milestones into an expanding chronological timeline.

---

## 2. Target Personas

| Persona | Role & Goals | Key Pain Points Addressed |
| :--- | :--- | :--- |
| **Curious Explorer (Student / Lifelong Learner)** | Wants an engaging, visual way to connect events across civilizations (Mesopotamia, Classical Mediterranean, Silk Roads, Scientific Revolution, Modern Age). | Traditional textbooks present regions in isolated chapters, making cross-civilization chronological relationships hard to visualize. |
| **Educator / Seminar Facilitator** | Needs a zero-configuration classroom activity where learners can filter by a specific historical era (`ancient`, `classical`, `medieval`, `early_modern`, `industrial`, `modern`) or test comprehensive world history synthesis. | Quiz tools rarely teach *why* an event occurred when a player misses a question; ChronoQuest immediately places misplaced cards into their true chronological slot and reveals historical significance. |
| **Competitive Chronomaster (Trivia & Strategy Enthusiast)** | Seeks high-stakes streak multipliers, tight life constraints (`2` lives on `chronomaster`), and a persistent **Hall of Records** leaderboard. | Flat scoring systems fail to reward sustained accuracy across long 12-card multi-era chains. |

---

## 3. Core User Stories & Acceptance Criteria

### US-01: Browse the World History Era Atlas (`HistoricalCatalog`)
- **As a** learner, **I want to** browse the 6 canonical eras of world history and filter historical events by era, **so that** I can study pivotal milestones, BCE/CE dates, regions, and historical significance before or after playing.
- **Acceptance Criteria**:
  1. `GET /api/v1/eras` returns all 6 eras (`ancient`, `classical`, `medieval`, `early_modern`, `industrial`, `modern`) in chronological order with start/end year labels and event counts.
  2. `GET /api/v1/events` returns the curated 24-event catalog sorted chronologically (`year ASC`), supporting optional `?era=<era>` filtering.

### US-02: Start a Customizable Timeline Placement Session (`StartTimelineSession`)
- **As a** player, **I want to** start a new timeline session with my chosen player name, difficulty tier (`explorer`, `historian`, `chronomaster`), and optional era filter, **so that** the challenge matches my skill level and study focus.
- **Acceptance Criteria**:
  1. Starting a session initializes the board with **1 face-up Anchor Card** on the timeline (showing its year and significance) and **1 Drawn Card** awaiting placement (showing title, era, region, and clue summary while hiding its exact year and significance).
  2. Session parameters scale by difficulty:

| Difficulty (`Difficulty`) | Cards to Place (`remaining + current`) | Total Deck Size (incl. Anchor) | Starting Lives (`lives_remaining`) | Base Points | Streak Bonus (per consecutive hit) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `explorer` | `5` | `6` | `3` | `100` | `+25` |
| `historian` | `8` | `9` | `3` | `150` | `+50` |
| `chronomaster` | `12` | `13` | `2` | `200` | `+75` |

  *(When a player filters by a single era containing 4 catalog events, the total deck size caps at the 4 available events: 1 Anchor Card + 3 Cards to Place.)*

### US-03: Place Drawn Historical Events & Learn from Immediate Feedback (`PlaceHistoricalEvent`)
- **As a** player, **I want to** choose the chronological insertion slot (`position_index`) for my drawn card relative to the cards already on the timeline, **so that** I earn points for accurate chronological reasoning and immediately learn the true date and historical significance after every turn.
- **Acceptance Criteria**:
  1. Selecting a valid chronological slot (`left_neighbor.year <= event.year <= right_neighbor.year`) records `is_correct = true`, increments `streak`, updates `max_streak`, awards `base_points + (streak - 1) * streak_bonus`, inserts the card at `position_index`, and reveals its `year`, `year_label`, and `significance`.
  2. Selecting an invalid slot records `is_correct = false`, awards `0` points, resets `streak` to `0`, decrements `lives_remaining` by `1`, and inserts the card into its true `correct_position` on the timeline with its `year`, `year_label`, and `significance` revealed.

### US-04: Complete Sessions & Compete on the Hall of Records Leaderboard
- **As a** player, **I want to** see my final score, accuracy, and best streak when I place all cards in the deck (`completed`) or run out of lives (`game_over`), and view top scores on the Hall of Records leaderboard.
- **Acceptance Criteria**:
  1. When `remaining_deck` becomes empty with `lives_remaining > 0`, session status becomes `completed`.
  2. When `lives_remaining` reaches `0`, session status becomes `game_over` and `current_event` is cleared (`null`).
  3. `GET /api/v1/leaderboard` returns finished sessions (`completed` and `game_over`) ordered by `score DESC, max_streak DESC, completed_at ASC`, with optional `?difficulty=` filtering.

---

## 4. Day-0 / Cold-Start / Zero-Data Operational Use Cases

Immediately after a fresh deployment when the SQLite volume is empty (`0` tables, `0` events, `0` sessions, `0` leaderboard rows), ChronoQuest executes a deterministic, zero-touch cold-start sequence:

### UC-DAY0-01: Automated Schema Genesis & Idempotent Catalog Bootstrap
- **Given** a fresh container or process boot against an uninitialized SQLite database file (`0` existing tables or `0` rows in `historical_events`),
- **When** the FastAPI `lifespan` startup hook runs,
- **Then** the persistence bootstrap configures SQLite `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON`, ensures the schema (`historical_events`, `timeline_sessions`, `placement_attempts`) exists, checks `SELECT COUNT(*) FROM historical_events`, and—when the count is `0` and `HISTORY_GAME_SEED_ON_STARTUP` is enabled—atomically seeds the canonical **24 World History events** (`4` events across each of the `6` eras). Subsequent restarts detect `count > 0` and perform zero duplicate inserts.

### UC-DAY0-02: First-Run Empty-Session State & Instant Onboarding
- **Given** a newly deployed instance where `0` `TimelineSession` records exist in `timeline_sessions`,
- **When** the first player opens the ChronoQuest web interface,
- **Then** the application immediately loads the 6-era catalog, pre-fills sensible session defaults (`Explorer` difficulty, `All Eras`), and provides a single-click **Start Timeline Challenge** onboarding card explaining how to place the Drawn Card before, between, or after existing timeline cards.

### UC-DAY0-03: Actionable Empty State for the Hall of Records Leaderboard
- **Given** `0` completed or game-over sessions exist in `timeline_sessions`,
- **When** a user views the **Hall of Records** leaderboard (`GET /api/v1/leaderboard` returning `[]`),
- **Then** the UI renders a dedicated empty-state panel (*"No chronicles recorded yet — complete your first Timeline Challenge to claim the top spot in the Hall of Records!"*) with a direct **Launch First Challenge** call-to-action button that focuses the session setup form.

---

## 5. Non-Functional Requirements

1. **Zero External API Dependencies**: All 24 historical events, era metadata, and gameplay rules run 100% locally inside the Python/SQLite backend without external LLM or third-party network calls.
2. **Strict Layer & Error Hygiene**: Every domain invariant failure translates into an RFC 9457 `application/problem+json` response (`type`, `title`, `status`, `detail`, `instance`).
3. **Accessibility & Keyboard Playability**: Every insertion slot (`position_index`) and navigation tab in the React UI is keyboard-focusable (`<button>`) with explicit `data-testid` and ARIA labels so players can play without drag-and-drop dexterity barriers.
