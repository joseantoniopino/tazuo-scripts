# GoldTracker - Economy Tracking Script for TazUO
# Tracks gold farming efficiency, deaths, and insurance costs
# Version: 1.0.0-alpha
# Author: Foruno

import os
import sys
import json
import time
import re
import traceback
from datetime import datetime

# ============================================================================
# EARLY LOGGING - Capture ALL errors before anything else
# ============================================================================

script_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(script_dir, "logs")

def early_log(msg):
    """Log errors even before logger is initialized"""
    try:
        os.makedirs(log_dir, exist_ok=True)
        logfile = os.path.join(log_dir, f"gold_tracker-{datetime.utcnow().strftime('%Y%m%d')}.log")
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(f"{datetime.utcnow().isoformat()}Z - {msg}\n")
    except:
        pass  # Can't log, nothing we can do

try:
    early_log("=" * 80)
    early_log("SCRIPT START")
    early_log(f"Script dir: {script_dir}")
    
    sys.path.insert(0, script_dir)
    
    # Import API
    try:
        import API
        TAZUO_API = True
        early_log("API imported successfully")
    except ImportError as e:
        TAZUO_API = False
        early_log(f"WARNING: API not available: {e}")
    
    # Import helper modules (simple import works fine with _)
    early_log("Starting helper module imports")
    
    import _zone_manager
    import _session_manager
    import _gump_manager
    
    ZoneManager = _zone_manager.ZoneManager
    SessionManager = _session_manager.SessionManager
    GumpManager = _gump_manager.GumpManager
    
    early_log("All helper modules loaded successfully")
        
except Exception as e:
    early_log(f"FATAL ERROR in initialization: {e}")
    early_log(traceback.format_exc())
    if 'TAZUO_API' in globals() and TAZUO_API:
        try:
            API.SysMsg(f"GoldTracker FATAL ERROR - Check logs/gold_tracker-{datetime.utcnow().strftime('%Y%m%d')}.log", 0x21)
        except:
            pass
    raise


