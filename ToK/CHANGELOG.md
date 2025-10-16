# Tomb of Kings (ToK) Changelog

All notable changes to this project will be documented in this file.
This project adheres to Semantic Versioning.

## [Unreleased]
- Planned: Minor UX polish and optional gump helper

## [1.0.0] - 2025-10-16
### Added
- Initial stable release.
- Lever detection (two graphics supported), highlights usable levers in green.
- Auto-use levers when within distance 1.
- Flame phase: detects and auto-uses Order/Chaos flames when levers are done.
- Scan-once-and-store pattern to avoid visual glitches after state changes.
- Minimal on-screen SysMsg; structured DEBUG logging when enabled.
