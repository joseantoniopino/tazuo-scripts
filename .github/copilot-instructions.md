# AI Agent Instructions - LegionScripts Project

## 📋 Project Overview

This is a **TazUO Python scripting collection** for Ultima Online automation. Multiple independent scripts for different dungeons/activities.

- **Project Type:** TazUO Python Scripts Collection
- **Main Scripts:**
  - `Shadowguard/shadowguard.py` - Shadowguard dungeon automation (see CHANGELOG for version)
  - `ToK/tomb_of_kings.py` - Tomb of Kings lever/flames automation (v1.0.0)
  - `cast_nether_blast.py` - Nether Blast spell casting
  - `healing_stone.py` - Healing stone automation
- **Target Client:** TazUO (Ultima Online client with Python API)
- **Shared Resources:** `API.py` (stub), `dumps/` (debugging), `docs/` (API documentation)

---

## 🎯 Core Project Rules

### 1. Language & Documentation
- **ALL documentation MUST be in English** (README, CHANGELOG, comments, commit messages)
- **Code comments in English only**
- **No Spanish in code or documentation** (except user-facing messages if needed)
- **CRITICAL: AI Agent MUST communicate with user IN SPANISH** - All dialogue, explanations, questions to user in Spanish
- **Code/docs output in English** - Comments, README, CHANGELOG, commits remain in English
- User speaks Spanish → Agent responds in Spanish → But generates English code/documentation

### 2. Credits & Attribution
- **Shadowguard:** Inspired by Dorana's concept, adapted for TazUO by Foruno
- **All other scripts:** Original work by Foruno for TazUO

### 3. Versioning
- Use **Semantic Versioning**: `MAJOR.MINOR.PATCH`
- Each script has independent versioning
- Check individual script folders for CHANGELOG/version info
- Complex scripts (Shadowguard) may use phase labels: `0.x.x Alpha`, `0.x.x Beta`, `1.x.x Release`

### 4. Token Efficiency & Output Style - CRITICAL
- **MINIMAL SUMMARIES** - Short bullet points ONLY, no extensive explanations
- **NO CHANGELOG UPDATES** during experimentation phase - only when explicitly requested
- **NO extensive "what I did" reports** - Code changes speak for themselves
- **NO markdown formatting overuse** - Minimal emojis, simple structure
- **NO comparison tables** - Ever, unless critical
- **NO "before/after" code blocks** - Only final code
- **NO ASCII art boxes** - Simple text only
- **Code-first approach** - Implement, then 1-2 line summary MAX
- **When done:** Simple "Done. Changed X in file Y." - That's it.

---

## 🐍 Python & TazUO Specific Rules

### API.py - CRITICAL UNDERSTANDING
- `API.py` is a **stub file** for IDE autocompletion (2413 lines)
- **Import errors from API.py are NORMAL and EXPECTED**
- The actual API is provided by TazUO at runtime
- **NEVER try to "fix" import errors in API.py**
- **LegionScript extension** (VS Code plugin) may show errors - this is normal
- When user mentions API errors, explain this is expected behavior

### Code Style
- **Architecture:** OOP with classes (not functional/procedural)
- **Error Handling:** Decorator pattern (`@log_errors`)
- **Type Hints:** Optional but encouraged for clarity
- **Naming:** 
  - `snake_case` for functions/methods/variables
  - `PascalCase` for classes
  - `UPPER_SNAKE_CASE` for constants

### TazUO API Constraints
- **No `if __name__ == "__main__":`** (breaks TazUO execution)
- Entry point must be direct execution (simple try/except/finally)
- Target cursor must be explicitly cleared (3 critical points)
- Timing is crucial: `WaitForTarget(500)`, `Pause(50/200/600)`

---

## 🏗️ Architecture Patterns

