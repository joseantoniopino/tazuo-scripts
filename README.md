# TazUO Scripts

Collection of Python automation scripts for Ultima Online using the TazUO client.

## 📦 Available Scripts

### 🪙 GoldTracker
Track gold farming sessions with detailed statistics, zone tracking, and insurance calculations.

- **Status:** Alpha (v1.0.0-alpha)
- **Features:**
  - Real-time gold tracking
  - Death counter with insurance costs
  - Zone-based session management
  - Minimizable UI
  - Auto-save sessions to CSV
  - Manual adjustments support

[📖 Full Documentation](./GoldTracker/README.md)

---

### 🛡️ Shadowguard
Automated room navigation and puzzle solving for Shadowguard dungeon.

- **Status:** Beta (v0.4.x)
- **Rooms Supported:** Lobby, Bar, Orchard, Armory, Fountain, Belfry, Roof
- **Features:**
  - Automatic room detection
  - Room-specific puzzle automation
  - Visual indicators (item hue painting)
  - DEBUG mode for troubleshooting

[📖 Full Documentation](./Shadowguard/README.md)

---

### 🔥 Tomb of Kings (ToK)
Automate lever pulling and flame activation in Tomb of Kings entrance.

- **Status:** Stable (v1.0.0)
- **Features:**
  - Auto-detect usable levers
  - Visual markers (green paint)
  - Auto-speak at flames
  - Script stops when complete

[📖 Full Documentation](./ToK/README.md)

---

## 🚀 Installation

1. **Download Scripts:**
   ```bash
   git clone https://github.com/joseantoniopino/tazuo-scripts.git
   ```

2. **Copy to TazUO:**
   - Copy desired script folder to your TazUO `LegionScripts` directory
   - Example: Copy `GoldTracker/` to `TazUO/LegionScripts/GoldTracker/`

3. **Configure:**
   - Copy `.example` files and rename (remove `.example`)
   - Edit configuration files as needed

4. **Load in TazUO:**
   - Open TazUO client
   - Go to: **Scripts → Load Script**
   - Select the script file (e.g., `gold_tracker.py`)

---

## 📚 Documentation

- **TazUO API:** See `docs/` folder for complete API reference
- **Individual Scripts:** Check each script's README for detailed usage

---

## 🛠️ Requirements

- **TazUO Client** (latest version recommended)
- **Python 3.x** (embedded in TazUO)
- **Ultima Online Account**

---

## 🐛 Troubleshooting

### Common Issues

**Q: Script shows import errors for `API.py`**  
A: This is normal. `API.py` is a stub for IDE autocompletion. The real API is provided by TazUO at runtime.

**Q: Script doesn't work**  
A: 
1. Enable DEBUG mode in script (set `DEBUG = True`)
2. Check logs in `script_folder/logs/`
3. Verify configuration files are correct

**Q: How do I enable debug logging?**  
A: Most scripts have a `DEBUG` flag at the top of the file. Change `DEBUG = False` to `DEBUG = True`.

---

## 🤝 Contributing

Contributions welcome! 

- **Bug Reports:** Open an issue with detailed description and logs
- **Feature Requests:** Describe the use case and expected behavior
- **Pull Requests:** Ensure code follows existing patterns and includes documentation

---

## 📄 License

MIT License - See individual script folders for details.

---

## 👤 Author

**Jose Pino (Foruno)**
- GitHub: [@joseantoniopino](https://github.com/joseantoniopino)
- Scripts for TazUO community

---

## 🙏 Credits

- **Shadowguard:** Inspired by Dorana's original concept, adapted for TazUO
- **TazUO Team:** For the amazing client and Python API
- **UO Community:** For continuous feedback and support

---

## ⚠️ Disclaimer

These scripts are provided as-is for educational purposes. Use at your own risk. Ensure compliance with your shard's rules regarding automation.
