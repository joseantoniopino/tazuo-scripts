# 🎮 Shadowguard Script - TazUO Python

## ⚠️ Status: ALPHA - Work in Progress

**Version:** 0.3.0 Alpha  
**Original Concept:** Dorana  
**TazUO Adaptation:** Foruno  
**Date:** October 11, 2025

---

## 📋 Project Status

**Current Phase:** Alpha - Partial Implementation  
**Functionality:** ~40% (2 of 7 rooms)  
**Stability:** ✅ Bar room functional and stable

### ✅ Implemented
- Lobby (detection only)
- **Bar Room** (fully automated)

### ⏳ Pending
- Orchard Room
- Armory Room
- Fountain Room
- Belfry Room
- Roof Boss

---

## 📁 Files in This Directory

| File | Description |
|------|-------------|
| `shadowguard.py` | ✅ Main script (Alpha 0.3.0) |
| `shadowguard_logger.py` | � JSON logging system |
| `API.py` | 📚 TazUO Python API reference |
| `c#/shadowguard.cs` | 📝 Original inspiration (for reference) |
| **README.md** | � This file |
| **CHANGELOG.md** | 📝 Version history |
| **logs/** | � JSON log files |

---

## 🚀 QUICK START

### 1. Load Script in TazUO
```
Scripts → Load Script → shadowguard.py
```

### 2. Enter Shadowguard
- Script will automatically detect which room you're in
- Green system message will confirm: "Room: BAR" or "Room: LOBBY"

### 3. Let the Script Work
- **Bar Room:** Automatically picks up bottles and throws at pirates
- **Lobby:** Detection only (waits for you to enter a room)
- **Other Rooms:** Not yet implemented (Beta phase)

---

## 🎯 FUNCTIONALITY BY ROOM

### 🍺 Bar Room (✅ Fully Implemented)

**Automation:**
- ✅ Automatically detects pirates (murderer notoriety)
- ✅ Picks up bottles from tables (priority) and backpack
- ✅ Throws bottles at nearest pirate
- ✅ Filters out invulnerable targets
- ✅ Cleans up target cursor (no freezes)
- ✅ Health monitoring (warns if < 35 HP)

**How it works:**
1. Finds bottles on tables (range 2) or in backpack
2. Finds nearest pirate (murderer, not invulnerable)
3. Double-clicks bottle → targets pirate
4. Picks up thrown bottle after delay
5. Repeats until room is clear

**Detection:** Looks for liquor bottles or pirate mobiles

---

### 🏛️ Lobby (✅ Detection Only)

**Automation:**
- ✅ Detects lobby (crystal ball + ankh)
- ⏳ Waits for player to enter a room

**Detection:** Looks for crystal ball and ankh on ground

---

### ⏳ Other Rooms (Not Yet Implemented)

The following rooms are planned for Beta/Release phases:

- 🌳 **Orchard Room** - Tree pairing, apple placement
- ⚔️ **Armory Room** - Phylactery purification
- ⛲ **Fountain Room** - Canal piece placement
- 🦇 **Belfry Room** - Dragon wing collection
- 🏰 **Roof** - Boss fight automation

**Current Status:** These rooms will return to lobby if detected

---

## 🔧 TECHNICAL DETAILS

### Architecture
- **Language:** Python 3
- **API:** TazUO Python API (see `API.py`)
- **Design:** OOP with Shadowguard class
- **Error Handling:** Decorator pattern (`@log_errors`)
- **Logging:** JSON structured logs (optional)

### Key Features
- Automatic room detection
- Clean error handling with decorators
- Target cursor management (prevents freezes)
- Optimized timing (500ms target wait, 600ms main loop)
- Invulnerable target filtering

### Performance
- **Main Loop:** 600ms cycle time
- **Target Wait:** 500ms (lag compensation)
- **Bottle Pickup:** 200ms delay after throw
- **Room Detection:** Every loop cycle

---

## ⚠️ KNOWN LIMITATIONS

### 1. Alpha Phase - Limited Rooms
**Status:** Only Bar room fully automated

**Reason:** Phased development approach
- Alpha: Lobby + Bar (current)
- Beta: Add 5 remaining rooms
- Release: Full Shadowguard automation

**Workaround:** Manually complete other rooms

---

### 2. No GUI System
**Status:** No graphical interface

**Reason:** Focus on core functionality first

**Workaround:** 
- Green system messages show room changes
- JSON logs provide detailed information
- Script runs automatically (no UI needed)

**Future:** Informative Gumps planned for Beta

---

### 3. No Hotkeys
**Status:** No pause/stop hotkeys

**Reason:** Not yet implemented

**Workaround:** Use TazUO's Stop Script button

---

## 📊 FUNCTIONALITY METRICS

```
Room Detection:        100% ✅ (Lobby + Bar)
Bar Automation:        100% ✅ (Fully functional)
Error Handling:        100% ✅ (Decorator pattern)
Logging System:        100% ✅ (JSON structured)
Other 5 Rooms:           0% ⏳ (Pending Beta)

OVERALL:               ~40% ✅ (2 of 7 rooms)
```

---

## 📖 DOCUMENTATION

### � CHANGELOG.md
Complete version history and feature documentation
- What's implemented
- Technical improvements
- Pending features
- Version history

### 📚 API.py
TazUO Python API reference (2400+ lines)
- All available functions
- Stub file for development
- Import errors are normal (API is provided by TazUO at runtime)

### �️ logs/
JSON log files with detailed execution information
- Event tracking
- Error logging
- Performance metrics

---

## 💡 USAGE TIPS

### ✅ DO:
- Keep bandages ready for Bar room
- Maintain backpack space for bottles
- Stay near tables to maximize pickup range
- Monitor health warnings (< 35 HP)
- Check JSON logs if something seems wrong

### ❌ DON'T:
- Don't expect other rooms to work (not implemented yet)
- Don't use AFK without supervision (TOS violation)
- Don't panic if target cursor appears briefly (it's normal)
- Don't expect GUI/Gumps in Alpha phase

---

## 🐛 TROUBLESHOOTING

### "Script does nothing"
**Solution:** Verify you're in Bar room. Other rooms not implemented yet.

### "System shows UNKNOWN room"
**Solution:** Move around a bit. Script is detecting the room. If persists, you may be in an unimplemented room.

### "Target cursor stuck"
**Solution:** Script should auto-clear cursors. If it persists, restart the script.

### "Bottles not picked up"
**Solution:** 
- Stand within range 2 of tables
- Verify bottles are on tables (not in containers)
- Check backpack has space

### "Script stopped with error"
**Solution:** 
- Check `logs/` folder for error details
- Common cause: player HP < 35 (safety feature)
- Restart script after addressing issue

---

## 📅 VERSION HISTORY

See **CHANGELOG.md** for complete version history.

### v0.3.0 Alpha (Oct 11, 2025) - Current
- ✅ Bar room fully functional
- ✅ Elegant error handling (decorator pattern)
- ✅ Clean logging (JSON structured)
- ✅ Optimized timing and performance

### v0.2.0 (Oct 10, 2025)
- Initial TazUO adaptation
- Basic Bar room detection
- Bottles + pirates logic

### v0.1.0 (Oct 10, 2025)
- Initial project structure
- JSON logger implemented

---

## 🎯 ROADMAP

### Beta Phase (v0.4.0 - v0.9.0)
- [ ] Informative Gumps
- [ ] Orchard room automation
- [ ] Armory room automation
- [ ] Fountain room automation
- [ ] Belfry room automation
- [ ] Roof boss automation

### Release Phase (v1.0.0)
- [ ] All 7 rooms complete
- [ ] Full testing and optimization
- [ ] Comprehensive documentation
- [ ] Hotkey support
- [ ] Advanced features (if needed)

---

## 🤝 CREDITS

### Original Concept
**Dorana** - Original Shadowguard script inspiration

### TazUO Adaptation
**Foruno** - Python implementation for TazUO

### Special Thanks
- TazUO development team for the Python API
- UO community for testing and feedback

---

## � BUG REPORTS

If you encounter bugs:
1. Note which room it occurred in
2. Describe expected vs actual behavior
3. Check system messages for errors
4. Save log files from `logs/` folder
5. Include version number (0.3.0 Alpha)

---

## ⚖️ LICENSE & USAGE

This script is for personal use in Ultima Online.

**Important Reminders:**
- Do not use scripts AFK (violates most shard TOS)
- Respect your shard's rules
- Use with supervision
- This is Alpha software - expect bugs

---

## 🎮 ENJOY SHADOWGUARD!

This script should make your Shadowguard experience smoother.  
Good luck and happy hunting! 🏹

---

**Last Updated:** October 11, 2025  
**Document Version:** 2.0  
**Script Version:** 0.3.0 Alpha
