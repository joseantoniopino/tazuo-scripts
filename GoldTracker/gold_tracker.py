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
from datetime import datetime, timezone
from functools import wraps

# ============================================================================
# EARLY LOGGING - Capture ALL errors before anything else
# ============================================================================

script_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(script_dir, "logs")

def early_log(msg):
    """Log errors even before logger is initialized"""
    try:
        os.makedirs(log_dir, exist_ok=True)
        logfile = os.path.join(log_dir, f"gold_tracker-{datetime.now(timezone.utc).strftime('%Y%m%d')}.log")
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()}Z - {msg}\n")
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
            API.SysMsg(f"GoldTracker FATAL ERROR - Check logs/gold_tracker-{datetime.now(timezone.utc).strftime('%Y%m%d')}.log", 0x21)
        except:
            pass
    raise


# ============================================================================
# LOAD DEBUG FROM CONFIG (before class definitions)
# ============================================================================
try:
    config_path = os.path.join(script_dir, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            _debug_flag = bool(config_data.get("debug", False))
            early_log(f"DEBUG mode loaded from config: {_debug_flag}")
    else:
        _debug_flag = False
        early_log("config.json not found; DEBUG defaulting to False")
except Exception as e:
    early_log(f"Could not load DEBUG from config: {e}")
    _debug_flag = False
DEBUG = _debug_flag


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
                "ts": datetime.now(timezone.utc).isoformat() + "Z"
            }
            
            logfile = os.path.join(
                self.log_dir,
                f"{self.script_name}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
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
# LOGGING DECORATORS - Reduce visual noise
# ============================================================================

def log_method(context, event_prefix):
    """Decorator to auto-log method execution (entry/exit only)"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if DEBUG and hasattr(self, 'logger'):
                self.logger.debug(context, f"{event_prefix}_START", f"→ {func.__name__}")
            try:
                result = func(self, *args, **kwargs)
                if DEBUG and hasattr(self, 'logger'):
                    self.logger.debug(context, f"{event_prefix}_END", f"✓ {func.__name__}")
                return result
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(context, f"{event_prefix}_ERROR", f"✗ {func.__name__}: {e}", 
                                    {"traceback": traceback.format_exc()})
                raise
        return wrapper
    return decorator

def log_errors_only(context):
    """Decorator that only logs errors, no entry/exit noise"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(context, "ERROR", f"✗ {func.__name__}: {e}", 
                                    {"traceback": traceback.format_exc()})
                raise
        return wrapper
    return decorator


# ============================================================================
# MAIN SCRIPT CLASS
# ============================================================================


# ============================================================================
# GOLDTRACKER MAIN CLASS
# ============================================================================

