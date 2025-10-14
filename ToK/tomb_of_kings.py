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
from datetime import datetime

try:
    import API
    TAZUO_API = True
except ImportError:
    TAZUO_API = False
    print("WARNING: API not available (expected outside TazUO)")


# ============================================================================
# DEBUG MODE - Set to True to enable extensive logging
# ============================================================================
# 
# **FOR USERS**: If you encounter issues with the script:
# 1. Change DEBUG = False to DEBUG = True below
# 2. Run the script and reproduce the issue
# 3. Find the log file in ToK/logs/tomb_of_kings-YYYYMMDD.log
# 4. Share the log file for troubleshooting
#
DEBUG = False  # <-- Change this to True for detailed logs
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


class ShadowguardLogger:
    """
    JSON structured logger for Shadowguard script.
    Creates logs/ folder if it doesn't exist.
    Logs in JSON Lines format for easy parsing.
    """
    
    def __init__(self):
        # Create logs directory if it doesn't exist
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(script_dir, "logs")
        
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except Exception as e:
            print(f"WARNING: Could not create logs directory: {e}")
            self.log_dir = None
    
    def _log_event(self, level, room, event, msg, details=None):
        """Internal method to write log entry"""
        if not self.log_dir:
            return
        
        try:
            entry = {
                "event": event,
                "msg": msg,
                "level": level,
                "details": details or {},
                "ts": datetime.utcnow().isoformat() + "Z",
                "room": room
            }
            
            logfile = os.path.join(
                self.log_dir, 
                f"shadowguard-{datetime.utcnow().strftime('%Y%m%d')}.log"
            )
            
            with open(logfile, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Logging error: {e}")
    
    def info(self, room, event, msg, details=None):
        """Log INFO level message"""
        self._log_event("INFO", room, event, msg, details)
    
    def warning(self, room, event, msg, details=None):
        """Log WARNING level message"""
        self._log_event("WARNING", room, event, msg, details)
    
    def error(self, room, event, msg, details=None):
        """Log ERROR level message"""
        self._log_event("ERROR", room, event, msg, details)
    
    def debug(self, room, event, msg, details=None):
        """Log DEBUG level message"""
        self._log_event("DEBUG", room, event, msg, details)


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
        self.version = "1.0.0"
        self.lever_data = {}  # Dictionary: {serial: {name, graphic, hue, x, y, initially_usable}}
        self.levers_scanned = False  # Flag to scan only once
        self.total_usable_levers = 0  # Count of usable levers at start (max 12)
        self.levers_used_count = 0  # Count of levers we've actually used
        
        # Flame tracking
        self.flame_data = {}  # {serial: {name, x, y, used}}
        self.flames_scanned = False
        self.flame_order_used = False
        self.flame_chaos_used = False
        
    def run(self):
        """Main script loop"""
        API.SysMsg("Tomb of Kings - Lever & Flames Helper", 0x3F)
        API.SysMsg("Walk near green objects to use them", 0x3F)
        
        logger.info("MAIN", "SCRIPT_START", "Tomb of Kings script started", {
            "debug_mode": DEBUG,
            "version": self.version,
            "player_x": API.Player.X,
            "player_y": API.Player.Y,
            "player_z": API.Player.Z
        })
        
        if DEBUG:
            API.SysMsg(f"DEBUG MODE: Enabled (detailed logs in logs/ folder)", 0x44)
        
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
                    
                    if self.total_usable_levers == 0:
                        API.SysMsg("No usable levers found - going straight to flames", 0x3F)
                    else:
                        API.SysMsg(f"Found {self.total_usable_levers} usable levers", 0x3F)
                    self.levers_scanned = True
                
                # Check if all levers used - trigger flame phase
                # If no usable levers at start (0), go straight to flame phase
                all_levers_used = (self.total_usable_levers == 0) or (self.levers_used_count >= self.total_usable_levers)
                
                logger.debug("MAIN", "PHASE_CHECK", "Checking phase transition", {
                    "all_levers_used": all_levers_used,
                    "total_usable_levers": self.total_usable_levers,
                    "levers_used_count": self.levers_used_count,
                    "flames_scanned": self.flames_scanned
                })
                
                # Scan for flames ONLY if all levers used AND not scanned yet
                if all_levers_used and not self.flames_scanned:
                    API.SysMsg("All levers used! Scanning for flames...", 0x3F)
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
                    API.SysMsg(f"Found {len(self.flame_data)} flames (green)", 0x3F)
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
                        
                        logger.debug("LEVER", "DISTANCE_CHECK", f"Checking lever proximity", {
                            "serial": hex(serial),
                            "lever_pos": f"({pos_x}, {pos_y})",
                            "player_pos": f"({API.Player.X}, {API.Player.Y})",
                            "distance": distance,
                            "use_distance": self.USE_DISTANCE,
                            "in_range": distance <= self.USE_DISTANCE
                        })
                        
                        if distance <= self.USE_DISTANCE:
                            # Use the lever
                            API.SysMsg(f"Using lever", 0x3F)
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
                            
                            API.SysMsg(f"Lever used! ({self.levers_used_count}/{self.total_usable_levers})", 0x3F)
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
                        
                        logger.debug("FLAME", "DISTANCE_CHECK", f"Checking flame proximity: {name}", {
                            "serial": hex(serial),
                            "flame_name": name,
                            "flame_pos": f"({pos_x}, {pos_y})",
                            "player_pos": f"({API.Player.X}, {API.Player.Y})",
                            "distance": distance,
                            "use_distance": self.USE_DISTANCE,
                            "in_range": distance <= self.USE_DISTANCE
                        })
                        
                        if distance <= self.USE_DISTANCE:
                            # Say magic word depending on flame type
                            if name == self.FLAME_ORDER_NAME:
                                API.SysMsg("Speaking: Ord", 0x3F)
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
                                API.SysMsg("Speaking: Anord", 0x3F)
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
                            
                            API.SysMsg(f"Flame used!", 0x3F)
                            API.Pause(1.5)
                
                # Check if all done - stop script
                if all_levers_used and self.flame_order_used and self.flame_chaos_used:
                    API.SysMsg("All tasks complete! Stopping script...", 0x44)
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
                
                if DEBUG:
                    API.SysMsg(f"DEBUG: Check log file for details", 0x44)
                
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
        API.SysMsg("Tomb of Kings Helper - Stopped", 0x21)


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
        
        if DEBUG:
            API.SysMsg(f"DEBUG: Full error logged to file", 0x44)
            print(f"FATAL ERROR DETAILS:\n{error_trace}")
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
