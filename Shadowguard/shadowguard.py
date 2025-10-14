# Shadowguard Automation for TazUO
# Inspired by Dorana's Shadowguard script
# Adapted for TazUO by Foruno
# 
# Features:
# - OOP architecture for maintainability
# - Elegant error handling with decorators
# - Optimized Bar room automation
# - Target cursor cleanup to prevent UI freeze
# - Integrated Logger and Gump system

import os
import json
from datetime import datetime
from functools import wraps

try:
    import API
    TAZUO_API = True
except ImportError:
    TAZUO_API = False
    print("WARNING: API not available (expected outside TazUO)")


# ============================================================================
# DEBUG FLAG - Set to True for detailed logging
# ============================================================================
DEBUG = False  # Change to True to enable comprehensive logging


# ============================================================================
# LOGGER CLASS - JSON structured logging with DEBUG flag
# ============================================================================

class ShadowguardLogger:
    """
    JSON structured logger for Shadowguard script.
    Creates logs/ folder if it doesn't exist.
    Logs in JSON Lines format for easy parsing.
    Respects DEBUG flag - no logs written if DEBUG = False.
    """
    
    def __init__(self):
        # Create logs directory if it doesn't exist
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(script_dir, "logs")
        
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except Exception as e:
            if DEBUG:
                print(f"WARNING: Could not create logs directory: {e}")
            self.log_dir = None
    
    def _log_event(self, level, room, event, msg, details=None):
        """Internal method to write log entry (only if DEBUG=True)"""
        if not DEBUG:
            return  # Skip logging if DEBUG is disabled
        
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
            if DEBUG:
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


# Initialize logger globally
logger = ShadowguardLogger()


# ============================================================================
# GUMP MANAGER CLASS - UI system
# ============================================================================