class GoldTracker:
    """Main GoldTracker script class"""
    
    def __init__(self):
        # Load config first
        self.config = self.load_config()
        # Version from config (fallback to code default)
        self.version = self.config.get("version", "0.9.0-beta")
        # Sync global DEBUG with config for consistent logging behavior
        global DEBUG
        DEBUG = bool(self.config.get("debug", False))
        
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
        
        # Log throttling (prevent spam in long sessions)
        self.last_no_gold_log = 0  # Throttle "no gold" logs
        self.last_gold_amount = 0  # Track gold changes only
        
        # Session state
        self.session_active = False
        self.stop_requested = False
        self.paused = False
        
        # Tracking variables
        self.last_backpack_gold = 0
        self.cached_insurance_cost = 0
        self.last_gold_check = time.time()
        self.last_autosave = time.time()
        self.last_death_time = 0  # Protection against duplicate death events
        
        self.logger.info("INIT", "START", "GoldTracker initialized", {
            "version": self.version,
            "debug": DEBUG
        })
        
    
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
                return config
        
        except Exception as e:
            early_log(f"ERROR loading config: {e}")
            early_log(traceback.format_exc())
            return self.get_default_config()
    
    def get_default_config(self):
        """Get default configuration"""
        return {
            "version": "0.9.0-beta",
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
                    if self.gump_mgr.stop_button_clicked:
                        self.logger.info("MAIN", "STOP_CLICKED", "Stop button clicked")
                        self.stop_requested = True
                        break
                    
                    if self.gump_mgr.cancel_button_clicked:
                        self.logger.info("MAIN", "CANCEL_CLICKED", "Cancel button clicked - deleting session")
                        self.session_mgr.delete_current_session()
                        self.stop_requested = True
                        break
                    
                    if self.gump_mgr.pause_button_clicked:
                        self.paused = not self.paused
                        self.logger.info("MAIN", "PAUSE_TOGGLED", f"Paused: {self.paused}")
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
        """Show zone selection gump with dynamic filtering"""
        self.logger.info("ZONE_SELECT", "START", "Showing zone selection gump")
        
        # Get zones dict from zone manager
        zones_dict = self.zone_mgr.zones  # {zone_name: [aliases]}
        
        if not zones_dict:
            self.logger.warning("ZONE_SELECT", "NO_ZONES", "No zones available")
            return None
        
        # Create gump with filtering support
        self.gump_mgr.create_zone_selection_gump(zones_dict)
        
        # Wait for user to click Start button
        self.logger.debug("ZONE_SELECT", "POLLING_START", "Entering polling loop")
        
        while not API.StopRequested:
            API.ProcessCallbacks()
            
            # Poll textbox for changes to update filter
            if "filter_input" in self.gump_mgr.controls:
                try:
                    current_text = self.gump_mgr.controls["filter_input"].Text
                    
                    # Log polling activity (only when text changes)
                    if current_text != self.gump_mgr.last_filter_text:
                        self.logger.debug("ZONE_SELECT", "TEXT_CHANGED", f"Input changed", {
                            "old": self.gump_mgr.last_filter_text,
                            "new": current_text
                        })
                        self.gump_mgr.update_zone_filter(current_text)
                except Exception as e:
                    self.logger.error("ZONE_SELECT", "POLLING_ERROR", str(e), {
                        "traceback": traceback.format_exc()
                    })
            else:
                # Log if control missing (once)
                if not hasattr(self, '_logged_missing_control'):
                    self.logger.warning("ZONE_SELECT", "NO_INPUT_CONTROL", "filter_input not found", {
                        "available_controls": list(self.gump_mgr.controls.keys())
                    })
                    self._logged_missing_control = True
            
            # Check if zone gump was closed and recreate if needed
            self.gump_mgr.recreate_zone_selection_if_closed()
            
            # Check if Start button clicked
            if self.gump_mgr.start_button_clicked:
                self.logger.info("ZONE_SELECT", "START_CLICKED", "Start button clicked")
                
                # Get selected zone
                self.logger.debug("ZONE_SELECT", "GETTING_ZONE", "Calling get_selected_zone()")
                zone_name, exists = self.gump_mgr.get_selected_zone()
                
                self.logger.info("ZONE_SELECT", "ZONE_RESULT", f"Zone: '{zone_name}', Exists: {exists}")
                
                if not zone_name:
                    self.logger.warning("ZONE_SELECT", "NO_SELECTION", "No zone selected - input was empty")
                    self.gump_mgr.start_button_clicked = False  # Reset flag
                    API.Pause(0.3)
                    continue
                
                # If zone doesn't exist, ask to create it
                if not exists:
                    self.logger.info("ZONE_SELECT", "NEW_ZONE_PROMPT", f"Zone '{zone_name}' not found")
                    
                    # Close selection gump
                    if self.gump_mgr.zone_gump:
                        self.gump_mgr.zone_gump.Dispose()
                        self.gump_mgr.zone_gump = None
                    
                    # Show create zone prompt
                    confirmed, final_zone_name, aliases = self.gump_mgr.create_new_zone_prompt(zone_name)
                    
                    if confirmed:
                        # Add zone to zones.json (use final name from modal, not original)
                        self.zone_mgr.add_zone(final_zone_name, aliases)
                        self.logger.info("ZONE_SELECT", "ZONE_CREATED", 
                                       f"Created zone: {final_zone_name}, aliases: {aliases}")
                        return final_zone_name
                    else:
                        # User cancelled, recreate selection gump
                        self.logger.info("ZONE_SELECT", "CREATE_CANCELLED", "User cancelled zone creation")
                        self.gump_mgr.start_button_clicked = False
                        self.gump_mgr.create_zone_selection_gump(zones_dict)
                        API.Pause(0.3)
                        continue
                
                # Zone exists, use it
                self.logger.info("ZONE_SELECT", "ZONE_SELECTED", f"Selected: {zone_name}")
                
                # Close zone gump
                if self.gump_mgr.zone_gump:
                    self.gump_mgr.zone_gump.Dispose()
                
                return zone_name
            
            API.Pause(0.3)  # Polling interval
        
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
        
        # IMPORTANT: Unregister old callbacks first to prevent accumulation
        # This prevents "Too many callbacks registered!" error
        try:
            API.Events.OnPlayerDeath(None)
            API.Events.OnPlayerHitsChanged(None)
            self.logger.info("SESSION_INIT", "CALLBACKS_CLEARED", "Cleared any existing callbacks")
        except Exception as e:
            self.logger.warning("SESSION_INIT", "CLEAR_WARNING", f"Error clearing callbacks: {e}")
        
        # Register death callback
        API.Events.OnPlayerDeath(self.on_player_death)
        self.logger.info("SESSION_INIT", "DEATH_EVENT", "Registered death event callback")
        
        # Register hits changed callback (for debugging resurrection)
        API.Events.OnPlayerHitsChanged(self.on_player_hits_changed)
        self.logger.info("SESSION_INIT", "HITS_EVENT", "Registered hits changed event callback")
        
        # Create session gump
        self.gump_mgr.create_session_gump(zone)
        
        self.logger.info("SESSION_INIT", "COMPLETE", "Session initialization complete")
    
    def scan_backpack_gold(self):
        """Scan backpack for gold and return total amount"""
        try:
            gold_piles = API.FindTypeAll(
                self.config["gold_graphic_id"],
                API.Backpack
            )
            
            if not gold_piles:
                # Only log "no gold" once every 5 minutes (not every scan)
                if time.time() - self.last_no_gold_log > 300:
                    self.logger.debug("GOLD_SCAN", "NO_GOLD", "No gold in backpack (will not log again for 5 min)")
                    self.last_no_gold_log = time.time()
                return 0
            
            total_gold = sum(pile.Amount for pile in gold_piles)
            
            # Only log gold changes, not every scan
            if total_gold != self.last_gold_amount:
                self.logger.debug("GOLD_SCAN", "CHANGED", f"Gold: {self.last_gold_amount} → {total_gold}")
                self.last_gold_amount = total_gold
            
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
                    return cost
                else:
                    self.logger.warning("INSURANCE", "NO_INPUT", "User provided no insurance cost")
                    return 0
            except:
                self.logger.error("INSURANCE", "PARSE_ERROR", "Could not parse user input")
                return 0
    
    def on_player_hits_changed(self, new_hits):
        """
        Callback triggered when player HP changes
        Used for debugging death/resurrection events
        """
        # Log IMMEDIATELY that callback was triggered
        self.logger.info("HITS", "CALLBACK_TRIGGERED", f"OnPlayerHitsChanged fired with new_hits={new_hits}")
        
        try:
            # Only log significant changes or when near death/resurrection
            if new_hits == 0 or new_hits <= 10 or (hasattr(self, '_last_logged_hits') and abs(new_hits - self._last_logged_hits) > 20):
                player_state = {
                    "new_hits": new_hits,
                    "max_hits": API.Player.HitsMax,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                self.logger.info("HITS", "CHANGED", f"Player HP changed to {new_hits}/{API.Player.HitsMax}", player_state)
                self._last_logged_hits = new_hits
        except Exception as e:
            self.logger.error("HITS", "ERROR", str(e), {
                "traceback": traceback.format_exc()
            })
    
    def on_player_death(self, player_serial):
        """
        Callback triggered when player dies
        Uses cached insurance cost from session start
        
        DEBUG MODE: Logs extensive player state information to debug resurrection issues
        """
        # Log IMMEDIATELY that callback was triggered (before any other logic)
        early_log(f">>> OnPlayerDeath CALLBACK TRIGGERED - Serial: {hex(player_serial)}")
        
        # CRITICAL: Check if player is actually dead (HP=0) or this is resurrection event (HP>0)
        current_hp = API.Player.Hits
        early_log(f">>> Player HP at OnPlayerDeath: {current_hp}")
        
        if current_hp > 0:
            # This is resurrection event, not actual death - IGNORE IT
            self.logger.warning("DEATH", "RESURRECTION_EVENT", f"OnPlayerDeath fired with HP={current_hp} > 0 - resurrection event, ignoring")
            return
        
        current_time = time.time()
        early_log(f">>> About to capture player state")
        
        # EXTENSIVE LOGGING - Capture ALL player state (only for real deaths with HP=0)
        try:
            player_state = {
                "player_serial": hex(player_serial),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "time_since_last": f"{current_time - self.last_death_time:.2f}s" if hasattr(self, 'last_death_time') else "N/A",
                # Player vitals
                "player_hits": current_hp,
                "player_max_hits": API.Player.HitsMax,
                "player_stamina": API.Player.Stamina,
                "player_max_stamina": API.Player.StaminaMax,
                "player_mana": API.Player.Mana,
                "player_max_mana": API.Player.ManaMax,
                # Position
                "x": API.Player.X,
                "y": API.Player.Y,
                "z": API.Player.Z,
                # Other properties
                "notoriety": API.Player.Notoriety,
                "name": API.Player.Name
            }
            early_log(f">>> Player state captured successfully")
            self.logger.info("DEATH", "EVENT_TRIGGERED", "OnPlayerDeath event fired - FULL STATE CAPTURE", player_state)
        except Exception as e:
            early_log(f">>> ERROR capturing player state: {e}")
            self.logger.error("DEATH", "STATE_ERROR", f"Failed to capture state: {e}", {"traceback": traceback.format_exc()})
            # Continue anyway - death counting is more important than full state capture
        
        
        # Check if this is a duplicate event (within 10 seconds)
        early_log(f">>> About to check duplicate")
        if hasattr(self, 'last_death_time'):
            time_since_last = current_time - self.last_death_time
            if time_since_last < 10:
                self.logger.warning("DEATH", "DUPLICATE_IGNORED", f"Ignoring duplicate death event (fired {time_since_last:.2f}s after previous)", {
                    "player_serial": hex(player_serial),
                    "protection_threshold": "10 seconds",
                    "player_state_at_duplicate": player_state
                })
                return
        
        # Update last death time
        early_log(f">>> Updating last_death_time")
        self.last_death_time = current_time
        early_log(f">>> last_death_time updated to {current_time}")
        
        early_log(f">>> About to log PROCESSING")
        self.logger.info("DEATH", "PROCESSING", "Processing death event", {
            "player_serial": hex(player_serial)
        })
        
        # Get current session data
        early_log(f">>> Getting current session")
        session = self.session_mgr.current_session
        if not session:
            early_log(f">>> ERROR: No active session")
            self.logger.warning("DEATH", "NO_SESSION", "Death detected but no active session")
            return
        
        early_log(f">>> Session found, deaths before: {session['deaths']}")
        # Increment death count
        session["deaths"] += 1
        early_log(f">>> Deaths after increment: {session['deaths']}")
        
        self.logger.info("DEATH", "COUNT_UPDATED", f"Death count: {session['deaths']}", {
            "insurance_cost_per_death": self.cached_insurance_cost,
            "total_deaths": session["deaths"]
        })
        
        # Update session data
        self.session_mgr.update_session_data(deaths=session["deaths"])
        
        # No on-screen SysMsg to avoid noise; details are in logs when DEBUG=True
    
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
        
        except ValueError as e:
            self.logger.warning("ADJUSTMENT", "INVALID_INPUT", f"Invalid input: '{input_text}'")
        
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
                self.logger.info("CLEANUP", "SESSION_SAVED", "Session finalized and saved")
            
            # Unregister callbacks (CRITICAL to prevent "Too many callbacks" error)
            try:
                API.Events.OnPlayerDeath(None)
                API.Events.OnPlayerHitsChanged(None)
                self.logger.info("CLEANUP", "CALLBACKS_UNREGISTERED", "Death and hits callbacks unregistered")
            except Exception as e:
                self.logger.warning("CLEANUP", "CALLBACK_ERROR", f"Error unregistering callbacks: {e}")
            
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
            API.SysMsg(f"GoldTracker ERROR - Check logs/gold_tracker-{datetime.now(timezone.utc).strftime('%Y%m%d')}.log", 0x21)
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
