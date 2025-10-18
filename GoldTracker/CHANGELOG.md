# GoldTracker Changelog

All notable changes to this project will be documented in this file.
This project adheres to Semantic Versioning. Alpha/Beta versions use 0.x.x; 1.x.x indicates a stable release.

## [Unreleased]
- Planned: In-game CRUD for sessions and zones (create/update/delete via gump)
- Planned: Merge sessions when zone and day match (consolidate same-day runs)

## [0.10.0-beta] - 2025-10-17
### Added
- Finish → Summary flow with "Save" and "Discard" actions.
- End time fixed at Finish; Summary shows exact timestamp; Save keeps and Discard removes the CSV row.
- Pause/Resume toggle button with synchronized blinking timer while paused.
- Pause-aware timing in CSV: new columns `session_duration` and `paused_time` (HH:MM:SS).
- Themed UI with shared `ui_theme` (button hues: Primary/Success/Danger/Warning; improved backgrounds and contrast).
- Session gump now closes when Finish is pressed; mini gump respects finalization state.

### Changed
- CSV schema updated: replaced `duration_minutes` with `session_duration` and added `paused_time`.
- Documentation updated to reflect new flow, colors, and timing model.

## [0.9.0-beta] - 2025-10-16
### Changed
- Adopted proper callback lifecycle: unregister before registering and in cleanup to prevent "Too many callbacks registered!" errors.
- Significant log volume reduction via throttling and removal of noisy debug paths (about ~70% reduction in long sessions).

### Fixed
- Eliminated callback accumulation across runs which caused start failures.

## [0.8.0-alpha] - 2025-10-15
### Fixed
- Deaths counted twice: `OnPlayerDeath` now ignores resurrection events (checks `API.Player.Hits > 0`).

## [0.7.0-alpha] - 2025-10-14
### Added
- Zone selection with fuzzy filter, session CSV tracking, dynamic gump UI, auto-save.

---

### Notes
- DEBUG logging follows JSON Lines format and is throttled to avoid spam.
- Gump is created once and updated dynamically; control properties updated without recreating the gump.