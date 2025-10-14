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
- ✅ Real-time dynamic gump display
- ✅ CSV export for session analysis
- ✅ Auto-save every 60 seconds
- ✅ Handles gold deposits (doesn't count as loss)

---

## 🚀 First Time Setup

When you run GoldTracker for the first time, it will **automatically create** the following files:

1. **`config.json`** - Script configuration (gold graphic ID, update intervals, etc.)
2. **`zones.json`** - Farming zones and aliases (Tomb of Kings, Shadowguard, Doom, etc.)
3. **`sessions.csv`** - Session history (created empty with headers)

**No manual setup required!** Just run the script and it will initialize everything.

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
Run the script from TazUO:
```
Scripts → Load Script → gold_tracker.py
```

### 2. Select Zone
A gump will appear with zone options:
- Select your farming zone (e.g., "Tomb of Kings")
- Or create a custom zone name in the textbox
- Click **Start**

### 3. Insurance Reading
The script will:
- Open your insurance menu automatically
- Read your total insurance cost (e.g., 9180 gp)
- Close the menu and start tracking

*If auto-read fails, you'll be prompted to enter insurance manually.*

### 4. Farm!
The script tracks automatically:
- Gold picked up from corpses
- Deaths (with insurance deduction)
- Net profit in real-time

### 5. Stop Session
Click **Stop** button when finished:
- Session data saved to `sessions.csv`
- Gump closes
- Script ends

---

## 📊 Gump Display

The tracking gump shows:

```
╔═══════════════════════════════════╗
║  GoldTracker v1.0.0-alpha         ║
╠═══════════════════════════════════╣
║  Zone: Tomb of Kings              ║
║  Duration: 45 min                 ║
║  Looted: 15,320 gp                ║
║  Deaths: 2                        ║
║  Insurance: 18,360 gp             ║
║  Net Profit: -3,040 gp            ║
╠═══════════════════════════════════╣
║  [Pause]  [Stop]  [Adjust]        ║
╚═══════════════════════════════════╝
```

---

## ⚙️ Configuration

### config.json

```json
{
    "gold_graphic_id": 3821,
    "update_interval_seconds": 5,
    "autosave_interval_seconds": 60,
    "insurance_cost_per_item": 600,
    "manual_insurance_cost": null,
    "auto_read_insurance_gump": true
}
```

**Fields:**
- `gold_graphic_id` - Item graphic ID for gold piles (usually 3821)
- `update_interval_seconds` - How often to scan backpack (default: 5)
- `autosave_interval_seconds` - Auto-save frequency (default: 60)
- `insurance_cost_per_item` - Fallback insurance cost per item (unused if auto-read works)
- `manual_insurance_cost` - Manually entered insurance (saved after manual input)
- `auto_read_insurance_gump` - Try to auto-read insurance menu (requires TazUO dev build)

### zones.json

```json
{
  "Tomb of Kings": ["tok", "tomb", "tomb of kings", "tumba"],
  "Shadowguard": ["shadowguard", "sg", "roof"],
  "Doom": ["doom", "gauntlet"]
}
```

**Format:**
- **Key** = Canonical zone name (displayed in gump/CSV)
- **Value** = Array of aliases (user can type any alias)

**Adding zones:**
1. Edit `zones.json` manually, OR
2. Type a new zone name in the textbox when starting a session

---

## 📈 Session Data (CSV)

All sessions are saved to `sessions.csv`:

| session_id | zone | start_time | end_time | duration_minutes | gold_gained | deaths | insurance_cost | net_profit | notes | merged | merged_from |
|------------|------|------------|----------|------------------|-------------|--------|----------------|------------|-------|--------|-------------|
| 1 | Tomb of Kings | 2025-10-13 19:49:09 | 2025-10-13 19:52:36 | 3 | 1916 | 1 | 9180 | -7264 | | false | |

**Use this data to:**
- Calculate gold per hour by zone
- Identify most profitable farming spots
- Track death rates
- Analyze insurance costs vs gains

---

## 🐛 DEBUG Mode

To enable detailed logging:

1. Open `config.json`
2. Find: `"debug": false`
3. Change to: `"debug": true`
4. Restart the script
5. Logs will be written to `logs/gold_tracker-YYYYMMDD.log`

**Log format:** JSON Lines (one event per line)

**Note:** The `debug` setting is in `config.json` (git-ignored), so you can toggle it without tracking changes in version control.

---

## 🔧 Troubleshooting

### Insurance Auto-Read Fails
**Problem:** `AttributeError: 'API' object has no attribute 'GetGumpContents'`  
**Cause:** Older TazUO version  
**Solutions:**
1. Update to TazUO dev build (recommended)
2. Use manual input when prompted

### Gold Not Detected
**Problem:** Script shows "No gold found" but you have gold  
**Solutions:**
1. Check `config.json` - `gold_graphic_id` should be `3821`
2. Enable debug mode in `config.json` (`"debug": true`) and check logs for scan results

### Zone Not Found
**Problem:** Typed alias doesn't match any zone  
**Solution:** Add alias to `zones.json` or type exact zone name

---

## 📝 Notes

- **Gold deposits are ignored** - If you bank gold, session counter stays accurate
- **Deaths are auto-detected** - Uses TazUO death event callback
- **Session merging** - Planned feature for interrupted sessions (not yet implemented)
- **Manual adjustments** - Planned feature (not yet implemented)

---

## 🆘 Support

For issues or questions:
1. Enable debug mode in `config.json` (`"debug": true`)
2. Check logs in `GoldTracker/logs/`
3. Report issue with log excerpt

---

## 📜 License

Original work by Foruno for TazUO.

---

**Version History:** See `PLANNING.md` for detailed development notes.
