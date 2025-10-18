# UI Theme configuration for LegionScripts
# Agnostic, reusable palette and sizing for TazUO gumps
# This file is intentionally lightweight and has no TazUO dependencies.
# Import and use constants/functions from any script.

from dataclasses import dataclass
import os
import json


@dataclass(frozen=True)
class Palette:
    # Hex colors for ColorBox backgrounds and accents
    BACKGROUND: str = "#0f172a"        # slate-900
    SURFACE: str = "#111827"           # gray-900 (panels)
    HEADER_ACCENT: str = "#1e40af"     # blue-800 (primary header - darker)
    HEADER_ACCENT_ALT: str = "#06b6d4" # cyan-400 (alternative/accent text)
    SEPARATOR: str = "#374151"         # gray-700


@dataclass(frozen=True)
class Hues:
    # UO hue indices for text/controls (fallback-safe)
    SUCCESS: int = 0x0044   # green
    DANGER: int = 0x0021    # red
    WARNING: int = 0x0035   # yellow
    PRIMARY: int = 0x0058   # blue (primary actions like Finish)
    CYAN: int = 0x0059      # cyan-like text hue (approximation)
    MUTED: int = 0x003F     # light gray/white-ish
    TITLE: int = 0x0481     # blue-ish (may vary per client)


# Defaults (will be overridden by config if present)
_default_palette = Palette()
_default_hues = Hues()

# Global singletons (initialized below)
PALETTE = _default_palette
HUES = _default_hues

# Optional configuration file (manual; create to override defaults)
_config_dir = os.path.dirname(os.path.abspath(__file__))
_config_path = os.path.join(_config_dir, "ui_theme.json")


def _serialize_defaults():
    return {
        "palette": {
            "BACKGROUND": _default_palette.BACKGROUND,
            "SURFACE": _default_palette.SURFACE,
            "HEADER_ACCENT": _default_palette.HEADER_ACCENT,
            "HEADER_ACCENT_ALT": _default_palette.HEADER_ACCENT_ALT,
            "SEPARATOR": _default_palette.SEPARATOR
        },
        "hues": {
            "SUCCESS": _default_hues.SUCCESS,
            "DANGER": _default_hues.DANGER,
            "WARNING": _default_hues.WARNING,
            "PRIMARY": _default_hues.PRIMARY,
            "CYAN": getattr(_default_hues, 'CYAN', 0x0059),
            "MUTED": _default_hues.MUTED,
            "TITLE": _default_hues.TITLE
        },
        # Preference to pick header accent variant: "mint" or "cyan"
        "header_accent_preference": "mint"
    }


def _load_or_create_theme():
    global PALETTE, HUES
    try:
        if not os.path.exists(_config_path):
            # No global file by default: keep in-code defaults and reflect accent pref
            PALETTE = _default_palette
            HUES = _default_hues
            globals()["_accent_pref"] = "mint"  # default accent
            return
        # Load and apply overrides
        with open(_config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        pal = data.get("palette", {}) or {}
        hues = data.get("hues", {}) or {}
        # Build new dataclass instances with overrides when provided
        PALETTE = Palette(
            BACKGROUND=pal.get("BACKGROUND", _default_palette.BACKGROUND),
            SURFACE=pal.get("SURFACE", _default_palette.SURFACE),
            HEADER_ACCENT=pal.get("HEADER_ACCENT", _default_palette.HEADER_ACCENT),
            HEADER_ACCENT_ALT=pal.get("HEADER_ACCENT_ALT", _default_palette.HEADER_ACCENT_ALT),
            SEPARATOR=pal.get("SEPARATOR", _default_palette.SEPARATOR),
        )
        HUES = Hues(
            SUCCESS=int(hues.get("SUCCESS", _default_hues.SUCCESS)),
            DANGER=int(hues.get("DANGER", _default_hues.DANGER)),
            WARNING=int(hues.get("WARNING", _default_hues.WARNING)),
            PRIMARY=int(hues.get("PRIMARY", _default_hues.PRIMARY)),
            CYAN=int(hues.get("CYAN", getattr(_default_hues, 'CYAN', 0x005A))),
            MUTED=int(hues.get("MUTED", _default_hues.MUTED)),
            TITLE=int(hues.get("TITLE", _default_hues.TITLE)),
        )
        # Accent preference
        pref = str(data.get("header_accent_preference", "mint") or "mint").lower()
        globals()["_accent_pref"] = "cyan" if pref in ("cyan", "alt") else "mint"
    except Exception:
        # On any error, fall back to safe defaults
        PALETTE = _default_palette
        HUES = _default_hues
        globals()["_accent_pref"] = "mint"


# Initialize theme on import
_accent_pref = "mint"
_load_or_create_theme()


def header_color() -> str:
    """Return preferred header accent color (blue by default or as configured)."""
    return PALETTE.HEADER_ACCENT if _accent_pref != "cyan" else PALETTE.HEADER_ACCENT_ALT


def alt_header_color() -> str:
    return PALETTE.HEADER_ACCENT_ALT


def background_color() -> str:
    return PALETTE.BACKGROUND


def surface_color() -> str:
    return PALETTE.SURFACE


def separator_color() -> str:
    return PALETTE.SEPARATOR