### Standard Script Structure
```python
# Script header with description
import os, json, traceback
from datetime import datetime

try:
    import API
    TAZUO_API = True
except ImportError:
    TAZUO_API = False

# DEBUG flag for logging (user-configurable)
DEBUG = False  # <-- Change to True for detailed logs

# Logger class (JSON structured logging)
class ScriptLogger:
    def __init__(self, script_name):
        # Creates logs/ directory
        pass
    
    def _log_event(self, level, context, event, msg, details=None):
        # Respects DEBUG flag
        if not DEBUG:
            return
        # Write JSON log
        pass

# Main script class
class MyScript:
    def __init__(self):
        self.version = "1.0.0"
        # State variables
    
    def run(self):
        # Main loop
        while not API.StopRequested:
            try:
                # Script logic
                pass
            except Exception as e:
                # Error handling with logging
                pass
    
    def cleanup(self):
        # Reset state, cleanup resources
        pass

# Entry point
if TAZUO_API:
    script = None
    try:
        script = MyScript()
        script.run()
    except Exception as e:
        # Fatal error handling
        pass
    finally:
        if script:
            script.cleanup()
```

### Key Design Decisions
- **DEBUG flag** - Global constant at top of file, user-visible
- **JSON logging** - Structured logs only when DEBUG=True
- **Scan-once pattern** - Store data in memory, never re-query changed items
- **OOP structure** - Class-based with init/run/cleanup pattern
- **Error handling** - Comprehensive try/except with traceback logging
- **No spam** - Minimal on-screen messages, detailed logs only in DEBUG mode

---

## 📊 Logging Standards

### ScriptLogger Class (Standard Pattern)
- **Format:** JSON Lines (one JSON object per line)
- **Location:** `script_folder/logs/script_name-YYYYMMDD.log`
- **Controlled by DEBUG flag:** No logs if `DEBUG = False`
- **Signature:** `logger.debug/info/warning/error(context, event, msg, details=None)`
- **Levels:**
  - `DEBUG` - Detailed flow (distance checks, API calls, state changes)
  - `INFO` - Important events (lever used, phase transition, scan complete)
  - `WARNING` - Non-fatal issues (item not found, paint failed)
  - `ERROR` - Exceptions with full traceback

### Log Entry Structure
```json
{
  "event": "LEVER_USED",
  "msg": "Lever marked as used",
  "level": "INFO",
  "context": "LEVER",
  "details": {"serial": "0x12345", "used_count": 3},
  "ts": "2025-10-13T12:34:56.789Z"
}
```

### System Messages (SysMsg)
- **Minimal on-screen messages** - Only critical user-facing info
- **Green (0x3F)** for success/info
- **Red (0x21)** for errors
- **Yellow (0x44)** for warnings/DEBUG mode notices
- **NO spam** - User should see ~5 messages per minute max

---

## 🎮 Scripts in Repository

### Shadowguard (`Shadowguard/`)
**Status:** See `Shadowguard/CHANGELOG.md` for current version and phase
- **Purpose:** Shadowguard dungeon room automation
- **Rooms (7 total):** Lobby, Bar, Orchard, Armory, Fountain, Belfry, Roof
- **Architecture:** Room detection + room-specific handlers
- **Credits:** Inspired by Dorana, adapted by Foruno

### Tomb of Kings (`ToK/`)
**Status:** v1.0.0 - Complete and stable
- **Purpose:** Automate lever pulling and flame activation in ToK entrance
- **Features:**
  - Detects and paints usable levers green
  - Auto-uses levers when player adjacent
  - Detects Flame of Order/Chaos after all levers used
  - Auto-speaks "Ord"/"Anord" at flames
  - Script stops automatically when complete
- **Key Pattern:** Scan-once-and-store (avoids TazUO API visual glitches)
- **DEBUG Mode:** Extensive logging available via `DEBUG = True` flag

### Other Scripts (Root Level)
- `cast_nether_blast.py` - Nether Blast casting automation
- `healing_stone.py` - Healing stone usage automation
- *(Check individual files for features/version)*

---

## 🔧 Technical Details to Remember

### Common Patterns Across Scripts

**Distance Calculation (Chebyshev):**
```python
dx = abs(target_x - API.Player.X)
dy = abs(target_y - API.Player.Y)
distance = max(dx, dy)  # Chebyshev distance
```

**Timing Critical Values:**
- `API.Pause(0.25)` - Main loop cycle (250ms)
- `API.Pause(1.5)` - After using object/action (1500ms)
- `API.WaitForTarget(500)` - Wait for target cursor (lag compensation)

**Object Detection:**
```python
# Find all of a type
items = list(API.FindTypeAll(graphic_id, range=25) or [])

# Find specific item (avoid after UseObject - causes visual glitch)
item = API.FindItem(serial)
```

