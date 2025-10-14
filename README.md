# LegionScripts

A collection of automation scripts for **TazUO** (Ultima Online client). These scripts enhance gameplay through intelligent automation and quality-of-life improvements.

**Author:** Foruno  
**Target Client:** TazUO with Python API support  
**Language:** Python 3.x  

---

## 📦 Available Scripts

### 🪙 [GoldTracker](GoldTracker/) - Economy Tracking System
**Version:** 1.0.0-alpha

Track your farming efficiency across different zones. Monitor gold gains, deaths, insurance costs, and calculate net profit per session with a real-time dynamic gump display.

📖 [Full Documentation](GoldTracker/README.md)

---

### 🗝️ [Tomb of Kings Automation](ToK/) - Lever Puzzle Helper
**Version:** 1.0.0

Automates the tedious entrance puzzle at Tomb of Kings. No more manually pulling 12 levers and speaking phrases at flames - let the script handle it while you focus on the dungeon.

📖 [Full Documentation](ToK/README.md)

---

## 🚀 Installation

### Prerequisites
- **TazUO Client** (Latest version recommended)
- **Python API Support** (Built into TazUO)
- **Windows OS** (TazUO requirement)

### Step-by-Step Installation

1. **Download the Scripts**
   - Download this repository as ZIP or clone it:
   ```
   git clone https://github.com/joseantoniopino/LegionScripts.git
   ```

2. **Extract to Accessible Location**
   - Extract the ZIP to any folder you can access
   - Example: `C:\UO\LegionScripts\`
   - **No need** to place in TazUO installation folder

3. **Place Scripts in TazUO Folder**
   - Copy the `LegionScripts` folder to your TazUO installation:
   ```
   \TazUO\LegionScripts\
   ```
   - Final structure should be:
   ```
   \TazUO\LegionScripts\GoldTracker\gold_tracker.py
   \TazUO\LegionScripts\ToK\tomb_of_kings.py
   ```

4. **Load in TazUO**
   - Open TazUO client
   - Click **"Legion Script"** in the menu bar (top of window)
   - Select the script you want to load:
     - GoldTracker: `gold_tracker.py`
     - Tomb of Kings: `tomb_of_kings.py`
   - Script starts automatically

5. **First Run Setup (Automatic)**
   - Scripts will auto-generate required files:
     - Configuration files (`config.json`)
     - Data files (zones, sessions, etc.)
     - Logs folder
   - **No manual configuration needed!**

---

## 📖 Quick Start Guides

### GoldTracker - First Session

1. Load the script: Click **"Legion Script"** menu → Select `gold_tracker.py`
2. **Zone Selection Gump** appears:
   - Select a zone from the list (e.g., "Tomb of Kings")
   - Or type a new zone name to create one
   - Click **Start**
3. **Insurance Reading:**
   - Script opens your insurance menu automatically
   - Reads total insurance cost
   - Closes menu and starts tracking
4. **Farm!**
   - Gump shows real-time gold, deaths, net profit
   - **Pause** button to freeze tracking temporarily
   - **Minimize (-)** button for compact view
5. **Stop Session:**
   - Click **Stop** when finished
   - Session data saved to CSV file

📖 [Detailed GoldTracker Guide](GoldTracker/README.md)

---

### Tomb of Kings - Entrance Automation

1. **Go to Tomb of Kings entrance**
   - Stand near the lever area
2. **Load the script:** Click **"Legion Script"** menu → Select `tomb_of_kings.py`
3. **Watch the automation:**
   - Script detects all 12 levers (paints them green)
   - Walk near levers - script auto-pulls them
   - After all levers: Flames appear
   - Script auto-speaks phrases at flames
4. **Script stops automatically** when complete
5. **Enter the dungeon!**

📖 [Detailed ToK Guide](ToK/README.md)

---

## 🐛 Troubleshooting

### Script Won't Load
**Problem:** TazUO shows "Script failed to load"

**Solutions:**
1. Verify file has `.py` extension
2. Check file path is correct
3. Ensure TazUO has Python API enabled
4. Try loading a different script to test TazUO

---

### Script Stops Immediately
**Problem:** Script loads but closes right away

**Solutions:**
1. Enable debug mode:
   - Open script file in text editor
   - Find: `DEBUG = False`
   - Change to: `DEBUG = True`
   - Save and reload script
2. Check log file in `logs/` folder inside script directory
3. Report issue with log excerpt

---

### "API not available" Error
**Problem:** Script shows warning about API

**Cause:** Script loaded outside TazUO or Python API disabled

**Solutions:**
1. Make sure you're loading script FROM TazUO (not running Python directly)
2. Update to latest TazUO version
3. Check TazUO settings for Python API support

---

## 🔧 Debug Mode

If you encounter issues, enable debug logging:

1. Open the script file (`.py`) in any text editor
2. Find this line near the top:
   ```python
   DEBUG = False
   ```
3. Change to:
   ```python
   DEBUG = True
   ```
4. Save the file
5. Reload script in TazUO
6. Reproduce the issue
7. Check `logs/` folder inside script directory
8. Log file format: `script_name-YYYYMMDD.log`

**Debug logs are JSON format** - each line is one event with timestamp, context, and details.

---

## 📁 File Structure

After installation and first run, you'll have:

```
LegionScripts/
├── GoldTracker/
│   ├── gold_tracker.py       # Main script (load this)
│   ├── config.json           # Auto-generated config
│   ├── zones.json            # Auto-generated zones
│   ├── sessions.csv          # Auto-generated session history
│   ├── README.md             # Full documentation
│   └── logs/                 # Debug logs (if enabled)
│
└── ToK/
    ├── tomb_of_kings.py      # Main script (load this)
    ├── README.md             # Full documentation
    └── logs/                 # Debug logs (if enabled)
```

**Important:**
- Only `.py` files need to be loaded in TazUO
- Config/data files are auto-generated (don't edit unless needed)
- `logs/` folders appear only when debug mode is enabled

---

## 📝 Configuration Files

### GoldTracker: config.json

Auto-generated on first run. You can edit to customize:

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

**Common edits:**
- `"debug": true` - Enable detailed logging
- `"update_interval_seconds": 10` - Scan backpack less frequently (save CPU)

### GoldTracker: zones.json

Defines farming zones and search aliases. Example:

```json
{
  "Tomb of Kings": ["tok", "tomb", "tumba"],
  "Doom": ["doom", "gauntlet"],
  "Wind": ["wind", "elementales"]
}
```

You can also create zones **in-game** without editing this file!

---

## 🤝 Support & Feedback

### Reporting Issues

1. Enable debug mode in the script
2. Reproduce the issue
3. Find log file in `logs/` folder
4. Create GitHub issue with:
   - Script name and version
   - What you were doing
   - Error message or unexpected behavior
   - Relevant log excerpt

### Feature Requests

Open a GitHub issue with:
- Clear description of desired feature
- Use case (why it's needed)
- Expected behavior

---

## 📜 Credits

**Author:** Foruno

Special thanks to:
- TazUO development team for the Python API
- Ultima Online community for testing and feedback

---

## 🔄 Updates

### Checking for Updates

This repository is actively maintained. To get the latest versions:

1. **Download latest release** from GitHub
2. **Replace old script files** with new ones
3. **Keep your config files** (config.json, zones.json, sessions.csv)
4. Reload scripts in TazUO

**Your data is safe** - Config and session files are never overwritten by updates.

---

## ⚖️ License

All scripts are original work by Foruno for TazUO.

Free to use for personal gameplay. Not for commercial distribution.

---

**Last Updated:** October 14, 2025  
**Repository Version:** 1.0.0  
**Available Scripts:** 2