class GumpManager:
    """
    Manages all Gump UI elements for Shadowguard script.
    
    Architecture:
    - Main Gump: Created ONCE, never recreated
    - Controls: Store references and update properties dynamically
    - NO recreation = NO flicker, position preserved
    """
    
    def __init__(self, version="0.4.3"):
        self.version = version
        self.running_master = True
        
        # Gump positioning
        self.gump_x = 15
        self.gump_y = 30
        self.gump_width = 350
        self.gump_base_height = 100  # Base info section
        self.gump_timer_height = 40   # Timer section
        self.gump_room_height = 80    # Room-specific section
        
        # Colors (hues) - Using high contrast colors
        self.hue_info = 0x5F  # Cyan for labels
        self.hue_active_info = 0x3F  # Bright green for active data
        self.hue_active_warning = 0x21  # Bright red for warnings
        
        # Background colors
        self.bg_color = "#2D2D2D"  # Darker gray background
        self.bg_opacity = 0.85  # Higher opacity for better readability
        
        # Current state
        self.current_room = "Unknown"
        self.room_entry_time = None
        self.gump = None
        self.gump_created = False
        
        # Control references (stored for dynamic updates)
        self.ctrl_room_value = None
        self.ctrl_status_value = None
        self.ctrl_timer_label = None
        self.ctrl_timer_bg = None
        self.ctrl_timer_fill = None
        self.ctrl_time_value = None
        
        # Bar room controls
        self.ctrl_bar_line1 = None
        self.ctrl_bar_line2 = None
        self.ctrl_bar_count = None
        self.ctrl_bar_bottle_graphic = None  # Bottle graphic item
        self.bar_section_visible = False
    
    def create_main_gump(self, room_name, room_entry_time=None, extra_data=None):
        """
        Create the main Gump ONCE with all possible controls.
        After creation, only update_gump_data() should be called.
        
        Args:
            room_name: Name of current room
            room_entry_time: datetime when room was entered (None for Lobby)
            extra_data: Room-specific data dict (for Bar, Fountain, etc)
        """
        if not TAZUO_API:
            return None
        
        # Only create once
        if self.gump_created and self.gump:
            return self.gump
        
        try:
            # Fixed total height for all rooms (max size)
            total_height = self.gump_base_height + self.gump_timer_height + self.gump_room_height
            
            # Create new gump (acceptMouseInput=True to allow moving, canMove=True, keepOpen=False)
            self.gump = API.CreateGump(acceptMouseInput=True, canMove=True, keepOpen=False)
            self.gump.SetRect(self.gump_x, self.gump_y, self.gump_width, total_height)
            
            # === BACKGROUND ===
            # Main background - dark with high opacity
            bg = API.CreateGumpColorBox(opacity=self.bg_opacity, color=self.bg_color)
            bg.SetRect(0, 0, self.gump_width, total_height)
            self.gump.Add(bg)
            
            # === HEADER ===
            # Title: "Shadowguard by Foruno"
            header_label = API.CreateGumpLabel("Shadowguard by Foruno", self.hue_info)
            header_label.SetPos(15, 15)
            self.gump.Add(header_label)
            
            # === CURRENT ROOM ===
            room_label = API.CreateGumpLabel("Current Room:", self.hue_info)
            room_label.SetPos(15, 40)
            self.gump.Add(room_label)
            
            # Store reference for dynamic updates
            self.ctrl_room_value = API.CreateGumpLabel(room_name, self.hue_active_info)
            self.ctrl_room_value.SetPos(105, 40)
            self.gump.Add(self.ctrl_room_value)
            
            # === RUNNING STATUS ===
            running_label = API.CreateGumpLabel("Running:", self.hue_info)
            running_label.SetPos(260, 15)
            self.gump.Add(running_label)
            
            # Store reference for dynamic updates
            status_text = "Yes" if self.running_master else "No"
            self.ctrl_status_value = API.CreateGumpLabel(status_text, self.hue_active_info)
            self.ctrl_status_value.SetPos(320, 15)
            self.gump.Add(self.ctrl_status_value)
            
            # === VERSION ===
            version_label = API.CreateGumpLabel(f"Version: {self.version}", self.hue_info)
            version_label.SetPos(260, 75)
            self.gump.Add(version_label)
            
            # === ROOM TIMER (create controls hidden, shown dynamically) ===
            # Timer label (starts empty)
            self.ctrl_timer_label = API.CreateGumpLabel("", self.hue_info)
            self.ctrl_timer_label.SetPos(15, 65)
            self.gump.Add(self.ctrl_timer_label)
            
            # Timer bar background (dark) - starts hidden (width 0)
            self.ctrl_timer_bg = API.CreateGumpColorBox(opacity=0.8, color="#000000")
            self.ctrl_timer_bg.SetRect(95, 69, 0, 11)  # Width 0 = hidden
            self.gump.Add(self.ctrl_timer_bg)
            
            # Timer bar fill (green progress) - starts hidden (width 0)
            self.ctrl_timer_fill = API.CreateGumpColorBox(opacity=0.9, color="#00FF00")
            self.ctrl_timer_fill.SetRect(95, 69, 0, 11)  # Width 0 = hidden
            self.gump.Add(self.ctrl_timer_fill)
            
            # Time remaining text (starts empty)
            self.ctrl_time_value = API.CreateGumpLabel("", self.hue_active_info)
            self.ctrl_time_value.SetPos(210, 65)
            self.gump.Add(self.ctrl_time_value)
            
            # === BAR ROOM SECTION (create all controls hidden, shown dynamically) ===
            margin_top = self.gump_base_height + self.gump_timer_height
            
            # Background for Bar section
            bar_bg = API.CreateGumpColorBox(opacity=self.bg_opacity, color="#151515")
            bar_bg.SetRect(0, margin_top, self.gump_width, 80)
            self.gump.Add(bar_bg)
            
            # Status line 1 (starts empty)
            self.ctrl_bar_line1 = API.CreateGumpLabel("", self.hue_active_info)
            self.ctrl_bar_line1.SetPos(15, 15 + margin_top)
            self.gump.Add(self.ctrl_bar_line1)
            
            # Status line 2 (starts empty)
            self.ctrl_bar_line2 = API.CreateGumpLabel("", self.hue_active_info)
            self.ctrl_bar_line2.SetPos(15, 40 + margin_top)
            self.gump.Add(self.ctrl_bar_line2)
            
            # Bottle item graphic (starts hidden - width 0, height 0)
            self.ctrl_bar_bottle_graphic = API.CreateGumpItemPic(0x099B, 0, 0)  # Width/height 0 = hidden
            self.ctrl_bar_bottle_graphic.SetPos(250, 15 + margin_top)
            self.gump.Add(self.ctrl_bar_bottle_graphic)
            
            # Bottle count (starts empty)
            self.ctrl_bar_count = API.CreateGumpLabel("", self.hue_active_info)
            self.ctrl_bar_count.SetPos(285, 15 + margin_top)
            self.gump.Add(self.ctrl_bar_count)
            
            # === SEND GUMP TO CLIENT ===
            API.AddGump(self.gump)
            self.gump_created = True
            
            # Now update with current data
            self.update_gump_data(room_name, room_entry_time, extra_data)
            
            return self.gump
            
        except Exception as e:
            logger.error("GUMPS", "CREATE_ERROR", f"Failed to create gump: {e}")
            return None
    
    def update_gump_data(self, room_name, room_entry_time=None, extra_data=None):
        """
        Update gump data WITHOUT recreating it.
        Uses control references to update Text and Hue properties.
        
        Args:
            room_name: Name of current room
            room_entry_time: datetime when room was entered (None for Lobby)
            extra_data: Room-specific data dict (for Bar, Fountain, etc)
        """
        if not TAZUO_API or not self.gump_created or not self.gump:
            return
        
        try:
            # Update room name
            if self.ctrl_room_value:
                self.ctrl_room_value.Text = room_name
            
            # Update running status
            if self.ctrl_status_value:
                status_text = "Yes" if self.running_master else "No"
                self.ctrl_status_value.Text = status_text
            
            # === TIMER SECTION (ALL rooms except Lobby) ===
            if room_name != "Lobby" and room_entry_time:
                # SHOW timer elements
                seconds_elapsed = int((datetime.now() - room_entry_time).total_seconds())
                time_left = max(0, 1800 - seconds_elapsed)  # 30 min = 1800 sec
                
                if time_left > 0:
                    fraction = time_left / 1800.0
                    
                    # Show timer label
                    if self.ctrl_timer_label:
                        self.ctrl_timer_label.Text = "Room Timer:"
                    
                    # Show timer background bar (full width)
                    if self.ctrl_timer_bg:
                        self.ctrl_timer_bg.SetWidth(109)
                    
                    # Update timer bar fill width
                    fill_width = int(fraction * 109)
                    if self.ctrl_timer_fill:
                        self.ctrl_timer_fill.SetWidth(fill_width if fill_width > 0 else 0)
                    
                    # Update time text (MM:SS)
                    minutes = time_left // 60
                    seconds = time_left % 60
                    time_string = f"{minutes}:{seconds:02d}"
                    if self.ctrl_time_value:
                        self.ctrl_time_value.Text = time_string
                else:
                    # Time expired - show 00:00
                    if self.ctrl_timer_label:
                        self.ctrl_timer_label.Text = "Room Timer:"
                    if self.ctrl_timer_bg:
                        self.ctrl_timer_bg.SetWidth(109)
                    if self.ctrl_timer_fill:
                        self.ctrl_timer_fill.SetWidth(0)
                    if self.ctrl_time_value:
                        self.ctrl_time_value.Text = "00:00"
            else:
                # HIDE timer (Lobby or no entry time)
                if self.ctrl_timer_label:
                    self.ctrl_timer_label.Text = ""
                if self.ctrl_timer_bg:
                    self.ctrl_timer_bg.SetWidth(0)  # Hide background bar
                if self.ctrl_timer_fill:
                    self.ctrl_timer_fill.SetWidth(0)
                if self.ctrl_time_value:
                    self.ctrl_time_value.Text = ""
            
            # === BAR ROOM SECTION ===
            if room_name == "Bar" and extra_data:
                # SHOW bar section
                lines = extra_data.get('lines', ["Run close to bottles", "Throw at pirates"])
                warning = extra_data.get('warning', False)
                hue = self.hue_active_warning if warning else self.hue_active_info
                
                # Update line 1
                if self.ctrl_bar_line1:
                    self.ctrl_bar_line1.Text = lines[0] if len(lines) > 0 else ""
                    self.ctrl_bar_line1.Hue = hue
                
                # Update line 2
                if self.ctrl_bar_line2:
                    self.ctrl_bar_line2.Text = lines[1] if len(lines) > 1 else ""
                    self.ctrl_bar_line2.Hue = hue
                
                # Show bottle graphic (restore size)
                if self.ctrl_bar_bottle_graphic:
                    self.ctrl_bar_bottle_graphic.SetWidth(40)
                    self.ctrl_bar_bottle_graphic.SetHeight(40)
                
                # Update bottle count
                bottle_count = extra_data.get('bottle_count', 0)
                if self.ctrl_bar_count:
                    self.ctrl_bar_count.Text = str(bottle_count)
                
                self.bar_section_visible = True
            else:
                # HIDE bar section
                if self.ctrl_bar_line1:
                    self.ctrl_bar_line1.Text = ""
                if self.ctrl_bar_line2:
                    self.ctrl_bar_line2.Text = ""
                
                # Hide bottle graphic (set size to 0)
                if self.ctrl_bar_bottle_graphic:
                    self.ctrl_bar_bottle_graphic.SetWidth(0)
                    self.ctrl_bar_bottle_graphic.SetHeight(0)
                
                if self.ctrl_bar_count:
                    self.ctrl_bar_count.Text = ""
                
                self.bar_section_visible = False
            
        except Exception as e:
            logger.error("GUMPS", "UPDATE_ERROR", f"Failed to update gump data: {e}")
    
    def update_gump(self, room_name, room_entry_time=None, extra_data=None):
        """
        Update the gump with new data.
        Creates gump if not exists, otherwise just updates data.
        """
        self.current_room = room_name
        self.room_entry_time = room_entry_time
        
        # Create gump if not created yet
        if not self.gump_created:
            return self.create_main_gump(room_name, room_entry_time, extra_data)
        
        # Otherwise just update the data (no recreation)
        self.update_gump_data(room_name, room_entry_time, extra_data)
    
    def close_gump(self):
        """Close the current gump"""
        if not TAZUO_API:
            return
        
        try:
            if self.gump:
                self.gump.Dispose()
                self.gump = None
        except Exception as e:
            logger.error("GUMPS", "CLOSE_ERROR", f"Failed to close gump: {e}")


