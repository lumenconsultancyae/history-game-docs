@timeline_challenge
Feature: World History Timeline Placement Challenge
  As a history enthusiast and ChronoQuest player
  I want to browse historical eras, start timeline placement challenges, place drawn events into chronological slots, learn from revealed historical significance, and compete on the Hall of Records leaderboard
  So that I can master the chronological sequence of world history across eras

  Background:
    Given the canonical World History catalog of 24 events across 6 historical eras is available

  @catalog @api @ui
  Scenario: Listing historical eras and browsing historical events by era
    When the player requests the catalog of historical eras
    Then 6 historical eras are returned in chronological order:
      | era          | label              |
      | ancient      | Ancient World      |
      | classical    | Classical Era      |
      | medieval     | Medieval Era       |
      | early_modern | Early Modern Era   |
      | industrial   | Industrial Age     |
      | modern       | Modern Era         |
    When the player browses historical events filtered by era "ancient"
    Then every returned historical event belongs to era "ancient"
    And the events are ordered chronologically with formatted BCE or CE year labels

  @session @api @ui
  Scenario: Starting a new timeline game session with an initial anchor card and a card to place
    When player "Ada Lovelace" starts a new timeline session on difficulty "explorer"
    Then a new timeline session is created with status "in_progress"
    And the session starts with score 0, streak 0, and 3 lives remaining
    And the timeline board contains 1 initial anchor card with its year and significance revealed
    And the session presents 1 drawn historical event card to place with its year hidden

  @placement @correct @api @ui
  Scenario: Placing a drawn historical event in the correct chronological slot
    Given player "Ada Lovelace" has an active "explorer" timeline session
    When the player places the drawn historical event in its chronologically valid position_index
    Then the placement attempt is recorded as correct
    And the session score increases by 100 points and the current streak becomes 1
    And the placed event reveals its historical year and significance on the timeline
    And the timeline board contains 2 cards sorted in non-decreasing chronological order

  @placement @misplaced @api @ui
  Scenario: Misplacing a historical event decrements lives and inserts the card into its true chronological slot
    Given player "Ada Lovelace" has an active "explorer" timeline session with a current streak of 1
    When the player places the drawn historical event in an incorrect chronological position_index
    Then the placement attempt is recorded as incorrect with 0 points awarded
    And the session lives_remaining decrements by 1 and the current streak resets to 0
    And the misplaced event is inserted into its true chronological slot on the timeline with its year and significance revealed

  @completion @leaderboard @api @ui
  Scenario: Completing a timeline session when all cards are placed or lives reach zero and viewing the leaderboard
    Given player "Herodotus" has an active "explorer" timeline session
    When the player places all remaining drawn cards in their correct chronological slots
    Then the timeline session transitions to status "completed" with no remaining card to place
    And the Hall of Records leaderboard includes player "Herodotus" ranked by score
    Given player "Ibn Battuta" has an active "chronomaster" timeline session with 2 lives remaining
    When the player misplaces 2 consecutive drawn historical events
    Then the timeline session transitions to status "game_over" with 0 lives remaining
