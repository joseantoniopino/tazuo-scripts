# Tomb of Kings - Entrance Automation

**Version:** 1.0.0  
**Status:** ✅ Complete & Stable  
**Author:** Foruno  
**For:** TazUO (Ultima Online)

> **⚠️ COMPATIBILITY WARNING:**  
> This script is designed for **TazUO (modern version)** and is **NOT compatible with TazUO Legacy**.  
> Requires TazUO with Python API support.

---

## 📖 Description

Automates the tedious entrance puzzle at **Tomb of Kings**. The entrance requires pulling 12 levers and speaking two magic phrases at sacred flames - a repetitive and time-consuming task. This script handles it all automatically while you focus on the dungeon.

**What it does:**
- ✅ Detects all 12 levers in the entrance area
- ✅ Paints usable levers green for visual feedback
- ✅ Auto-pulls levers when you walk adjacent to them
- ✅ Detects Flame of Order and Flame of Chaos after all levers used
- ✅ Auto-speaks correct phrases at flames ("Ord" / "Anord")
- ✅ Stops automatically when entrance is complete

**Zero manual input required** - Just walk around near the levers!

---

## 🎮 How to Use

### 1. Preparation
- Go to **Tomb of Kings entrance** (the lever puzzle area)
- Stand anywhere near the levers

### 2. Load Script
- Click **"Legion Script"** in the TazUO menu bar (top of window)
- Select `tomb_of_kings.py` from the list
- Script starts automatically

### 3. Watch the Magic
The script will:
1. **Scan the area** (25 tile radius)
2. **Detect all levers** - Paints usable ones **green**
3. **Wait for you** to walk near levers
4. **Auto-pull levers** when you're adjacent (1 tile away)
5. **Track used levers** internally (no recolor)
6. **Detect flames—** After all 12 levers pulled, Flames appear
7. **Auto-speak phrases:**
   - Flame of Order → Says "Ord"
   - Flame of Chaos → Says "Anord"
8. **Stop automatically** Script ends when both flames activated

### 4. Enter Dungeon
Once a script stops, the entrance is open. Walk in and enjoy!

---

## 🎨 Visual Feedback

The script uses colored hues to show lever status:

- **Green (🟢)** - Usable lever (not yet pulled)
- **No color** - Used lever (wrong name)

**Note:** Colors are client-side only. Other players won't see them.

---

## 🔧 Configuration

### Auto-Generated Config

On first run, the script will create a `config.json` file in this folder with default settings. You can edit it and reload the script.

#### Keys
```json
{
  "version": "1.0.0",
  "debug": false,
  "use_distance": 1,
  "detection_range": 25,
  "hue_green": 68
}
```

Most users never need to change these values.

---

## 🐛 Debug Mode

If the script doesn't work as expected:

### Enable Debug Logging

1. Run the script once to generate `config.json` (if not present)
2. Open `public/ToK/config.json`
3. Set `"debug": true`
4. Save the file and reload the script
5. Reproduce the issue
6. Check `public/ToK/logs/tomb_of_kings-YYYYMMDD.log`

### What Gets Logged

When debug mode is enabled:
- Lever detection events
- Distance calculations
- Lever use attempts
- Flame detection
- Speech events
- Errors with full tracebacks

**Log format:** JSON Lines (one event per line)

---

## 🔍 Troubleshooting

### Levers Not Detected

**Problem:** Script loads but no levers turn green

**Possible Causes:**
1. Not in Tomb of Kings entrance area
2. Too far from levers (need to be within 25 tiles)
3. Levers already pulled by someone else

**Solutions:**
1. Walk closer to lever area
2. Enable debug mode and check logs for "LEVER_SCAN" events
3. Wait for levers to reset (if recently used)

---

### Levers Not Auto-Pulling

**Problem:** Levers are green but don't auto-pull when walking near

**Possible Causes:**
1. Not close enough (need to be exactly 1 tile away)
2. Lever already used
3. Server lag

**Solutions:**
1. Stand **directly adjacent** to lever (diagonal counts)
2. Check if the lever is no longer green (already used)
3. Enable debug mode and check "DISTANCE_CHECK" events

---

### Script Stops Too Early

**Problem:** Script ends before all levers pulled or flames activated