# ============================================================================
# LOAD DEBUG FROM CONFIG (before class definitions)
# ============================================================================
DEBUG = False  # Default value
try:
    config_path = os.path.join(script_dir, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            DEBUG = config_data.get("debug", False)
            early_log(f"DEBUG mode loaded from config: {DEBUG}")
except Exception as e:
    early_log(f"Could not load DEBUG from config: {e}")
    DEBUG = False


# ============================================================================
# LOGGER CLASS
# ============================================================================

class ScriptLogger:
    """JSON structured logger for TazUO scripts"""
    
    def __init__(self, script_name="gold_tracker"):
        self.script_name = script_name
        
        # Create logs directory
        self.log_dir = os.path.join(script_dir, "logs")
        self.init_error = None
        
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except Exception as e:
            self.init_error = str(e)
            print(f"WARNING: Could not create logs directory: {e}")
    
    def _log_event(self, level, context, event, msg, details=None):
        """Internal method to write log entry - respects DEBUG flag"""
        if not DEBUG:
            return
        
        try:
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir, exist_ok=True)
            
            entry = {
                "event": event,
                "msg": msg,
                "level": level,
                "context": context,
                "details": details or {},
                "ts": datetime.utcnow().isoformat() + "Z"
            }
            
            logfile = os.path.join(
                self.log_dir,
                f"{self.script_name}-{datetime.utcnow().strftime('%Y%m%d')}.log"
            )
            
            with open(logfile, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        except Exception as e:
            print(f"Logging error: {e}")
    
    def info(self, context, event, msg, details=None):
        """Log INFO level message"""
        self._log_event("INFO", context, event, msg, details)
    
    def warning(self, context, event, msg, details=None):
        """Log WARNING level message"""
        self._log_event("WARNING", context, event, msg, details)
    
    def error(self, context, event, msg, details=None):
        """Log ERROR level message"""
        self._log_event("ERROR", context, event, msg, details)
    
    def debug(self, context, event, msg, details=None):
        """Log DEBUG level message"""
        self._log_event("DEBUG", context, event, msg, details)


# ============================================================================
# GOLDTRACKER MAIN CLASS
# ============================================================================

class GoldTracker:
    """Main GoldTracker script class"""
    
    def __init__(self):
        self.version = "1.0.0-alpha"
        
        # Load config
        self.config = self.load_config()
        
        # Initialize logger
        self.logger = ScriptLogger("gold_tracker")
        
        # Initialize managers
        self.zone_mgr = ZoneManager(
            zones_file=os.path.join(script_dir, "zones.json"),
            debug=DEBUG
        )
        self.session_mgr = SessionManager(
            csv_file=os.path.join(script_dir, "sessions.csv"),
            logger=self.logger,
            debug=DEBUG
        )
        self.gump_mgr = GumpManager(
            api=API,
            logger=self.logger,
            debug=DEBUG
        )
        
        # Session state
        self.session_active = False
        self.stop_requested = False
        self.paused = False
        
        # Tracking variables
        self.last_backpack_gold = 0
        self.cached_insurance_cost = 0
        self.last_gold_check = time.time()
        self.last_autosave = time.time()
        
        self.logger.info("INIT", "START", "GoldTracker initialized", {
            "version": self.version,
            "debug": DEBUG
        })
        
        if DEBUG:
            API.SysMsg("GoldTracker v{} - DEBUG MODE ENABLED".format(self.version), 0x44)
        else:
            API.SysMsg("GoldTracker v{} started".format(self.version), 0x3F)
    
    def load_config(self):
        """Load configuration from config.json, create if missing"""
        config_file = os.path.join(script_dir, "config.json")
        
        try:
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    early_log(f"Configuration loaded from {config_file}")
                    return config
            else:
                # Generate default config file
                early_log("Creating default config.json")
                config = self.get_default_config()
                
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                
                early_log(f"Default config.json created at {config_file}")
                API.SysMsg("Created default config.json", 0x3F)
                return config
        
        except Exception as e:
            early_log(f"ERROR loading config: {e}")
            early_log(traceback.format_exc())
            return self.get_default_config()
    
    def get_default_config(self):
        """Get default configuration"""
        return {
            "gold_graphic_id": 3821,
            "update_interval_seconds": 5,
            "autosave_interval_seconds": 60,
            "auto_read_insurance_gump": True,
            "insurance_cost": 0,
            "debug": False
        }
    
    def run(self):
        """Main script execution"""
        try:
            self.logger.info("MAIN", "RUN_START", "Starting main execution")
            
            # Phase 1: Zone selection
            zone = self.select_zone()
            if not zone:
                API.SysMsg("GoldTracker: No zone selected, exiting", 0x44)
                self.logger.info("MAIN", "NO_ZONE", "User cancelled zone selection")
                return
            
            self.logger.info("MAIN", "ZONE_SELECTED", f"Zone selected: {zone}")
            
            # Phase 2: Initialize session
            self.initialize_session(zone)
            
            # Phase 3: Main tracking loop
            self.logger.info("MAIN", "LOOP_START", "Entering main tracking loop")
            
            while not API.StopRequested and not self.stop_requested:
                try:
                    # Process gump callbacks
                    API.ProcessCallbacks()
                    
                    # Check button states (using flags set by callbacks)
                    # DEBUG: Log button states periodically
                    if DEBUG and int(time.time()) % 5 == 0:
                        self.logger.debug("MAIN", "BUTTON_FLAGS", "Button states", {
                            "stop": self.gump_mgr.stop_button_clicked,
                            "cancel": self.gump_mgr.cancel_button_clicked,
                            "pause": self.gump_mgr.pause_button_clicked,
                            "minimize": self.gump_mgr.minimize_button_clicked,
                            "adjust": self.gump_mgr.adjust_button_clicked
                        })
                    if self.gump_mgr.stop_button_clicked:
                        self.logger.info("MAIN", "STOP_CLICKED", "Stop button clicked")
                        self.stop_requested = True
                        break
                    
                    if self.gump_mgr.cancel_button_clicked:
                        self.logger.info("MAIN", "CANCEL_CLICKED", "Cancel button clicked - deleting session")
                        self.session_mgr.delete_current_session()
                        API.SysMsg("Session cancelled and deleted", 0x21)
                        self.stop_requested = True
                        break
                    
                    if self.gump_mgr.pause_button_clicked:
                        self.paused = not self.paused
                        self.logger.info("MAIN", "PAUSE_TOGGLED", f"Paused: {self.paused}")
                        API.SysMsg("Session paused" if self.paused else "Session resumed", 0x44)
                        self.gump_mgr.pause_button_clicked = False  # Reset flag
                    
                    if self.gump_mgr.minimize_button_clicked:
                        self.logger.info("MAIN", "MINIMIZE_CLICKED", "Minimize button clicked")
                        self.gump_mgr.toggle_minimize()
                        self.gump_mgr.minimize_button_clicked = False  # Reset flag
                    
                    if self.gump_mgr.adjust_button_clicked:
                        self.logger.debug("MAIN", "ADJUST_CLICKED", "Manual adjustment button clicked")
                        self.process_manual_adjustment()
                        self.gump_mgr.adjust_button_clicked = False  # Reset flag
                    
                    # Check if gump was closed and recreate if needed
                    self.gump_mgr.recreate_session_gump_if_closed()
                    
                    # Skip tracking if paused
                    if self.paused:
                        API.Pause(0.25)
                        continue
                    
                    # Gold tracking (every N seconds)
                    if time.time() - self.last_gold_check >= self.config["update_interval_seconds"]:
                        self.update_gold_tracking()
                        self.last_gold_check = time.time()
                    
                    # Auto-save (every N seconds)
                    if time.time() - self.last_autosave >= self.config["autosave_interval_seconds"]:
                        self.session_mgr.auto_save()
                        self.last_autosave = time.time()
                        self.logger.info("AUTOSAVE", "SUCCESS", "Session auto-saved")
                    
                    # Update gump display
                    session_data = self.session_mgr.get_session_data()
                    if session_data:
                        self.gump_mgr.update_session_gump(session_data)
                    
                    API.Pause(0.25)
                
                except Exception as e:
                    self.logger.error("MAIN_LOOP", "ERROR", str(e), {
                        "traceback": traceback.format_exc()
                    })
                    API.Pause(1)
            
            self.logger.info("MAIN", "LOOP_END", "Exited main loop")
        
        except Exception as e:
            self.logger.error("MAIN", "FATAL_ERROR", str(e), {
                "traceback": traceback.format_exc()
            })
            API.SysMsg("GoldTracker: Fatal error - {}".format(str(e)), 0x21)
        
        finally:
            self.cleanup()
    
    def select_zone(self):
        """Show zone selection gump and wait for user input"""
        self.logger.info("ZONE_SELECT", "START", "Showing zone selection gump")
        
        zones = self.zone_mgr.get_zone_list()
        
        if not zones:
            self.logger.warning("ZONE_SELECT", "NO_ZONES", "No zones available")
            API.SysMsg("No zones configured. Please add zones to zones.json", 0x21)
            return None
        
        self.gump_mgr.create_zone_selection_gump(zones)
        
        # Wait for user to click Start button
        while not API.StopRequested:
            API.ProcessCallbacks()
            
            if self.gump_mgr.start_button_clicked:
                self.logger.debug("ZONE_SELECT", "START_CLICKED", "Start button clicked")
                
                # Check if new zone entered
                new_zone_text = self.gump_mgr.controls["new_zone_input"].Text.strip()
                if new_zone_text:
                    self.logger.info("ZONE_SELECT", "NEW_ZONE", f"New zone entered: {new_zone_text}")
                    self.zone_mgr.add_zone(new_zone_text)
                    
                    # Close zone gump
                    if self.gump_mgr.zone_gump:
                        self.gump_mgr.zone_gump.Dispose()
                    
                    return new_zone_text
                
                # Check which radio button is selected
                for i, radio in enumerate(self.gump_mgr.controls["zone_radios"]):
                    if radio.IsChecked:
                        selected_zone = zones[i]
                        self.logger.info("ZONE_SELECT", "ZONE_SELECTED", f"Selected: {selected_zone}")
                        
                        # Close zone gump
                        if self.gump_mgr.zone_gump:
                            self.gump_mgr.zone_gump.Dispose()
                        
                        return selected_zone
                
                API.SysMsg("Please select a zone or enter a new one", 0x21)
                self.logger.warning("ZONE_SELECT", "NO_SELECTION", "No zone selected")
            
            API.Pause(0.25)
        
        return None
    
    def initialize_session(self, zone):
        """Initialize farming session"""
        self.logger.info("SESSION_INIT", "START", f"Initializing session for {zone}")
        
        # Scan initial gold
        initial_gold = self.scan_backpack_gold()
        self.last_backpack_gold = initial_gold
        
        self.logger.info("SESSION_INIT", "INITIAL_GOLD", f"Initial gold: {initial_gold}")
        
        # Read insurance cost (always try to read, fallback to saved if fails)
        if self.config.get("auto_read_insurance_gump", True):
            self.cached_insurance_cost = self.read_insurance_from_gump()
        else:
            self.cached_insurance_cost = self.config.get("insurance_cost", 0)
            self.logger.info("SESSION_INIT", "SKIP_AUTO_READ", f"Using saved insurance: {self.cached_insurance_cost}")
        
        # Start session
        self.session_mgr.start_session(zone, initial_gold)
        self.session_mgr.update_session_data(insurance_cost=self.cached_insurance_cost)
        self.session_active = True
        
        # Register death callback
        API.Events.OnPlayerDeath(self.on_player_death)
        self.logger.info("SESSION_INIT", "DEATH_EVENT", "Registered death event callback")
        
        # Create session gump
        self.gump_mgr.create_session_gump(zone)
        
        API.SysMsg("GoldTracker: Session started in {}".format(zone), 0x3F)
        self.logger.info("SESSION_INIT", "COMPLETE", "Session initialization complete")
    
    def scan_backpack_gold(self):
        """Scan backpack for gold and return total amount"""
        try:
            gold_piles = API.FindTypeAll(
                self.config["gold_graphic_id"],
                API.Backpack
            )
            
            if not gold_piles:
                self.logger.debug("GOLD_SCAN", "NO_GOLD", "No gold found in backpack")
                return 0
            
            total_gold = sum(pile.Amount for pile in gold_piles)
            
            self.logger.debug("GOLD_SCAN", "SUCCESS", f"Found {total_gold} gold in {len(gold_piles)} piles")
            
            return total_gold
        
        except Exception as e:
            self.logger.error("GOLD_SCAN", "ERROR", str(e), {
                "traceback": traceback.format_exc()
            })
            return 0
    
    def save_insurance_to_config(self, cost):
        """Save insurance cost to config.json"""
        try:
            self.config["insurance_cost"] = cost
            config_path = os.path.join(script_dir, "config.json")
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            self.logger.info("INSURANCE", "SAVED_TO_CONFIG", f"Insurance saved: {cost} gp")
        
        except Exception as e:
            self.logger.error("INSURANCE", "SAVE_ERROR", str(e), {
                "traceback": traceback.format_exc()
            })
    
    def read_insurance_from_gump(self):
        """
        Open insurance gump and read TOTAL COST OF INSURANCE
        Called once at session start
        """
        try:
            self.logger.info("INSURANCE", "READ_START", "Opening insurance gump")
            API.SysMsg("Reading insurance cost...", 0x44)
            
            # Open insurance menu (context menu option 5)
            API.ContextMenu(API.Player.Serial, 5)
            self.logger.debug("INSURANCE", "CONTEXT_MENU", "Opened context menu option 5")
            
            API.Pause(1.5)  # Wait for gump to appear
            
            # Use GetGumpContents to read insurance cost
            self.logger.debug("INSURANCE", "METHOD", "Using GetGumpContents")
            gump_text = API.GetGumpContents()  # Get last opened gump (insurance menu)
            
            # LOG: Full gump content for debugging
            self.logger.info("INSURANCE", "GUMP_RAW", "Raw gump text", {
                "length": len(gump_text) if gump_text else 0,
                "content": gump_text[:500] if gump_text else "NULL",  # First 500 chars
                "full_content": gump_text  # Full content for detailed analysis
            })
            
            if gump_text and "TOTAL COST OF INSURANCE" in gump_text.upper():
                self.logger.info("INSURANCE", "GUMP_FOUND", "Found insurance text in gump")
                
                # Parse: "TOTAL COST OF INSURANCE: 9180"
                match = re.search(r'TOTAL COST OF INSURANCE[:\s]+(\d+)', gump_text, re.IGNORECASE)
                
                if match:
                    cost = int(match.group(1))
                    
                    self.logger.info("INSURANCE", "COST_PARSED", f"Insurance cost: {cost} gp")
                    
                    # Close the insurance gump
                    insurance_gump = API.GetGump()  # Get last gump
                    if insurance_gump:
                        insurance_gump.Dispose()
                    
                    # Save to config (always, regardless of source)
                    self.save_insurance_to_config(cost)
                    
                    API.SysMsg("Insurance cost: {} gp".format(cost), 0x3F)
                    return cost
                else:
                    # LOG: Regex didn't match
                    self.logger.warning("INSURANCE", "REGEX_FAILED", "Pattern not found in gump text", {
                        "pattern": r'TOTAL COST OF INSURANCE[:\s]+(\d+)',
                        "searched_in": gump_text
                    })
            else:
                # LOG: Text key not found in gump
                self.logger.warning("INSURANCE", "TEXT_NOT_FOUND", "Insurance text not in gump", {
                    "gump_empty": gump_text is None or gump_text == "",
                    "gump_preview": gump_text[:200] if gump_text else "NULL"
                })
            
            # Auto-read failed, raise exception to trigger manual input
            self.logger.warning("INSURANCE", "AUTO_READ_FAILED", "Could not parse insurance cost from gump")
            raise Exception("Could not parse insurance cost")
        
        except Exception as e:
            self.logger.error("INSURANCE", "READ_ERROR", str(e), {
                "traceback": traceback.format_exc()
            })
            
            # ALWAYS ask user for manual input if auto-read fails
            # Saved insurance cost is only used to PRE-FILL the input
            self.logger.info("INSURANCE", "PROMPT_USER", "Auto-read failed, prompting user for insurance cost")
            API.SysMsg("Could not auto-read insurance. Please verify/update.", 0x44)
            
            # Get saved insurance from config (default to 0 if not set)
            saved_insurance = self.config.get("insurance_cost", 0)
            
            # Create improved insurance input gump
            gump_width = 450
            gump_height = 240
            input_gump = self.gump_mgr.api.CreateGump(acceptMouseInput=True, canMove=True, keepOpen=False)
            input_gump.SetRect(0, 0, gump_width, gump_height)
            input_gump.CenterXInViewPort()
            input_gump.CenterYInViewPort()
            
            # Background
            bg = self.gump_mgr.api.CreateGumpColorBox(0.9, "#1a1a2e")
            bg.SetRect(0, 0, gump_width, gump_height)
            input_gump.Add(bg)
            
            # Title (centered)
            title = self.gump_mgr.api.CreateGumpLabel("Insurance Cost", 0x0481)  # Gold color
            title.SetPos(gump_width // 2 - 60, 30)
            input_gump.Add(title)
            
            # Instruction label (centered)
            instruction_text = "Your last saved insurance was: {} gp".format(saved_insurance)
            instruction = self.gump_mgr.api.CreateGumpLabel(instruction_text, 0x44)
            instruction.SetPos(gump_width // 2 - 130, 100)
            input_gump.Add(instruction)
            
            # Text input (centered, pre-filled with saved value)
            cost_input = self.gump_mgr.api.CreateGumpTextBox(str(saved_insurance), width=150, height=30)
            cost_input.SetPos(gump_width // 2 - 75, 135)
            input_gump.Add(cost_input)
            
            # OK button (centered)
            insurance_entered = {"clicked": False}
            def on_ok_click():
                insurance_entered["clicked"] = True
            
            ok_btn = self.gump_mgr.api.CreateSimpleButton("OK", 100, 35)
            ok_btn.SetPos(gump_width // 2 - 50, 185)
            input_gump.Add(ok_btn)
            self.gump_mgr.api.AddControlOnClick(ok_btn, on_ok_click)
            
            self.gump_mgr.api.AddGump(input_gump)
            
            # Wait for user input
            while not API.StopRequested and not insurance_entered["clicked"]:
                API.ProcessCallbacks()
                API.Pause(0.25)
            
            # Parse input
            try:
                cost_str = cost_input.Text.strip()
                cost = int(cost_str) if cost_str else 0
                
                # Close gump
                input_gump.Dispose()
                
                if cost > 0:
                    # Save to config (always, regardless of source)
                    self.save_insurance_to_config(cost)
                    
                    self.logger.info("INSURANCE", "USER_PROVIDED", f"User entered: {cost} gp")
                    API.SysMsg("Insurance cost saved: {} gp".format(cost), 0x3F)
                    return cost
                else:
                    self.logger.warning("INSURANCE", "NO_INPUT", "User provided no insurance cost")
                    API.SysMsg("No insurance cost entered. Using 0 gp.", 0x44)
                    return 0
            except:
                self.logger.error("INSURANCE", "PARSE_ERROR", "Could not parse user input")
                API.SysMsg("Invalid input. Using 0 gp.", 0x21)
                return 0
    
    def on_player_death(self, player_serial):
        """
        Callback triggered when player dies
        Uses cached insurance cost from session start
        """
        self.logger.info("DEATH", "DETECTED", "Player death event triggered", {
            "player_serial": player_serial
        })
        
        # Get current session data
        session = self.session_mgr.current_session
        if not session:
            self.logger.warning("DEATH", "NO_SESSION", "Death detected but no active session")
            return
        
        # Increment death count
        session["deaths"] += 1
        
        self.logger.info("DEATH", "COUNT_UPDATED", f"Death count: {session['deaths']}", {
            "insurance_cost_per_death": self.cached_insurance_cost,
            "total_deaths": session["deaths"]
        })
        
        # Update session data
        self.session_mgr.update_session_data(deaths=session["deaths"])
        
        # Notify user
        API.SysMsg("Death #{} - Insurance: {} gp".format(
            session["deaths"],
            self.cached_insurance_cost
        ), 0x21)
    
    def update_gold_tracking(self):
        """
        Scan backpack gold and update session counter
        Detects: looting (increase) and deposits (decrease, ignore)
        """
        try:
            current_gold = self.scan_backpack_gold()
            
            # Gold INCREASED = player looted
            if current_gold > self.last_backpack_gold:
                gold_looted = current_gold - self.last_backpack_gold
                
                session = self.session_mgr.current_session
                if session:
                    session["gold_looted"] += gold_looted
                    self.session_mgr.update_session_data(gold_looted=session["gold_looted"])
                
                self.logger.info("GOLD", "LOOTED", f"Player looted {gold_looted} gold", {
                    "current_backpack": current_gold,
                    "previous_backpack": self.last_backpack_gold,
                    "session_total": session["gold_looted"] if session else 0
                })
            
            # Gold DECREASED = player deposited to bank
            elif current_gold < self.last_backpack_gold:
                gold_deposited = self.last_backpack_gold - current_gold
                
                self.logger.info("GOLD", "DEPOSITED", f"Player deposited {gold_deposited} gold (ignored)", {
                    "current_backpack": current_gold,
                    "previous_backpack": self.last_backpack_gold
                })
            
            self.last_backpack_gold = current_gold
        
        except Exception as e:
            self.logger.error("GOLD", "TRACKING_ERROR", str(e), {
                "traceback": traceback.format_exc()
            })
    
    def process_manual_adjustment(self):
        """Process manual gold adjustment from textbox"""
        try:
            input_text = self.gump_mgr.controls["adjust_input"].Text.strip()
            
            if not input_text:
                self.logger.debug("ADJUSTMENT", "EMPTY_INPUT", "Empty adjustment input")
                return
            
            self.logger.info("ADJUSTMENT", "INPUT", f"Manual adjustment input: '{input_text}'")
            
            # Parse input (supports "+5000", "-5000", "5000")
            adjustment = int(input_text)
            
            # Update session
            session = self.session_mgr.current_session
            if session:
                session["manual_adjustments"] += adjustment
                self.session_mgr.update_session_data(manual_adjustments=session["manual_adjustments"])
            
            # Clear input
            self.gump_mgr.controls["adjust_input"].Text = ""
            
            self.logger.info("ADJUSTMENT", "APPLIED", f"Adjustment applied: {adjustment:+d} gp", {
                "total_adjustments": session["manual_adjustments"] if session else 0
            })
            
            API.SysMsg("Adjustment applied: {:+d} gp".format(adjustment), 0x3F)
        
        except ValueError as e:
            self.logger.warning("ADJUSTMENT", "INVALID_INPUT", f"Invalid input: '{input_text}'")
            API.SysMsg("Invalid input. Use numbers only (e.g., '-5000' or '5000')", 0x21)
        
        except Exception as e:
            self.logger.error("ADJUSTMENT", "ERROR", str(e), {
                "traceback": traceback.format_exc()
            })
    
    def cleanup(self):
        """Cleanup on script exit"""
        self.logger.info("CLEANUP", "START", "Starting cleanup")
        
        try:
            if self.session_active:
                # Finalize session
                self.session_mgr.end_session()
                API.SysMsg("GoldTracker: Session ended and saved", 0x3F)
                self.logger.info("CLEANUP", "SESSION_SAVED", "Session finalized and saved")
            
            # Cleanup gumps
            self.gump_mgr.cleanup()
            
            self.logger.info("CLEANUP", "COMPLETE", "GoldTracker cleanup complete")
        
        except Exception as e:
            self.logger.error("CLEANUP", "ERROR", str(e), {
                "traceback": traceback.format_exc()
            })


# ============================================================================
# ENTRY POINT
# ============================================================================

if TAZUO_API:
    script = None
    try:
        early_log("Creating GoldTracker instance")
        script = GoldTracker()
        early_log("Running GoldTracker")
        script.run()
    except Exception as e:
        early_log(f"FATAL ERROR: {e}")
        early_log(traceback.format_exc())
        try:
            API.SysMsg(f"GoldTracker ERROR - Check logs/gold_tracker-{datetime.utcnow().strftime('%Y%m%d')}.log", 0x21)
        except:
            pass
        if script and script.logger:
            script.logger.error("FATAL", "EXCEPTION", str(e), {
                "traceback": traceback.format_exc()
            })
    finally:
        if script:
            script.cleanup()
        early_log("SCRIPT END")
        early_log("=" * 80)
