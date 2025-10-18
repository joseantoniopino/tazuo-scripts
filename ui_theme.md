# UI Theme (Optional) for LegionScripts

A lightweight, reusable color and typography helper for TazUO gumps. It centralizes a safe palette and UO hue values so your scripts look consistent without duplicating constants.

This module is optional. Scripts must continue to work without it.

---

## What it provides

- Palette (hex colors) for ColorBox backgrounds and accents
- Hues (UO integer indices) for labels and buttons
- Helper functions to pick header/background/separator colors
- Optional JSON overrides via `ui_theme.json` (not auto-created)

File: `public/ui_theme.py`

---

## When to use it

- You want consistent button colors (Primary/Success/Danger/Warning)
- You want a shared header accent (mint/cyan) across gumps
- You want to tweak colors without editing each script

If you prefer full control, you can ignore this module; your scripts won’t depend on it.

---

## Import patterns

Recommended pattern for optional use (with fallback):

```python
# In your script/gump manager
THEME = None
try:
    # Make sure this points to the folder containing ui_theme.py
    import os, sys
    parent_dir = os.path.dirname(os.path.dirname(__file__))  # example
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    import ui_theme as THEME
except Exception:
    THEME = None  # Fallback to hardcoded hues/colors

if THEME:
    HUE_PRIMARY = THEME.HUES.PRIMARY
    HUE_SUCCESS = THEME.HUES.SUCCESS
    HUE_DANGER  = THEME.HUES.DANGER
    HUE_WARNING = THEME.HUES.WARNING
    HUE_MUTED   = THEME.HUES.MUTED
    TITLE_HUE   = THEME.HUES.TITLE
    COLOR_BG        = THEME.background_color()
    COLOR_HEADER    = THEME.header_color()
    COLOR_SEPARATOR = THEME.separator_color()
else:
    # Safe defaults if theme is missing
    HUE_PRIMARY = 0x0058
    HUE_SUCCESS = 0x0044
    HUE_DANGER  = 0x0021
    HUE_WARNING = 0x0035
    HUE_MUTED   = 0x003F
    TITLE_HUE   = 0x0481
    COLOR_BG        = "#0f172a"
    COLOR_HEADER    = "#1e40af"
    COLOR_SEPARATOR = "#374151"
```

This is the exact approach used in GoldTracker’s `_gump_manager.py`.

---

## API overview

### Dataclasses

- Palette (hex strings for ColorBox backgrounds):
  - BACKGROUND, SURFACE, HEADER_ACCENT, HEADER_ACCENT_ALT, SEPARATOR
- Hues (int hue IDs for labels/buttons):
  - SUCCESS, DANGER, WARNING, PRIMARY, CYAN, MUTED, TITLE

Access them as singletons:

```python
from public import ui_theme as THEME  # or via sys.path trick above
bg = THEME.PALETTE.BACKGROUND
ok = THEME.HUES.SUCCESS
```

### Helper functions

- `header_color()`
- `alt_header_color()`
- `background_color()`
- `surface_color()`
- `separator_color()`

All return hex strings suitable for `CreateGumpColorBox`.

---

## Configuration (optional)

You can override palette/hues by creating `public/ui_theme.json` yourself. It is not auto-created. If the file is absent, built-in defaults are used.

Example:

```json
{
  "palette": {
    "BACKGROUND": "#0b1324",
    "SURFACE": "#0f172a",
    "HEADER_ACCENT": "#0ea5e9",        
    "HEADER_ACCENT_ALT": "#06b6d4",
    "SEPARATOR": "#334155"
  },
  "hues": {
    "SUCCESS": 68,
    "DANGER": 33,
    "WARNING": 53,
    "PRIMARY": 88,
    "CYAN": 89,
    "MUTED": 63,
    "TITLE": 1153
  },
  "header_accent_preference": "cyan"  
}
```

- If a key is missing, defaults are used for that key.
- `header_accent_preference`: "mint" (default) or "cyan".

---

## Guarantees and behavior

- No hard dependency: if `ui_theme.py` cannot be imported, scripts must fall back to safe defaults.
- No side effects: importing `ui_theme` does not modify your scripts or gumps.
- Config is opt-in: `ui_theme.json` is read only if present; otherwise defaults are used.

---

## Compatibility notes

- Works on modern TazUO with Python API; this module itself has no TazUO imports.
- Color HUE values may vary slightly by client; pick the ones you prefer via overrides if needed.

---

## Changelog

- 2025-10-18: Initial documentation and clarification that `ui_theme.json` is optional and not auto-created.