**Possible Causes:**
1. TazUO stop button pressed accidentally
2. Script error (check for error messages)

**Solutions:**
1. Don't press stop button until flames are done
2. Enable debug mode and check for ERROR events in logs
3. Reload script and try again

---

### Flames Not Detected

**Problem:** All levers pulled but flames don't appear or script doesn't speak

**Possible Causes:**
1. Flames not spawned yet (server delay)
2. Too far from flames
3. Flame names changed by server

**Solutions:**
1. Wait a few seconds after last lever
2. Walk closer to flame locations
3. Enable debug mode and check "FLAME_SCAN" events
4. Report issue with log excerpt

---

## 📊 Technical Details

### How It Works

**Scan-Once Pattern:**
- Script scans levers ONCE at startup
- Stores all lever data in memory (serial, position, name)
- Works from memory only - never re-scans changed items
- Avoids TazUO visual glitches from re-querying

**Detection Logic:**
- Lever graphic IDs: `4238` (0x108E) and `4236` (0x108C)
- Usable lever name: `"A Lever"`
- Unusable lever name: `"A Lever (unusable)"`
- Flame graphic ID: `6571` (both Order and Chaos)
- Flame names: `"Flame Of Order"` / `"Flame Of Chaos"`

**Auto-Use Logic:**
- Every 0.25 seconds (250ms polling)
- Checks distance to each lever
- Uses Chebyshev distance (max of dx, dy)
- Auto-uses if distance ≤ 1 tile
- 1.5 second cooldown after each use

**Safety Features:**
- Marks used levers immediately (prevents double-use)
- Ignores levers with "unusable" in name
- Stops automatically when complete
- No spam - one action per lever/flame

---

## 📝 Script Architecture

```python
class TombOfKings:
    def __init__(self):
        # Initialize state
        self.scanned = False
        self.lever_data = {}
        self.used_levers = set()
    
    def run(self):
        # Main loop
        while not API.StopRequested:
            if not self.scanned:
                self.scan_levers()     # Once at startup
            
            self.check_and_use_levers()  # Every cycle
            self.check_flames()          # After levers done
            API.Pause(0.25)
    
    def cleanup(self):
        # Reset hues, clear state
        pass
```

**Key Principles:**
- Scan once, store forever
- Work from memory, not live queries
- Client-side hue changes only
- No server spam

---

## 🚫 Limitations

### What This Script Does NOT Do

❌ Walk to levers automatically  
❌ Navigate the entrance maze  
❌ Handle combat with monsters  
❌ Open the dungeon entrance door  
❌ Farm inside the dungeon  

**You still need to:**
- Walk around the lever area yourself
- Handle any monsters that spawn
- Open the final entrance door manually
- Use separate scripts for dungeon farming

---

## 📦 Files Created

After first run:

```
ToK/
├── tomb_of_kings.py              # Main script
├── README.md                     # This file
├── config.json                   # Auto-generated configuration
└── logs/                         # Debug logs (if "debug": true)
    └── tomb_of_kings-YYYYMMDD.log
```

**Note:** `config.json` is created automatically on first run and stores debug and tuning options.

---

## 🔄 Updates

### Version History

**v1.0.0** (October 2025)
- Initial stable release
- All features complete and tested
- Scan-once pattern implemented
- Auto-reopen protection (if accidentally closed)

### Checking for Updates

Download latest version from GitHub repository and replace `tomb_of_kings.py` file.

Config is auto-generated on first run. If you've customized `config.json`, you can keep it when updating the script.

---

## 🤝 Support

### Reporting Issues

1. Run the script once to generate `config.json` (if not present)
2. Open `public/ToK/config.json` and set `"debug": true`
3. Reproduce the issue
4. Get log file from `public/ToK/logs/`
5. Create GitHub issue with:
   - Description of problem
   - What you expected
   - Log excerpt showing the issue

### Known Issues

None currently reported. Script is stable.

---

## 📜 Credits

**Author:** Foruno  
**Original Concept:** Manual lever solution (tedious!)  
**Automation:** Full TazUO Python implementation

---

## ⚖️ License

Original work by Foruno.  
Free to use for personal gameplay.

---

**Last Updated:** October 14, 2025  
**Script Version:** 1.0.0  
**Lines of Code:** ~620
