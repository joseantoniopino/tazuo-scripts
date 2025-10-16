# Tomb of Kings - Lever & Flames Automation
# Helps player navigate and activate levers/flames in Tomb of Kings entrance
# 
# Features:
# - Detects usable levers (changes to green hue)
# - Auto-uses levers when player is nearby
# - Detects Flame of Order/Chaos after all levers used
# - Auto-speaks magic words when near flames

import os
import json
import traceback
from datetime import datetime, timezone

try:
    import API
    TAZUO_API = True
except ImportError:
    TAZUO_API = False
    print("WARNING: API not available (expected outside TazUO)")


# ============================================================================
# DEBUG MODE - Controlled via config.json
# ============================================================================
#
# FOR USERS: Enable debug in config.json for persistence.
# - Set "debug": true in config.json
# - Logs: ToK/logs/tomb_of_kings-YYYYMMDD.log (JSON Lines)
#

# Unified configuration loading: single read/creation at import time
def _load_or_create_config():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cfg_path = os.path.join(script_dir, "config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        # Create default config on first run
        default_cfg = {
            "version": "1.0.0",
            "debug": False,
            "use_distance": 1,
            "detection_range": 25,
            "hue_green": 0x0044,
            "hue_red": 0x0021,
            "phase_log_interval_seconds": 5.0
        }
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(default_cfg, f, indent=4, ensure_ascii=False)
        return default_cfg
    except Exception:
        # Fallback to safe defaults if anything goes wrong
        return {
            "version": "1.0.0",
            "debug": False,
            "use_distance": 1,
            "detection_range": 25,
            "hue_green": 0x0044,
            "hue_red": 0x0021,
            "phase_log_interval_seconds": 5.0
        }

# Load config once and set DEBUG before logger initialization
CONFIG = _load_or_create_config()
DEBUG = bool(CONFIG.get("debug", False))
# ============================================================================


# ============================================================================
# LOGGER CLASS - JSON structured logging
# ============================================================================

class ScriptLogger:
    """
    Generic JSON structured logger for TazUO scripts.
    Creates logs/ folder if it doesn't exist.
    Logs in JSON Lines format for easy parsing.
    Respects global DEBUG flag - only logs when DEBUG=True.
    """
    
    def __init__(self, script_name="script"):
        self.script_name = script_name
        
        # Create logs directory if it doesn't exist
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(script_dir, "logs")
        self.init_error = None
        
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except Exception as e:
            self.init_error = str(e)
            print(f"WARNING: Could not create logs directory: {e}")
    
    def _log_event(self, level, context, event, msg, details=None):
        """Internal method to write log entry - respects DEBUG flag"""
        # Only log if DEBUG mode is enabled
        if not DEBUG:
            return
        
        try:
            # Try to create log directory again if it failed during init
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
        """Log INFO level message (only if DEBUG=True)"""
        self._log_event("INFO", context, event, msg, details)
    
    def warning(self, context, event, msg, details=None):
        """Log WARNING level message (only if DEBUG=True)"""
        self._log_event("WARNING", context, event, msg, details)
    
    def error(self, context, event, msg, details=None):
        """Log ERROR level message (only if DEBUG=True)"""
        self._log_event("ERROR", context, event, msg, details)
    
    def debug(self, context, event, msg, details=None):
        """Log DEBUG level message (only if DEBUG=True)"""
        self._log_event("DEBUG", context, event, msg, details)


# Initialize logger globally
logger = ScriptLogger("tomb_of_kings")




class TombOfKings:
    """
    Tomb of Kings entrance automation.
    Simple lever detection and auto-use script.
    """
    
    # Graphic IDs - levers can be in 2 different graphics (server doesn't change them)
    LEVER_GRAPHICS = [4238, 4236]  # 0x108E, 0x108C
    
    # Names to identify lever state
    LEVER_USABLE_NAME = "A Lever"
    LEVER_UNUSABLE_NAME = "A Lever (unusable)"
    
    # Flame graphics and names
    FLAME_GRAPHIC = 6571  # Both flames have same graphic
    FLAME_ORDER_NAME = "Flame Of Order"
    FLAME_CHAOS_NAME = "Flame Of Chaos"
    
    # Hue colors (client-side visual markers)
    HUE_GREEN = 0x0044   # Verde - Usable/Detected
    HUE_RED = 0x0021     # Rojo - Used
    
    # Distances
    USE_DISTANCE = 1     # Distance to auto-use lever/flame (must be adjacent)
    DETECTION_RANGE = 25 # Range to detect objects
    
    def __init__(self):
        # Load config first and sync DEBUG
        self.config = self.load_config()
        self.version = self.config.get("version", "1.0.0")
        
        # Override tunables from config (instance-level to allow per-run overrides)
        self.USE_DISTANCE = int(self.config.get("use_distance", self.USE_DISTANCE))
        self.DETECTION_RANGE = int(self.config.get("detection_range", self.DETECTION_RANGE))
        self.HUE_GREEN = int(self.config.get("hue_green", self.HUE_GREEN))
        self.HUE_RED = int(self.config.get("hue_red", self.HUE_RED))
        
        # Data structures
        self.lever_data = {}  # {serial: {name, graphic, hue, x, y, initially_usable}}
        self.levers_scanned = False  # Scan only once
        self.total_usable_levers = 0  # Count usable levers at start (max 12)
        self.levers_used_count = 0  # Count of levers we've actually used
        
        # Flame tracking
        self.flame_data = {}  # {serial: {name, x, y, used}}
        self.flames_scanned = False
        self.flame_order_used = False
        self.flame_chaos_used = False
        
        # Logging reduction state
        self._lever_in_range = {}   # serial -> bool
        self._flame_in_range = {}   # serial -> bool
        self._last_phase_state = None
        self._phase_log_interval = float(self.config.get("phase_log_interval_seconds", 5.0))
        self._last_phase_log = 0.0
        
    def load_config(self):
        """Return preloaded configuration (single-load at module import)."""
        try:
            return dict(CONFIG)
        except Exception:
            return self.get_default_config()
    
    def get_default_config(self):
        """Default configuration values for this script."""
        return {
            "version": "1.0.0",
            "debug": False,
            "use_distance": self.USE_DISTANCE,
            "detection_range": self.DETECTION_RANGE,
            "hue_green": self.HUE_GREEN,
            "hue_red": self.HUE_RED
        }
        
    def run(self):
        """Main script loop"""
        logger.info("MAIN", "SCRIPT_START", "Tomb of Kings script started", {
            "debug_mode": DEBUG,
            "version": self.version,
            "player_x": API.Player.X,
            "player_y": API.Player.Y,
            "player_z": API.Player.Z
        })
        
        
        while not API.StopRequested:
            try:
                # Scan for levers ONLY ONCE at startup
                if not self.levers_scanned:
                    logger.debug("SCAN", "LEVER_SCAN_START", "Starting lever scan", {
                        "graphics": self.LEVER_GRAPHICS,
                        "detection_range": self.DETECTION_RANGE
                    })
                    
                    for graphic in self.LEVER_GRAPHICS:
                        levers = list(API.FindTypeAll(graphic, range=self.DETECTION_RANGE) or [])
                        logger.debug("SCAN", "FIND_TYPE_ALL", f"Found {len(levers)} levers for graphic {graphic}", {
                            "graphic": graphic,
                            "count": len(levers)
                        })
                        
                        for lever in levers:
                            initially_usable = lever.Name == self.LEVER_USABLE_NAME
                            self.lever_data[lever.Serial] = {
                                "name": lever.Name,
                                "graphic": lever.Graphic,
                                "hue": lever.Hue,
                                "x": lever.X,
                                "y": lever.Y,
                                "initially_usable": initially_usable
                            }
                            
                            logger.debug("SCAN", "LEVER_DETECTED", f"Lever: {lever.Name}", {
                                "serial": hex(lever.Serial),
                                "name": lever.Name,
                                "graphic": lever.Graphic,
                                "hue": hex(lever.Hue),
                                "position": f"({lever.X}, {lever.Y}, {lever.Z})",
                                "initially_usable": initially_usable
                            })
                            
                            # Only paint and count usable levers
                            if initially_usable:
                                lever.SetHue(self.HUE_GREEN)
                                self.total_usable_levers += 1
                                logger.debug("SCAN", "LEVER_PAINTED", f"Painted lever green", {
                                    "serial": hex(lever.Serial),
                                    "new_hue": hex(self.HUE_GREEN)
                                })
                    
                    logger.info("MAIN", "LEVER_SCAN_COMPLETE", f"Found {self.total_usable_levers} usable levers", {
                        "total_levers": len(self.lever_data),
                        "usable_levers": self.total_usable_levers,
                        "unusable_levers": len(self.lever_data) - self.total_usable_levers
                    })
                    
                    self.levers_scanned = True
                
                # Check if all levers used - trigger flame phase
                # If no usable levers at start (0), go straight to flame phase
                all_levers_used = (self.total_usable_levers == 0) or (self.levers_used_count >= self.total_usable_levers)
                
                # Throttled/state-change phase logging
                current_state = (all_levers_used, self.total_usable_levers, self.levers_used_count, self.flames_scanned)
                now = datetime.now(timezone.utc).timestamp()
                should_log_phase = (self._last_phase_state != current_state) or (now - self._last_phase_log >= self._phase_log_interval)
                if should_log_phase:
                    logger.debug("MAIN", "PHASE_CHECK", "Phase state", {
                        "all_levers_used": all_levers_used,
                        "total_usable_levers": self.total_usable_levers,
                        "levers_used_count": self.levers_used_count,
                        "flames_scanned": self.flames_scanned
                    })
                    self._last_phase_state = current_state
                    self._last_phase_log = now
                
                # Scan for flames ONLY if all levers used AND not scanned yet
                if all_levers_used and not self.flames_scanned:
                    logger.info("MAIN", "FLAME_PHASE_START", "All levers used, scanning flames", {
                        "levers_used": self.levers_used_count,
                        "total_levers": self.total_usable_levers
                    })
                    
                    flames = list(API.FindTypeAll(self.FLAME_GRAPHIC, range=self.DETECTION_RANGE) or [])
                    logger.debug("SCAN", "FLAME_FIND", f"Found {len(flames)} flame objects", {
                        "graphic": self.FLAME_GRAPHIC,
                        "count": len(flames)
                    })
                    
                    for flame in flames:
                        logger.debug("SCAN", "FLAME_CHECK", f"Checking flame: {flame.Name}", {
                            "serial": hex(flame.Serial),
                            "name": flame.Name,
                            "graphic": flame.Graphic,
                            "position": f"({flame.X}, {flame.Y}, {flame.Z})",
                            "is_valid": flame.Name in [self.FLAME_ORDER_NAME, self.FLAME_CHAOS_NAME]
                        })
                        
                        if flame.Name in [self.FLAME_ORDER_NAME, self.FLAME_CHAOS_NAME]:
                            self.flame_data[flame.Serial] = {
                                "name": flame.Name,
                                "x": flame.X,
                                "y": flame.Y,
                                "used": False
                            }
                            # Paint flames green
                            flame.SetHue(self.HUE_GREEN)
                            logger.debug("SCAN", "FLAME_PAINTED", f"Painted flame green: {flame.Name}", {
                                "serial": hex(flame.Serial),
                                "new_hue": hex(self.HUE_GREEN)
                            })
                    
                    logger.info("MAIN", "FLAME_SCAN_COMPLETE", f"Found {len(self.flame_data)} flames", {
                        "flame_count": len(self.flame_data),
                        "flame_names": [f["name"] for f in self.flame_data.values()]
                    })
                    self.flames_scanned = True
                
                # Process levers from MEMORY ONLY (no API calls)
                for serial, data in self.lever_data.items():
                    # Skip levers that were already unusable from the start
                    if not data["initially_usable"]:
                        continue
                    
                    name = data["name"]
                    pos_x = data["x"]
                    pos_y = data["y"]
                    
                    # Check if this usable lever hasn't been used yet
                    if name == self.LEVER_USABLE_NAME:
                        # Check if player is close enough
                        dx = abs(pos_x - API.Player.X)
                        dy = abs(pos_y - API.Player.Y)
                        distance = max(dx, dy)
                        
                        in_range = distance <= self.USE_DISTANCE
                        prev = self._lever_in_range.get(serial)
                        if prev is None or prev != in_range:
                            logger.debug("LEVER", "RANGE_CHANGE", "Lever range state changed", {
                                "serial": hex(serial),
                                "lever_pos": f"({pos_x}, {pos_y})",
                                "player_pos": f"({API.Player.X}, {API.Player.Y})",
                                "distance": distance,
                                "use_distance": self.USE_DISTANCE,
                                "in_range": in_range
                            })
                            self._lever_in_range[serial] = in_range
                        
                        if distance <= self.USE_DISTANCE:
                            # Use the lever
                            logger.info("LEVER", "USING_LEVER", "Attempting to use lever", {
                                "serial": hex(serial),
                                "position": f"({pos_x}, {pos_y})",
                                "distance": distance
                            })
                            
                            try:
                                API.UseObject(serial)
                                logger.debug("LEVER", "USE_OBJECT_CALLED", "API.UseObject called successfully", {
                                    "serial": hex(serial)
                                })
                            except Exception as e:
                                logger.error("LEVER", "USE_OBJECT_FAILED", f"Failed to use lever: {str(e)}", {
                                    "serial": hex(serial),
                                    "error": str(e),
                                    "traceback": traceback.format_exc()
                                })
                                API.SysMsg(f"ERROR using lever: {str(e)}", 0x21)
                            
                            # Mark as used in memory
                            self.lever_data[serial]["name"] = self.LEVER_UNUSABLE_NAME
                            self.levers_used_count += 1
                            
                            logger.info("LEVER", "LEVER_USED", "Lever marked as used", {
                                "serial": hex(serial),
                                "used_count": self.levers_used_count,
                                "total_count": self.total_usable_levers
                            })
                            
                            API.Pause(1.5)
                
                # Process flames from MEMORY ONLY (if flame phase active)
                if self.flames_scanned:
                    for serial, data in self.flame_data.items():
                        if data["used"]:
                            continue  # Skip already used flames
                        
                        name = data["name"]
                        pos_x = data["x"]
                        pos_y = data["y"]
                        
                        # Check if player is close enough
                        dx = abs(pos_x - API.Player.X)
                        dy = abs(pos_y - API.Player.Y)
                        distance = max(dx, dy)
                        
                        in_range = distance <= self.USE_DISTANCE
                        prev = self._flame_in_range.get(serial)
                        if prev is None or prev != in_range:
                            logger.debug("FLAME", "RANGE_CHANGE", "Flame range state changed", {
                                "serial": hex(serial),
                                "flame_name": name,
                                "flame_pos": f"({pos_x}, {pos_y})",
                                "player_pos": f"({API.Player.X}, {API.Player.Y})",
                                "distance": distance,
                                "use_distance": self.USE_DISTANCE,
                                "in_range": in_range
                            })
                            self._flame_in_range[serial] = in_range
                        
                        if distance <= self.USE_DISTANCE:
                            # Say magic word depending on flame type
                            if name == self.FLAME_ORDER_NAME:
                                logger.info("FLAME", "SPEAKING_ORD", "Speaking magic word: Ord", {
                                    "serial": hex(serial),
                                    "flame_name": name
                                })
                                try:
                                    API.Msg("Ord")
                                    logger.debug("FLAME", "MSG_SENT", "API.Msg('Ord') called successfully")
                                except Exception as e:
                                    logger.error("FLAME", "MSG_FAILED", f"Failed to speak: {str(e)}", {
                                        "error": str(e),
                                        "traceback": traceback.format_exc()
                                    })
                                self.flame_order_used = True
                            elif name == self.FLAME_CHAOS_NAME:
                                logger.info("FLAME", "SPEAKING_ANORD", "Speaking magic word: Anord", {
                                    "serial": hex(serial),
                                    "flame_name": name
                                })
                                try:
                                    API.Msg("Anord")
                                    logger.debug("FLAME", "MSG_SENT", "API.Msg('Anord') called successfully")
                                except Exception as e:
                                    logger.error("FLAME", "MSG_FAILED", f"Failed to speak: {str(e)}", {
                                        "error": str(e),
                                        "traceback": traceback.format_exc()
                                    })
                                self.flame_chaos_used = True
                            
                            # Mark flame as used in memory
                            self.flame_data[serial]["used"] = True
                            logger.debug("FLAME", "FLAME_MARKED_USED", "Flame marked as used in memory", {
                                "serial": hex(serial),
                                "order_used": self.flame_order_used,
                                "chaos_used": self.flame_chaos_used
                            })
                            
                            # Try to paint red (testing if flames allow hue change)
                            try:
                                logger.debug("FLAME", "PAINT_ATTEMPT", "Attempting to paint flame red", {
                                    "serial": hex(serial)
                                })
                                flame_obj = API.FindItem(serial)
                                if flame_obj:
                                    flame_obj.SetHue(self.HUE_RED)
                                    logger.debug("FLAME", "PAINT_SUCCESS", "Flame painted red", {
                                        "serial": hex(serial),
                                        "new_hue": hex(self.HUE_RED)
                                    })
                                else:
                                    logger.warning("FLAME", "PAINT_FAIL", "FindItem returned None", {
                                        "serial": hex(serial)
                                    })
                            except Exception as e:
                                logger.warning("FLAME", "PAINT_ERROR", f"Could not paint flame red: {str(e)}", {
                                    "serial": hex(serial),
                                    "error": str(e)
                                })
                            
                            API.Pause(1.5)
                
                # Check if all done - stop script
                if all_levers_used and self.flame_order_used and self.flame_chaos_used:
                    logger.info("MAIN", "COMPLETE", "All levers and flames used, stopping script", {
                        "levers_used": self.levers_used_count,
                        "total_levers": self.total_usable_levers,
                        "order_used": self.flame_order_used,
                        "chaos_used": self.flame_chaos_used
                    })
                    break
                
                API.Pause(0.25)  # Check every 250ms
                
            except Exception as e:
                error_msg = str(e)
                error_trace = traceback.format_exc()
                
                API.SysMsg(f"ERROR: {error_msg}", 0x21)
                logger.error("MAIN", "SCRIPT_ERROR", f"Unhandled exception in main loop", {
                    "error": error_msg,
                    "traceback": error_trace,
                    "player_pos": f"({API.Player.X}, {API.Player.Y}, {API.Player.Z})",
                    "levers_scanned": self.levers_scanned,
                    "flames_scanned": self.flames_scanned,
                    "levers_used": self.levers_used_count,
                    "total_levers": self.total_usable_levers
                })
                
                
                API.Pause(1.0)
    
    def cleanup(self):
        """Cleanup on script exit - Reset hues to 0"""
        logger.info("CLEANUP", "START", "Starting cleanup - resetting hues", {
            "lever_count": len(self.lever_data),
            "flame_count": len(self.flame_data)
        })
        
        try:
            # Reset lever hues
            for serial in self.lever_data.keys():
                try:
                    logger.debug("CLEANUP", "RESET_LEVER", f"Resetting lever hue", {
                        "serial": hex(serial)
                    })
                    lever = API.FindItem(serial)
                    if lever:
                        lever.SetHue(0x0)
                        logger.debug("CLEANUP", "LEVER_RESET", "Lever hue reset to 0", {
                            "serial": hex(serial)
                        })
                    else:
                        logger.warning("CLEANUP", "LEVER_NOT_FOUND", "Could not find lever for reset", {
                            "serial": hex(serial)
                        })
                except Exception as e:
                    logger.error("CLEANUP", "LEVER_RESET_ERROR", f"Error resetting lever: {str(e)}", {
                        "serial": hex(serial),
                        "error": str(e)
                    })
            
            # Reset flame hues
            for serial in self.flame_data.keys():
                try:
                    logger.debug("CLEANUP", "RESET_FLAME", f"Resetting flame hue", {
                        "serial": hex(serial)
                    })
                    flame = API.FindItem(serial)
                    if flame:
                        flame.SetHue(0x0)
                        logger.debug("CLEANUP", "FLAME_RESET", "Flame hue reset to 0", {
                            "serial": hex(serial)
                        })
                    else:
                        logger.warning("CLEANUP", "FLAME_NOT_FOUND", "Could not find flame for reset", {
                            "serial": hex(serial)
                        })
                except Exception as e:
                    logger.error("CLEANUP", "FLAME_RESET_ERROR", f"Error resetting flame: {str(e)}", {
                        "serial": hex(serial),
                        "error": str(e)
                    })
        except Exception as e:
            logger.error("CLEANUP", "CLEANUP_ERROR", f"General cleanup error: {str(e)}", {
                "error": str(e),
                "traceback": traceback.format_exc()
            })
        
        logger.info("CLEANUP", "COMPLETE", "Cleanup finished")


# ============================================================================
# ENTRY POINT
# ============================================================================

if TAZUO_API:
    script = None
    try:
        script = TombOfKings()
        logger.info("ENTRY", "INIT", "Script instance created successfully", {
            "version": script.version
        })
        script.run()
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        
        API.SysMsg(f"FATAL ERROR: {error_msg}", 0x21)
        logger.error("ENTRY", "FATAL_ERROR", "Fatal error in script execution", {
            "error": error_msg,
            "traceback": error_trace
        })
        
    finally:
        if script:
            try:
                script.cleanup()
            except Exception as e:
                logger.error("ENTRY", "CLEANUP_FAILED", f"Cleanup failed: {str(e)}", {
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
        logger.info("ENTRY", "SHUTDOWN", "Script execution ended")
else:
    print("Script must be run inside TazUO client")
