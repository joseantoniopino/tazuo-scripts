# Shadowguard Script - Changelog

## Version 0.4.1 (2025-10-11) - Alpha

### 🎯 Project Status
- **Phase**: Alpha - Lobby + Bar + Gumps UI (Fixed)
- **Functionality**: ~45% (2 of 7 rooms + UI system)
- **Stability**: ✅ Bar room functional, Gumps fixed and working

### 🐛 Fixed in 0.4.1
- **Gump rendering**: Now uses CreateGumpColorBox for proper backgrounds
- **High contrast colors**: Changed to bright white/green/red for readability
- **Single gump instance**: Disposes old gump before creating new one (no duplicates)
- **Target cursor**: Fixed WaitForTarget() parameter (was causing NO_CURSOR warnings)
- **Less log spam**: Gump updates no longer spam logs

## Version 0.4.0 (2025-10-11) - Alpha

### 🎯 Project Status
- **Phase**: Alpha - Lobby + Bar + Gumps UI
- **Functionality**: ~45% (2 of 7 rooms + UI system)
- **Stability**: ✅ Bar room functional, Gumps integrated

### 🆕 New in 0.4.0
- **Single-file architecture**: All code consolidated in `shadowguard.py`
- **Gump UI system**: Informative UI with room-specific data
- **Logger improvements**: Auto-creates `logs/` folder if missing

## Version 0.3.0 (2025-10-11) - Alpha

### 🎯 Project Status
- **Phase**: Alpha - Only Lobby + Bar implemented
- **Functionality**: ~40% (2 of 7 rooms)
- **Stability**: ✅ Bar room functional and stable

### ✅ Implemented

#### Bar Room (Complete)
- Automatic room detection (bottles + pirates)
- Bottle pickup from tables (range 2)
- Automatic bottle throwing at nearest pirates
- Correct priority: table → backpack
- Invulnerable filter
- Target cursor cleanup (no freezes)
- Optimized timing

#### Base System
- OOP architecture with Shadowguard class
- Error handling with @log_errors decorators
- Clean JSON logging (only important events)
- Room detection (Lobby + Bar)

### 🔧 Technical Improvements

#### Elegant Error Handling
- ``@log_errors`` decorator captures errors automatically
- Try/catch only at entry point
- Clean log: only ERRORS, WARNINGS, ROOM_CHANGE
- No THROWING/PICKUP spam

#### Automation Logic
- Inspired by Dorana's Shadowguard script
- Optimized timing: WaitForTarget(500ms), Pause(50ms), loop(600ms)
- Priority: ``table_bottle → backpack_bottle``
- Invulnerable filter: ``'Invulnerable' not in flags``

#### UI (0.4.0)
- ✅ Gump system integrated (single-file)
- ✅ Main gump: room name, timer, version, status
- ✅ Bar gump: status lines, bottle count, warnings
- Green SysMsg on room change
- No spam on screen
- Structured JSON log with auto-created logs/ folder

### 🏗️ Architecture (0.4.0)
- **Single file**: `shadowguard.py` contains all code
- **3 Classes**: `ShadowguardLogger`, `GumpManager`, `Shadowguard`
- **Easy distribution**: Download one file and run
- **Modular**: Clean separation with classes

### ❌ Pending (Beta/Release)
- [ ] Gump button callbacks (toggle, exit room)
- [ ] Orchard room
- [ ] Armory room  
- [ ] Fountain room
- [ ] Belfry room
- [ ] Roof boss

---

## Version 0.2.0 (2025-10-10)
- Initial adaptation for TazUO
- Basic Bar room detection
- Bottles + pirates logic

## Version 0.1.0 (2025-10-10)
- Initial project structure
- JSON logger implemented

---

**Credits:**
- Original concept: Dorana
- TazUO adaptation: Foruno
