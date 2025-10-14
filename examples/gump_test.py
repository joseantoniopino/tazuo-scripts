# Gump Update Test - Verify dynamic gump updates without recreation
# This script tests the correct pattern for updating gump content in real-time
#
# NEW (v1.1): Added viewport centering using new API methods from PR merge
# - gump.CenterXInViewPort() - Center horizontally in game area
# - gump.CenterYInViewPort() - Center vertically in game area

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
DEBUG = True  # <-- Enabled for testing
# ============================================================================


# ============================================================================
# LOGGER CLASS
# ============================================================================

class ScriptLogger:
    """JSON structured logger for TazUO scripts."""
    
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
logger = ScriptLogger("gump_test")


# ============================================================================
# GUMP TEST UI
# ============================================================================

class GumpTestUI:
    """Test script for dynamic gump updates without recreation"""
    
    def __init__(self):
        self.version = "1.1.0-test"  # Updated - added viewport centering
        self.gump = None
        self.counter = 0
        self.test_label = None
        self.position_label = None
        self.counter_label = None
        self.status_label = None
        
        logger.info("INIT", "START", "Initializing GumpTestUI", {
            "version": self.version
        })
    
    def create_gump(self):
        """Create gump once and store control references"""
        logger.info("GUMP", "CREATE_START", "Creating gump with controls")
        
        try:
            # Create gump
            self.gump = API.CreateGump(acceptMouseInput=True, canMove=True, keepOpen=False)
            logger.debug("GUMP", "GUMP_CREATED", "API.CreateGump() called successfully")
            
            # Set initial position and size
            initial_x = 100
            initial_y = 100
            width = 350
            height = 250
            self.gump.SetRect(initial_x, initial_y, width, height)
            
            # Center in viewport (game area) - NEW API method from PR merge
            self.gump.CenterXInViewPort()
            self.gump.CenterYInViewPort()
            logger.debug("GUMP", "RECT_SET", "Gump rectangle set and centered in viewport", {
                "initial_x": initial_x,
                "initial_y": initial_y,
                "width": width,
                "height": height,
                "centered": "viewport"
            })
            
            # Add semi-transparent dark background
            background = API.CreateGumpColorBox(0.85, "#1a1a1a")
            background.SetRect(0, 0, width, height)
            self.gump.Add(background)
            logger.debug("GUMP", "BACKGROUND_ADDED", "Dark background added", {
                "opacity": 0.85, "color": "#1a1a1a"
            })
            
            # Add title label (static)
            title = API.CreateGumpLabel("🧪 Gump Update Test", hue=0x3F)
            title.SetPos(10, 10)
            self.gump.Add(title)
            logger.debug("GUMP", "TITLE_ADDED", "Title label added", {
                "text": "Gump Update Test",
                "hue": hex(0x3F)
            })
            
            # Add version label (static)
            version = API.CreateGumpLabel(f"Version: {self.version}", hue=0x44)
            version.SetPos(10, 30)
            self.gump.Add(version)
            logger.debug("GUMP", "VERSION_ADDED", "Version label added")
            
            # Add dynamic labels (will be updated)
            self.counter_label = API.CreateGumpLabel("Counter: 0", hue=0x63)
            self.counter_label.SetPos(10, 60)
            self.gump.Add(self.counter_label)
            logger.debug("GUMP", "COUNTER_LABEL_ADDED", "Counter label added (dynamic)")
            
            self.position_label = API.CreateGumpLabel("Position: (?, ?)", hue=0x63)
            self.position_label.SetPos(10, 85)
            self.gump.Add(self.position_label)
            logger.debug("GUMP", "POSITION_LABEL_ADDED", "Position label added (dynamic)")
            
            self.test_label = API.CreateGumpLabel("Status: Initializing...", hue=0x88)
            self.test_label.SetPos(10, 110)
            self.gump.Add(self.test_label)
            logger.debug("GUMP", "TEST_LABEL_ADDED", "Test label added (dynamic)")
            
            self.status_label = API.CreateGumpLabel("", hue=0x3F)
            self.status_label.SetPos(10, 140)
            self.gump.Add(self.status_label)
            logger.debug("GUMP", "STATUS_LABEL_ADDED", "Status label added (dynamic)")
            
            # Add instructions
            info1 = API.CreateGumpLabel("▶ Try moving this gump!", hue=0x44)
            info1.SetPos(10, 170)
            self.gump.Add(info1)
            
            info2 = API.CreateGumpLabel("▶ Position should be preserved", hue=0x44)
            info2.SetPos(10, 190)
            self.gump.Add(info2)
            
            info3 = API.CreateGumpLabel("▶ Counter updates every second", hue=0x44)
            info3.SetPos(10, 210)
            self.gump.Add(info3)
            logger.debug("GUMP", "INSTRUCTIONS_ADDED", "Instruction labels added")
            
            # Add gump to screen
            API.AddGump(self.gump)
            logger.info("GUMP", "CREATE_COMPLETE", "Gump created and added to screen", {
                "control_count": 8,
                "dynamic_controls": 4
            })
            
            API.SysMsg("Gump Test UI created - Try moving it!", 0x3F)
            
        except Exception as e:
            logger.error("GUMP", "CREATE_FAILED", f"Failed to create gump: {str(e)}", {
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            API.SysMsg(f"ERROR creating gump: {str(e)}", 0x21)
            raise
    
    def update_gump(self):
        """Update gump content WITHOUT recreating it"""
        try:
            # Increment counter
            self.counter += 1
            
            logger.debug("UPDATE", "CYCLE_START", f"Update cycle #{self.counter}")
            
            # Read current gump position
            try:
                current_x = self.gump.X
                current_y = self.gump.Y
                logger.debug("UPDATE", "POSITION_READ", "Current gump position read", {
                    "x": current_x,
                    "y": current_y
                })
            except Exception as e:
                logger.warning("UPDATE", "POSITION_READ_FAIL", f"Could not read position: {str(e)}")
                current_x = "?"
                current_y = "?"
            
            # Update counter label
            counter_text = f"Counter: {self.counter}"
            self.counter_label.Text = counter_text
            logger.debug("UPDATE", "COUNTER_UPDATED", "Counter label updated", {
                "new_text": counter_text,
                "counter": self.counter
            })
            
            # Update position label
            position_text = f"Position: ({current_x}, {current_y})"
            self.position_label.Text = position_text
            logger.debug("UPDATE", "POSITION_UPDATED", "Position label updated", {
                "new_text": position_text
            })
            
            # Update test label with color cycling
            color_cycle = [0x3F, 0x21, 0x44, 0x63, 0x88]  # Green, Red, Yellow, Blue, Gray
            current_color = color_cycle[self.counter % len(color_cycle)]
            test_text = f"Status: Running (cycle {self.counter})"
            self.test_label.Text = test_text
            self.test_label.Hue = current_color
            logger.debug("UPDATE", "TEST_LABEL_UPDATED", "Test label updated with color", {
                "new_text": test_text,
                "hue": hex(current_color)
            })
            
            # Update status with timestamp
            status_text = f"Last update: {datetime.now().strftime('%H:%M:%S')}"
            self.status_label.Text = status_text
            logger.debug("UPDATE", "STATUS_UPDATED", "Status label updated", {
                "new_text": status_text
            })
            
            logger.info("UPDATE", "CYCLE_COMPLETE", f"Update cycle #{self.counter} completed successfully")
            
        except Exception as e:
            logger.error("UPDATE", "UPDATE_FAILED", f"Failed to update gump: {str(e)}", {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "counter": self.counter
            })
            API.SysMsg(f"ERROR updating gump: {str(e)}", 0x21)
    
    def run(self):
        """Main script loop"""
        API.SysMsg("Starting Gump Update Test...", 0x3F)
        logger.info("MAIN", "SCRIPT_START", "Gump test script started", {
            "debug_mode": DEBUG,
            "version": self.version
        })
        
        # Create gump once
        self.create_gump()
        
        while not API.StopRequested:
            try:
                # Update gump content every second
                self.update_gump()
                
                # Check for stop after 30 updates
                if self.counter >= 30:
                    logger.info("MAIN", "AUTO_STOP", "Reached 30 updates, stopping test")
                    API.SysMsg("Test complete (30 updates) - Stopping script", 0x44)
                    break
                
                API.Pause(1.0)  # Update every second
                
            except Exception as e:
                error_msg = str(e)
                error_trace = traceback.format_exc()
                
                API.SysMsg(f"ERROR: {error_msg}", 0x21)
                logger.error("MAIN", "SCRIPT_ERROR", f"Unhandled exception in main loop", {
                    "error": error_msg,
                    "traceback": error_trace,
                    "counter": self.counter
                })
                
                API.Pause(1.0)
    
    def cleanup(self):
        """Cleanup on script exit"""
        logger.info("CLEANUP", "START", "Starting cleanup")
        
        try:
            if self.gump:
                logger.debug("CLEANUP", "DISPOSE_GUMP", "Disposing gump")
                self.gump.Dispose()
                logger.info("CLEANUP", "GUMP_DISPOSED", "Gump disposed successfully")
        except Exception as e:
            logger.error("CLEANUP", "DISPOSE_FAILED", f"Failed to dispose gump: {str(e)}", {
                "error": str(e)
            })
        
        logger.info("CLEANUP", "COMPLETE", "Cleanup finished")
        API.SysMsg("Gump Test - Stopped", 0x21)


# ============================================================================
# ENTRY POINT
# ============================================================================

if TAZUO_API:
    script = None
    try:
        script = GumpTestUI()
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