**Hue/Color Constants:**
```python
HUE_GREEN = 0x0044   # Success/Usable
HUE_RED = 0x0021     # Error/Used
HUE_YELLOW = 0x0035  # Warning
# Always hex format (0x prefix)
```

### Script-Specific Details

**Shadowguard - Bottle Detection:**
```python
bottle_id = 0x099B  # Liquor bottle
# Name: "bottle" in name.lower() and "liquor" in name.lower()
```

**ToK - Lever Detection:**
```python
LEVER_GRAPHICS = [4238, 4236]  # 0x108E, 0x108C
LEVER_USABLE_NAME = "A Lever"
LEVER_UNUSABLE_NAME = "A Lever (unusable)"
```

**ToK - Flame Detection:**
```python
FLAME_GRAPHIC = 6571  # Both Order and Chaos
FLAME_ORDER_NAME = "Flame Of Order"  # Say "Ord"
FLAME_CHAOS_NAME = "Flame Of Chaos"  # Say "Anord"
```

---

## 🚫 What NOT to Do

### Code
- ❌ Don't use `if __name__ == "__main__":`
- ❌ Don't try to fix API.py import errors
- ❌ Don't create log spam (respect DEBUG flag)
- ❌ Don't call `FindItem()` or `FindTypeAll()` on items after `UseObject()` (visual glitch)
- ❌ Don't use shared variables across script runs (breaks functionality)
- ❌ Don't forget DEBUG flag at top of new scripts

### Documentation
- ❌ Don't use Spanish in any documentation
- ❌ Don't claim features not implemented
- ❌ Don't update CHANGELOG during debugging (only when user requests)

### Git
- ❌ Don't ignore this file (it should be versioned)
- ❌ Don't commit logs/ folders (should be in .gitignore)

---

## 📁 File Structure

```
LegionScripts/
├── .github/
│   └── copilot-instructions.md  # This file (versioned)
├── .gitignore                   # Git ignore rules (logs/, examples/, __pycache__, etc.)
├── API.py                       # TazUO API stub (2413 lines, imports fail = normal)
│
├── Shadowguard/                 # Shadowguard dungeon automation
│   ├── c#/
│   │   └── shadowguard.cs       # Original inspiration (reference only)
│   ├── logs/                    # JSON log files (git-ignored)
│   ├── shadowguard.py           # Main script (v0.4.3 - see CHANGELOG)
│   ├── CHANGELOG.md             # Version history (English)
│   └── README.md                # User documentation (English)
│
├── ToK/                         # Tomb of Kings automation
│   ├── logs/                    # JSON log files (git-ignored)
│   └── tomb_of_kings.py         # Main script (v1.0.0)
│
├── examples/                    # Test scripts (git-ignored)
│   ├── gump_test.py             # Dynamic gump update test
│   ├── logs/                    # Test logs
│   └── README.md                # Examples documentation
│
├── docs/                        # TazUO API documentation (reference)
│   ├── API.md                   # API overview
│   ├── PyMobile.md, PyItem.md   # Object type docs
│   └── ...                      # Other API docs
│
├── dumps/                       # Item dumps for debugging (git-ignored)
│   ├── dump_A_Lever.txt
│   ├── dump_Flame_Of_Order.txt
│   └── ...                      # Item property dumps from TazUO
│
├── cast_nether_blast.py         # Standalone scripts
├── healing_stone.py
└── (other .py scripts)
```

---

## 🎯 Development Workflow

### When User Asks for Changes
1. **Read context first** - Check current file state
2. **Understand scope** - Is it a bug fix or new feature?
3. **Plan changes** - Break down into logical steps
4. **Use manage_todo_list** - For multi-step work
5. **Test incrementally** - One change at a time
6. **NO CHANGELOG UPDATES** - Unless explicitly requested

