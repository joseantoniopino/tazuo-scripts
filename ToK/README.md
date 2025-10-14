# Tomb of Kings (ToK) - Lever Automation

Automates lever pulling and flame activation in the Tomb of Kings entrance.

## 📋 Features

- **Auto-detect usable levers** - Scans and identifies active levers
- **Visual markers** - Paints usable levers green
- **Auto-use** - Pulls levers when player is adjacent
- **Flame detection** - Detects Flame of Order/Chaos after all levers used
- **Auto-speak** - Says "Ord" or "Anord" at appropriate flame
- **Auto-stop** - Script stops when complete

## 🚀 Usage

1. Stand near ToK entrance (where levers are visible)
2. Load script: `Scripts → Load Script → tomb_of_kings.py`
3. Script will:
   - Scan for levers and paint usable ones green
   - Wait for you to approach levers
   - Auto-use when you're adjacent
   - Detect flame after all levers used
   - Auto-speak at flame
   - Stop automatically

## ⚙️ Configuration

### DEBUG Mode

Enable detailed logging by editing the script:

```python
DEBUG = True  # Line ~25 in tomb_of_kings.py
```

Logs are written to `ToK/logs/tomb_of_kings-YYYYMMDD.log`

## 🐛 Known Issues

### Visual Glitches
If levers appear to move/animate incorrectly:
- **Cause:** TazUO API redraw issue when re-querying changed items
- **Solution:** Restart script (scan-once pattern prevents this)

### Lever Not Detected
If a lever isn't painted green:
- Check lever name is exactly "A Lever" (case-sensitive)
- Ensure lever is within range (25 tiles)
- Check DEBUG logs for detection issues

## 📝 Version

**v1.0.0** - Stable Release

## 🙏 Credits

Original concept and implementation by **Foruno** for TazUO.
