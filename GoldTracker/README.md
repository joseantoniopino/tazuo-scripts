# GoldTracker - Economy Tracking Script

**Version:** 1.0.0-alpha  
**Author:** Foruno  
**For:** TazUO (Ultima Online)

---

## 📖 Description

GoldTracker is an economy tracking script that monitors your farming efficiency across different zones in Ultima Online. It tracks gold gained, deaths, insurance costs, and calculates net profit per session.

**Key Features:**
- ✅ Automatic gold detection in backpack
- ✅ Death detection with insurance cost deduction
- ✅ Zone management with alias support
- ✅ Real-time dynamic gump display with pause/resume
- ✅ CSV export for session analysis
- ✅ Auto-save every 60 seconds
- ✅ Handles gold deposits (doesn't count as loss)
- ✅ Dynamic zone filtering with search-as-you-type
- ✅ Minimize/restore gump functionality
- ✅ Gump auto-reopens if accidentally closed

---

## 🚀 First Time Setup

When you run GoldTracker for the first time, it will **automatically create** the following files:

1. **`config.json`** - Script configuration (gold graphic ID, update intervals, etc.)
2. **`zones.json`** - Farming zones and aliases (13 default zones included)
3. **`sessions.csv`** - Session history (created empty with headers)

**No manual setup required!** Just run the script and it will initialize everything.

### Default Zones Included

Wind, Tomb of Kings, Doom, Shame, Hythloth, Covetous, Destard, Wrong, Citadel, Shadowguard, Khaldun, Despise, Deceit

---

## 📁 Files Overview

### Auto-Generated Files (Git-Ignored)

These files are created automatically on first run and contain your personal data:

- **`config.json`** - Your configuration settings (including debug mode)
- **`zones.json`** - Your custom zones and aliases
- **`sessions.csv`** - Your farming session history
- **`logs/`** - Debug logs (when `"debug": true` in config.json)

### Example Files (Included in Repo)

These show the format but are NOT used by the script:

- **`config.json.example`** - Example configuration format
- **`zones.json.example`** - Example zones format

---

## 🎮 How to Use

### 1. Start Script
Load the script in TazUO:
- Click **"Legion Script"** in the menu bar (top of window)
- Select `gold_tracker.py` from the list
- Script starts automatically

### 2. Select Zone (Enhanced Interface)

A dynamic zone selection gump will appear:

**Search & Filter:**
- Type in the search box to filter zones in real-time
- Searches both zone names and aliases
- Example: Type "tok" to find "Tomb of Kings"

**Select Existing Zone:**
- Click a radio button to auto-fill the search box
- Click **Start** to begin tracking

**Create New Zone:**
- Type a new zone name in the search box (e.g., "test zone")
- Click **Start**
- A modal will appear asking for aliases:
  - **First alias will be the zone name**
  - Add more aliases separated by commas
  - Example: `test zone, test, tz, testzone`
- Click **Create** to save the new zone

**Gump Auto-Reopen:**
- If you accidentally close the zone selection gump (right-click), it will automatically reappear
- Your filter text and selections are preserved

### 3. Insurance Reading

The script will:
- Open your insurance menu automatically
- Read your total insurance cost (e.g., 9180 gp)
- Close the menu and start tracking

*If auto-read fails, you'll be prompted to enter insurance manually.*

### 4. Farm!

The script tracks automatically:
- **Gold picked up** from corpses and loot
- **Deaths** (with insurance deduction per death)
- **Net profit** calculated in real-time
- **Duration** updated every 5 seconds

**Session Gump Features:**
- **Minimize button (-)** - Collapse to mini gump (top-right corner)
- **Expand button (+)** - Restore full gump from mini view
- **Pause button** - Freeze tracking temporarily
- **Resume button** - Continue tracking after pause
- **Stop button** - End session and save data

**Gump Auto-Reopen:**
- If you accidentally close the session gump (right-click), it will automatically reappear
- Both mini and full gumps auto-reopen if closed
- Gump position is preserved

### 5. Stop Session

Click **Stop** button when finished:
- Session data saved to `sessions.csv`
- Gump closes
- Script ends

---

## 📊 Gump Display

### Full Session Gump

```
╔═══════════════════════════════════╗
║  GoldTracker - Active Session  [-]║
╠═══════════════════════════════════╣
║  Zone: Tomb of Kings              ║
║  Duration: 45 min                 ║
║  Looted: 15,320 gp                ║
║  Deaths: 2                        ║
║  Insurance: 18,360 gp             ║
║  Net Profit: -3,040 gp            ║
╠═══════════════════════════════════╣
║  [Pause]  [Stop]  [Cancel]        ║
╚═══════════════════════════════════╝
```

### Minimized Gump

```
╔════════════╗
║ GT v1.0 [+]║
║ -3,040 gp  ║
╚════════════╝
```

**Note:** Click the `[-]` button to minimize, `[+]` to restore.

---

## ⚙️ Configuration

### config.json

```json
{
    "debug": false,
    "gold_graphic_id": 3821,
    "update_interval_seconds": 5,
    "auto_read_insurance_gump": true,
    "insurance_cost": 9180,
    "autosave_interval_seconds": 60
}
```

**Fields:**
- `debug` - Enable detailed JSON logging (default: false)
- `gold_graphic_id` - Item graphic ID for gold piles (default: 3821)
- `update_interval_seconds` - How often to scan backpack (default: 5)
- `auto_read_insurance_gump` - Try to auto-read insurance menu (requires TazUO dev build)
- `insurance_cost` - Total insurance cost read from gump or entered manually
- `autosave_interval_seconds` - Auto-save frequency (default: 60)

### zones.json

```json
{
  "Tomb of Kings": ["tok", "tomb", "tomb of kings", "tumba"],
  "Shadowguard": ["shadowguard", "sg", "roof"],
  "Doom": ["doom", "gauntlet"],
  "Wind": ["wind", "viento", "elementales"]
}
```

**Format:**
- **Key** = Canonical zone name (displayed in gump/CSV)
- **Value** = Array of aliases (user can type any alias to filter/select)

**Adding Zones:**

**Method 1: In-Game (Recommended)**
1. Type a new zone name in the search box (e.g., "my dungeon")
2. Click **Start**
3. Modal appears: "Create New Zone"
4. In the textbox, enter aliases separated by commas:
   - **First alias becomes the zone name**
   - Example: `my dungeon, md, dungeon, test`
5. Click **Create**
6. Zone is saved to `zones.json` automatically

**Method 2: Manual Edit**
1. Open `zones.json`
2. Add new entry:
   ```json
   "My Dungeon": ["my dungeon", "md", "dungeon", "test"]
   ```
3. Save file
4. Restart script

**Zone Selection Features:**
- ✅ **Dynamic filtering:** Type in the search box to filter zones by name or alias
- ✅ **Alias matching:** Type any alias to find zones (e.g., "tok" finds "Tomb of Kings")
- ✅ **Click to auto-fill:** Click a radio button to auto-fill the search box
- ✅ **Create new zones:** Enter a non-existent zone name to create it with custom aliases
- ✅ **Auto-reopen:** Zone selection and creation gumps reopen if accidentally closed

---

## 📈 Session Data (CSV)

All sessions are saved to `sessions.csv`:

| session_id | zone | start_time | end_time | duration_minutes | gold_gained | deaths | insurance_cost | net_profit | notes | merged | merged_from |
|------------|------|------------|----------|------------------|-------------|--------|----------------|------------|-------|--------|-------------|
| 1 | Tomb of Kings | 2025-10-14 10:14:13 | 2025-10-14 10:26:11 | 11 | 40785 | 0 | 0 | 40785 | | false | |
| 2 | Wind | 2025-10-14 11:57:21 | 2025-10-14 11:57:52 | 0 | 0 | 0 | 0 | 0 | | false | |

**Use this data to:**
- Calculate gold per hour by zone
- Identify most profitable farming spots
- Track death rates
- Analyze insurance costs vs gains
- Import into Excel/Google Sheets for charts and analysis

---

## 🐛 DEBUG Mode

To enable detailed logging:

1. Open `config.json`
2. Find: `"debug": false`
3. Change to: `"debug": true`
4. Restart the script
5. Logs will be written to `logs/gold_tracker-YYYYMMDD.log`

**Log format:** JSON Lines (one event per line)

**Example log entry:**
```json
{
  "event": "GOLD_PICKED_UP",
  "msg": "Gold detected",
  "level": "INFO",
  "context": "TRACKING",
  "details": {"gold": 1234, "total": 5678},
  "ts": "2025-10-14T15:14:25.716000Z"
}
```

**Note:** The `debug` setting is in `config.json` (git-ignored), so you can toggle it without tracking changes in version control.

---

## 🔧 Troubleshooting

### Insurance Auto-Read Fails
**Problem:** `AttributeError: 'API' object has no attribute 'GetGumpContents'`  
**Cause:** Older TazUO version  
**Solutions:**
1. Update to TazUO dev build (recommended)
2. Use manual input when prompted
3. Set `"auto_read_insurance_gump": false` in `config.json`

### Gold Not Detected
**Problem:** Script shows "No gold found" but you have gold  
**Solutions:**
1. Check `config.json` - `gold_graphic_id` should be `3821`
2. Enable debug mode (`"debug": true`) and check logs for scan results
3. Verify gold is in your backpack (not bank box)

### Zone Not Found
**Problem:** Typed alias doesn't match any zone  
**Solution:** Add alias to `zones.json` or create a new zone using the in-game modal

### Gump Disappears
**Problem:** Gump closes unexpectedly  
**Solution:** Gumps auto-reopen if closed accidentally. If they don't:
1. Check if script is still running (no error messages)
2. Enable debug mode and check logs
3. Restart script if needed

### Filter Not Working
**Problem:** Typing in search box doesn't filter zones  
**Solution:** 
1. Ensure you're typing in the correct textbox (top of zone selection gump)
2. Filter updates every 0.3 seconds - wait briefly
3. Check debug logs for "TEXT_CHANGED" events

---

## 📝 Notes

### Current Features
- ✅ **Gold deposits are ignored** - If you bank gold, session counter stays accurate
- ✅ **Deaths are auto-detected** - Uses TazUO death event callback
- ✅ **Pause/Resume** - Freeze tracking when AFK or handling deaths
- ✅ **Minimize/Restore** - Compact view when farming
- ✅ **Auto-reopen** - Gumps reappear if accidentally closed
- ✅ **Dynamic filtering** - Real-time zone search
- ✅ **Zone creation** - Add custom zones in-game

### Planned Features (Not Yet Implemented)
- ⏳ **Session merging** - Combine interrupted sessions
- ⏳ **Manual adjustments** - Edit gold/deaths after session
- ⏳ **Statistics dashboard** - View historical data in-game
- ⏳ **Zone deletion** - Remove zones from in-game UI

---

## 🆘 Support

For issues or questions:
1. Enable debug mode in `config.json` (`"debug": true`)
2. Reproduce the issue
3. Check logs in `GoldTracker/logs/gold_tracker-YYYYMMDD.log`
4. Report issue with relevant log excerpt

---

## 📜 License

Original work by Foruno for TazUO.

---

## 📚 Additional Documentation

- **Development notes:** See `PLANNING.md` for detailed implementation notes
- **Example files:** Check `config.json.example` and `zones.json.example` for format reference

---

**Last Updated:** October 14, 2025  
**Version:** 1.0.0-alpha