### When User Reports Errors
1. **Check if API.py related** - Explain it's normal
2. **Ask for DEBUG mode** - User should set `DEBUG = True` and reproduce
3. **Check logs/** folder - JSON files have detailed trace
4. **Verify TazUO context** - Some errors are client-specific
5. **Check dumps/** folder - User may have provided item data
6. **Don't assume** - Ask for clarification if needed

### DEBUG Workflow
**When user reports issue:**
1. Ask user to set `DEBUG = True` at top of script
2. Ask user to reproduce issue
3. Request log file from `script_folder/logs/script_name-YYYYMMDD.log`
4. Analyze JSON log entries (timestamps, context, details)
5. Identify root cause from traceback/state information
6. Fix and ask user to test with DEBUG still enabled
7. Once confirmed fixed, user can set `DEBUG = False` again

### Experimentation Phase Rules - CRITICAL
- **Save tokens** - User pays per token, be efficient
- **NO CHANGELOG updates** during testing/debugging
- **NO extensive reports** - Just: "Fixed X in file Y"
- **CHANGELOG only when:** User says "update changelog" OR major release ready

### Version Bump Rules (Only when user requests)
- **Patch (X.Y.Z):** Bug fixes, small improvements
- **Minor (X.Y.0):** New features, significant additions
- **Major (X.0.0):** Breaking changes, complete rewrites, major milestones

---

## 💡 Common User Questions

### "API.py shows errors"
**Answer:** This is normal. API.py is a stub file for IDE autocompletion. The real API is provided by TazUO at runtime. The LegionScript VS Code extension may also show errors - ignore them.

### "Script doesn't work / has errors"
**Answer:** 
1. Ask user to set `DEBUG = True` at top of script file
2. Ask user to reproduce the issue
3. Request log file from `script_folder/logs/` directory
4. Analyze logs for root cause
5. If not enough info, ask for item dumps in `dumps/` folder

### "How do I enable debug logging?"
**Answer:** 
1. Open the script file (e.g., `ToK/tomb_of_kings.py`)
2. Find the line `DEBUG = False` near the top (usually line 20-35)
3. Change it to `DEBUG = True`
4. Run script - logs will be created in `script_folder/logs/`
5. After debugging, change back to `DEBUG = False` for normal use

### "Script causes visual glitches (items moving)"
**Answer:** This is a known TazUO API issue. Scripts must follow scan-once pattern:
- Scan items ONCE at startup with `FindTypeAll()`
- Store all data in memory (serial, position, name, etc.)
- Work from memory only - NEVER call `FindItem()` or `FindTypeAll()` again
- Don't query items after `UseObject()` - trust server
See "TazUO API Visual Glitches" section below for full details.

### "Need item information for debugging"
**Answer:** User can provide item dumps in the `dumps/` folder. These are text files with item properties, IDs, names, etc. from TazUO for debugging detection logic.

---

## 🔄 Context Preservation

If user starts new chat due to token limits:
1. **Read this file first** (you're doing it now!)
2. **Check script-specific files:**
   - `Shadowguard/CHANGELOG.md` - Shadowguard version/status
   - `ToK/tomb_of_kings.py` - ToK current implementation (check version in `__init__`)
   - Other script files for their current state
3. **Check logs/** folders - Recent execution history if DEBUG was enabled
4. **Check dumps/** folder - Item data user has provided for debugging

This file contains ALL accumulated knowledge from previous sessions.

---

## 🏆 Success Criteria

Code is good when:
- ✅ All documentation in English
- ✅ DEBUG flag present and user-visible (near top of file with clear instructions)
- ✅ ScriptLogger respects DEBUG flag (no logs if False)
- ✅ Scan-once pattern for item detection (no FindXXX after UseObject)
- ✅ Clean error handling with traceback logging
- ✅ Minimal on-screen messages (SysMsg only for critical info)
- ✅ Comprehensive DEBUG logging (when enabled)
- ✅ Proper cleanup on exit (reset hues, clear state)
- ✅ Version correctly labeled in script

---

## 📚 Additional Context

### Ultima Online Specifics
- **Notoriety Values:** 1=Innocent, 3=Criminal, 6=Murderer, etc.
- **Graphic IDs:** Hexadecimal (0x099B) or decimal (2459)
- **Range:** Distance in tiles (range 2 = 2 tiles from player)
- **Flags:** Mobile properties (Invulnerable, Poisoned, etc.)

### TazUO Client
- Python 3.x compatible
- Custom API for UO automation
- Scripts loaded via UI: Scripts → Load Script
- Stop script: TazUO button (no hotkeys implemented yet)

### TazUO API Visual Glitches - CRITICAL FINDINGS
**Discovered during ToK (Tomb of Kings) lever automation development:**

**The Problem:**
Calling `FindTypeAll()` or `FindItem()` on items that have **already changed server-side state** causes visual redraw glitches (items appear to move/animate incorrectly).

**When it happens:**
- ✅ First scan with `FindTypeAll()` = OK (items in initial state)
- ✅ Using `UseObject()` = OK (server changes item state correctly)
- ❌ Second `FindTypeAll()` or `FindItem()` on same items = Visual glitch
- ❌ **Even restarting script** causes glitch if items already changed in previous run

**Root Cause:**
Client has stale cache when re-querying items that changed server-side (position, graphic, hue, name). The Find methods force a redraw with incorrect cached data.

**Proven Solutions:**
1. **Scan ONCE** - Store all data in memory (serial, x, y, name, etc.)
2. **Never re-scan** - Work from memory only, never call Find methods again
3. **Paint BEFORE** - Call `SetHue()` only during initial scan, before any `UseObject()`
4. **No verification** - Trust server accepted actions, don't query items afterward

**Pattern for Tomb of Kings:**
```python
# Scan once at startup
if not self.scanned:
    levers = API.FindTypeAll(graphic, range=25)
    for lever in levers:
        self.data[lever.Serial] = {"x": lever.X, "y": lever.Y, "name": lever.Name}
        if lever.Name == "usable":
            lever.SetHue(GREEN)  # Paint BEFORE any use
    self.scanned = True

# Work from memory only
for serial, data in self.data.items():
    if distance_to(data["x"], data["y"]) <= 1:
        API.UseObject(serial)  # No FindItem after!
        self.used.add(serial)
```

**What DOESN'T work:**
- ❌ `FindItem()` after `UseObject()` - causes glitch
- ❌ `FindTypeAll()` on second script run - causes glitch  
- ❌ `SetHue()` on tiles (`GetTile` results) - invisible
- ❌ Shared variables to persist across runs - breaks painting

---

### TazUO Dynamic Gumps - CRITICAL PATTERN

**Discovered:** October 13, 2025 (verified with `examples/gump_test.py`)

**The Discovery:**
TazUO gumps **CAN be updated dynamically** without recreation. Initial belief was incorrect - gumps DO NOT need to be recreated to update content.

**Correct Pattern (Create Once, Update Properties):**
```python
# === CREATION (once at init) ===
self.gump = API.CreateGump(acceptMouseInput=True, canMove=True, keepOpen=False)
self.gump.SetRect(x, y, width, height)

# Add background
bg = API.CreateGumpColorBox(opacity=0.85, color="#1a1a1a")
bg.SetRect(0, 0, width, height)
self.gump.Add(bg)

# Create controls and STORE REFERENCES
self.label_counter = API.CreateGumpLabel("Counter: 0", hue=0x3F)
self.label_counter.SetPos(10, 10)
self.gump.Add(self.label_counter)

self.progress_bar = API.CreateGumpColorBox(opacity=0.9, color="#00FF00")
self.progress_bar.SetRect(10, 30, 100, 10)
self.gump.Add(self.progress_bar)

# Send to client ONCE
API.AddGump(self.gump)

# === UPDATE (in loop, every frame/second) ===
def update_gump(self, counter, progress_fraction):
    # Update text - NO recreation
    self.label_counter.Text = f"Counter: {counter}"
    
    # Update color - NO recreation
    self.label_counter.Hue = 0x21 if counter % 2 == 0 else 0x3F
    
    # Update width (progress bar) - NO recreation
    new_width = int(progress_fraction * 100)
    self.progress_bar.SetWidth(new_width)
```

**Key API Methods:**

**Control Creation:**
- `API.CreateGump(acceptMouseInput, canMove, keepOpen)` - Create gump container
- `API.CreateGumpLabel(text, hue)` - Create label control
- `API.CreateGumpColorBox(opacity, color)` - Create colored rectangle
- `API.CreateGumpItemPic(graphic, width, height)` - Create item graphic
- `API.CreateGumpCheckbox(text, isChecked)` - Create checkbox control (NEW)
- `API.AddGump(gump)` - Send gump to client (call ONCE)

**Control Positioning (use methods, NOT property assignment):**
- `control.SetPos(x, y)` - Set both X and Y
- `control.SetX(x)` - Set X only
- `control.SetY(y)` - Set Y only
- `control.SetRect(x, y, width, height)` - Set position and size
- `control.SetWidth(width)` - Change width (useful for progress bars)
- `control.SetHeight(height)` - Change height
- `control.GetX()` - Get current X position (read-only property workaround)
- `control.GetY()` - Get current Y position (read-only property workaround)

**Gump Positioning & Visibility (NEW):**
- `gump.SetInScreen()` - Ensure gump fully visible in screen boundaries
- `gump.CenterXInScreen()` - Center gump horizontally in full screen
- `gump.CenterYInScreen()` - Center gump vertically in full screen
- `gump.CenterXInViewPort()` - Center gump horizontally in viewport (game area)
- `gump.CenterYInViewPort()` - Center gump vertically in viewport (game area)

**Properties (read-only vs writable):**
- `control.X` / `control.Y` - **READ-ONLY** (use `SetPos()` to change)
- `control.Text` - **WRITABLE** (can assign: `control.Text = "new text"`)
- `control.Hue` - **WRITABLE** (can assign: `control.Hue = 0x21`)

**Checkbox Control (NEW):**
- `checkbox.IsChecked` - **READ-ONLY** property (bool)
- `checkbox.GetIsChecked()` - Get checkbox state (method)
- `checkbox.SetIsChecked(bool)` - Set checkbox state
- `checkbox.GetText()` - Get checkbox label text

**NineSlice Gumps:**
- `nineSliceGump.GetHue()` / `SetHue(hue)` - Get/set gump hue
- `nineSliceGump.GetResizable()` / `SetResizable(bool)` - Get/set resizable state
- `nineSliceGump.GetBorderSize()` / `SetBorderSize(int)` - Get/set border size
- `modernNineSliceGump.SetResizeCallback(callback)` - Callback for resize events

**Benefits:**
- ✅ NO flicker (recreation causes visible flash)
- ✅ Position preserved (gump stays where user moved it)
- ✅ Real-time updates (can update every frame if needed)
- ✅ Efficient (no disposal/recreation overhead)

**Hiding/Showing Elements:**
- Labels: Set `Text = ""` to hide, set actual text to show
- ColorBox: Set `SetWidth(0)` to hide, restore width to show
- ItemPic: Set `SetWidth(0)` and `SetHeight(0)` to hide, restore to show

**Common Mistakes:**
- ❌ Assigning to `control.X` or `control.Y` directly (read-only - use `SetPos()`)
- ❌ Calling `gump.AddLabel()` - method doesn't exist (use `API.CreateGumpLabel()`)
- ❌ Recreating gump every update (old incorrect pattern)
- ❌ Not storing control references (can't update without them)
- ❌ Confusing ViewPort vs Screen centering (ViewPort = game area, Screen = full window)

**Example Implementation (Shadowguard v0.4.3):**
```python
# Create gump with all possible controls (Lobby + Timer + Bar section)
# Controls start hidden (empty text, width 0)
# Update dynamically based on room:
#   - Lobby: Only basic info visible
#   - Bar: Basic info + Timer + Bar-specific controls
#   - Other rooms: Basic info + Timer + room-specific controls
```

**Testing:**
See `examples/gump_test.py` for complete working test that verifies:
- Counter incrementing every second (text update)
- Color cycling (hue update)
- Position tracking (reading gump.X, gump.Y)
- Timestamp updates (real-time refresh)
- 30 cycle auto-stop

---

## 📝 Summary for AI Agent

**Project:** LegionScripts - TazUO Python automation scripts collection  
**Key Scripts:** Shadowguard (dungeon rooms), ToK (levers/flames), others  
**Critical Patterns:**
- DEBUG flag at top of every script (user-configurable)
- ScriptLogger with JSON logging (only when DEBUG=True)
- Scan-once-and-store pattern (avoid TazUO visual glitches)
- Comprehensive error handling with tracebacks
- Minimal on-screen spam

**When in doubt:** Check this file, script-specific docs, and logs/ folders.

---

**Last Updated:** October 13, 2025  
**Instructions Version:** 2.3 (GoldTracker planning - full gump input API documented)

---

## 🧪 Testing & Examples

Test scripts are located in `examples/` folder (git-ignored):
- `gump_test.py` - Proof of concept for dynamic gump updates
- See `examples/README.md` for documentation on test scripts

When creating tests:
- Use DEBUG flag pattern
- Document what you're testing
- Clean up resources in finally block

---

**Note to AI Agent:** Read this file at the start of EVERY conversation. This contains critical project context and rules that MUST be followed. When in doubt, refer back to this file.