# Elegant decorator to automatically capture errors
def log_errors(room_name):
    """Decorator to automatically log errors without cluttering code"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(room_name, "ERROR", f"Error in {func.__name__}: {str(e)}", {
                    "exception_type": type(e).__name__,
                    "function": func.__name__
                })
                API.Pause(1)
                # Return safe defaults
                if 'is_' in func.__name__:
                    return False
                return None
        return wrapper
    return decorator


class Shadowguard:
    """
    Shadowguard automation script - Phase 1 (Lobby + Bar)
    
    Error Handling Strategy:
    - @log_errors decorator automatically captures errors in critical methods
    - Entry point has global try/catch for fatal errors
    - Clean code without try/catch everywhere
    """
    
    def __init__(self):
        self.version = "0.4.3"  # Alpha - Bar room + Dynamic Gumps + DEBUG flag system
        self.running_master = True
        self.current_room = None
        self.room_entry_time = None
        
        # Show DEBUG status
        if DEBUG:
            API.SysMsg("DEBUG MODE ENABLED - Logging to logs/shadowguard-YYYYMMDD.log", 0x44)
        
        # Room types
        self.ROOM_UNKNOWN = 0
        self.ROOM_LOBBY = 1
        self.ROOM_BAR = 2
        
        # Bar room counters
        self.bottle_id = 0x099B  # Liquor bottle graphic ID
        self.bottles_thrown = 0
        self.bottles_picked = 0
        
        # Initialize Gump Manager
        self.gump_manager = None
        try:
            self.gump_manager = GumpManager(version=self.version)
        except Exception as e:
            logger.warning("MAIN", "GUMP_INIT_FAILED", f"Failed to init gumps: {e}")
        
    def run(self):
        """Main script loop"""
        
        while not API.StopRequested:
            # Detect current room
            new_room = self.get_current_room()
            
            # Update entry time if room changed
            if new_room != self.current_room:
                self.current_room = new_room
                self.room_entry_time = datetime.now()
                room_name = self.get_room_name()
                API.SysMsg(f"Room: {room_name}", 65)  # Green message
                logger.info("MAIN", "ROOM_CHANGE", f"Entered {room_name}")
                
                # Reset counters on room change
                if new_room == self.ROOM_BAR:
                    self.bottles_thrown = 0
                    self.bottles_picked = 0
                
                # Update gump on room change
                self.update_gump()
            
            # Handle current room logic
            if self.running_master:
                if self.current_room == self.ROOM_BAR:
                    self.handle_bar()
                elif self.current_room == self.ROOM_LOBBY:
                    self.handle_lobby()
                else:
                    API.Pause(1)
            else:
                API.Pause(1)
    
    @log_errors("DETECT")
    def get_current_room(self):
        """Detect which room we're currently in"""
        # Check for Bar first (more specific)
        if self.is_bar():
            return self.ROOM_BAR
        
        # Check for Lobby
        if self.is_lobby():
            return self.ROOM_LOBBY
        
        return self.ROOM_UNKNOWN
    
    @log_errors("BAR")
    def is_bar(self):
        """Check if we're in the Bar room"""
        # Check for bottles in range (tables/ground)
        bottles = API.FindTypeAll(self.bottle_id, range=25)
        
        if bottles:
            # Verify it's a liquor bottle by name
            for bottle in bottles[:3]:
                name = (getattr(bottle, 'Name', '') or '').lower()
                if 'bottle' in name and 'liquor' in name:
                    return True
        
        # Check for pirates (murderer notoriety)
        mobiles = API.GetAllMobiles(distance=25, notoriety=[API.Notoriety.Murderer])
        
        if mobiles:
            return True
        
        return False
    
    @log_errors("LOBBY")
    def is_lobby(self):
        """Check if we're in the Lobby"""
        items = API.GetItemsOnGround(30)
        if not items:
            return False
        
        has_crystal_ball = False
        has_ankh = False
        
        for item in items:
            name = (getattr(item, 'Name', '') or '').lower()
            if 'crystal ball' in name:
                has_crystal_ball = True
            elif 'ankh' in name:
                has_ankh = True
            
            if has_crystal_ball and has_ankh:
                return True
        
        return False
    
    def get_room_name(self):
        """Get the name of the current room"""
        if self.current_room == self.ROOM_LOBBY:
            return "Lobby"
        elif self.current_room == self.ROOM_BAR:
            return "Bar"
        else:
            return "Unknown"
    
    @log_errors("BAR")
    def handle_bar(self):
        """Handle Bar room automation"""
        # Update gump every 1 second (real time)
        if not hasattr(self, '_last_gump_update'):
            self._last_gump_update = datetime.now()
        
        seconds_since_update = (datetime.now() - self._last_gump_update).total_seconds()
        if seconds_since_update >= 1.0:
            self.update_gump()
            self._last_gump_update = datetime.now()
        
        # Cancel any leftover target cursor (single check at start, like C# approach)
        if API.HasTarget():
            API.CancelTarget()
        
        # Health check - show warning message and update gump (like C# version)
        if API.Player.Hits < 35:
            API.SysMsg("Heal thyself!", 0x21)  # Red warning message
            
            # Update gump with warning messages (like C# version)
            bottle_count = 0
            backpack_bottles = API.FindTypeAll(self.bottle_id, API.Backpack)
            if backpack_bottles:
                for bottle in backpack_bottles:
                    bottle_count += getattr(bottle, 'Amount', 1)
            
            extra_data = {
                'lines': ["Low Health Detected", "Heal thyself!"],
                'bottle_count': bottle_count,
                'warning': True  # Activates red color in gump
            }
            
            self.gump_manager.update_gump(
                room_name="Bar",
                room_entry_time=self.room_entry_time,
                extra_data=extra_data
            )
            
            API.Pause(5)
            return  # Note: Keep return to avoid throwing bottles while low HP
        
        # Find bottles: prioritize tables over backpack
        backpack_bottle = API.FindType(self.bottle_id, API.Backpack)
        table_bottles = API.FindTypeAll(self.bottle_id, range=2)
        
        use_bottle = None
        table_bottle = None
        
        if table_bottles:
            table_bottle = table_bottles[0]
            use_bottle = table_bottle
        elif backpack_bottle:
            use_bottle = backpack_bottle
        
        if not use_bottle:
            API.Pause(0.6)
            return
        
        # Find enemies (pirates)
        enemies = API.GetAllMobiles(distance=6, notoriety=[API.Notoriety.Murderer])
        
        if not enemies:
            # No enemies: pickup table bottle if available
            if table_bottle:
                container = getattr(table_bottle, 'Container', None)
                if container != API.Backpack:
                    API.MoveItem(table_bottle.Serial, API.Backpack, 1)
                    self.bottles_picked += 1
                    API.Pause(0.2)
                    return
            
            API.Pause(0.6)
            return
        
        # Target enemy with lowest HP (skip invulnerable)
        target = None
        for enemy in sorted(enemies, key=lambda e: getattr(e, 'Hits', 99999)):
            flags = getattr(enemy, 'Flags', '')
            if 'Invulnerable' not in str(flags):
                target = enemy
                break
        
        if not target:
            API.Pause(0.6)
            return
        
        target_name = getattr(target, 'Name', 'Unknown')
        
        # Throw bottle at target (removed redundant cursor check - already done at start)
        API.UseObject(use_bottle.Serial)
        
        # WaitForTarget: optimized to 150ms like C# version (0.15s)
        if API.WaitForTarget(timeout=0.15):
            API.Pause(0.05)
            API.Target(target.Serial)
            self.bottles_thrown += 1
        else:
            # Target cursor didn't appear - cancel and continue
            if API.HasTarget():
                API.CancelTarget()
        
        # Pickup table bottle after throwing
        if table_bottle:
            container = getattr(table_bottle, 'Container', None)
            if container != API.Backpack:
                API.MoveItem(table_bottle.Serial, API.Backpack, 1)
                self.bottles_picked += 1
                API.Pause(0.2)
        
        API.Pause(0.6)
    
    def handle_lobby(self):
        """Handle Lobby room"""
        API.Pause(2)
    
    @log_errors("GUMPS")
    def update_gump(self):
        """Update the gump with current room data"""
        if not self.gump_manager:
            return
        
        room_name = self.get_room_name()
        extra_data = None
        
        # Prepare room-specific data
        if self.current_room == self.ROOM_BAR:
            # Count bottles in backpack
            bottle_count = 0
            backpack_bottles = API.FindTypeAll(self.bottle_id, API.Backpack)
            if backpack_bottles:
                for bottle in backpack_bottles:
                    bottle_count += getattr(bottle, 'Amount', 1)
            
            extra_data = {
                'lines': [
                    "Run close to bottles",
                    "Bottles thrown at pirates automatically"
                ],
                'bottle_count': bottle_count,
                'warning': API.Player.Hits < 35
            }
        
        # Update gump
        self.gump_manager.update_gump(
            room_name=room_name,
            room_entry_time=self.room_entry_time,
            extra_data=extra_data
        )
    
    @log_errors("MAIN")
    def cleanup(self):
        """Cleanup on script exit"""
        if API.HasTarget():
            API.CancelTarget()
        
        # Close gump
        if self.gump_manager:
            self.gump_manager.close_gump()
        
        logger.info("MAIN", "CLEANUP", "Script stopped", {
            "bottles_picked": self.bottles_picked,
            "bottles_thrown": self.bottles_thrown,
            "final_room": self.get_room_name()
        })


# Script entry point
try:
    sg = Shadowguard()
    sg.run()
except KeyboardInterrupt:
    pass  # Silent stop on user interrupt
except Exception as e:
    logger.error("MAIN", "FATAL_ERROR", f"Unhandled error: {str(e)}", {
        "exception_type": type(e).__name__
    })
finally:
    try:
        if 'sg' in locals():
            sg.cleanup()
    except:
        pass