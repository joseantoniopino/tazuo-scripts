# Gump Manager - Dynamic Gump UI Controller
# Handles zone selection and session tracking gumps

import traceback
import time
import os
import sys
from datetime import datetime

# Try to import shared UI theme (agnostic)
THEME = None
try:
    # Attempt import from parent 'public' folder
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    import ui_theme as THEME  # type: ignore
except Exception:
    THEME = None


class GumpManager:
    """Manages gump UI for GoldTracker"""
    
    def __init__(self, api, logger=None, debug=False):
        self.api = api  # API reference passed from main script
        self.logger = logger
        self.debug = debug
        self.zone_gump = None
        self.session_gump = None
        self.controls = {}
        
        # Summary gump references
        self.summary_gump = None
        self.summary_save_clicked = False
        self.summary_discard_clicked = False
        
        # Button click flags (set by callbacks)
        self.start_button_clicked = False
        self.stop_button_clicked = False
        self.pause_button_clicked = False
        self.cancel_button_clicked = False
        self.adjust_button_clicked = False
        self.minimize_button_clicked = False
        
        # Gump display state
        self.minimized = False
        self.current_zone = None
        
        # Zone filtering state
        self.all_zones = {}  # {zone_name: [aliases]}
        self.filtered_zones = []  # Currently visible zones
        self.last_filter_text = ""
        
        # Color scheme and palette (from shared theme if available)
        if THEME:
            self.HUE_PRIMARY = THEME.HUES.PRIMARY
            self.HUE_SUCCESS = THEME.HUES.SUCCESS
            self.HUE_DANGER = THEME.HUES.DANGER
            self.HUE_WARNING = THEME.HUES.WARNING
            self.HUE_MUTED = THEME.HUES.MUTED
            self.HUE_CYAN = getattr(THEME.HUES, 'CYAN', THEME.HUES.PRIMARY)
            self.TITLE_HUE = THEME.HUES.TITLE
            self.COLOR_BG = THEME.background_color()
            self.COLOR_HEADER = THEME.header_color()
            self.COLOR_SEPARATOR = THEME.separator_color()
        else:
            # Fallbacks
            self.HUE_PRIMARY = 0x0058   # blue for primary actions (Finish)
            self.HUE_SUCCESS = 0x0044   # green
            self.HUE_DANGER = 0x0021    # red
            self.HUE_WARNING = 0x0035   # yellow
            self.HUE_MUTED = 0x003F     # muted/white-ish
            self.HUE_CYAN = 0x005A      # cyan-like text (lighter)
            self.TITLE_HUE = 0x0481     # blue-ish
            self.COLOR_BG = "#0f172a"   # deep background
            self.COLOR_HEADER = "#1e40af"  # blue accent fallback (darker)
            self.COLOR_SEPARATOR = "#374151"
        
        # Blink state for paused timer
        self._blink_on = False
        self._last_blink_toggle = 0.0
        self._blink_interval = 0.5  # seconds
        
        # Finalization state (to avoid recreating session gump after Finish)
        self.finalizing = False

        # Dispose handling flags (event-driven recreation)
        self._suppress_dispose_handlers = False
        self._zone_disposed = False
        self._session_disposed = False
        self._mini_disposed = False
        self._summary_disposed = False
        self._modal_disposed = False
        # Public flag used by gold_tracker summary loop
        self.summary_disposed = False
        # Creation guard to prevent duplicate builds during race conditions
        self._creating_session_gump = False

        # Creation timestamps to avoid immediate double-creation after events
        self._last_session_create = 0.0
        
        # Global suppression window to avoid any recreation races (in seconds)
        self._recreate_suppressed_until = 0.0
        
        # Track created gump instances to guarantee full disposal on Finish/cleanup
        # This protects against rare duplicate creations after minimize/expand races
        self._session_gump_instances = []
        self._mini_gump_instances = []
        
        if self.debug:
            print("[GumpManager] Initialized")
    
    def create_zone_selection_gump(self, zones_dict):
        """
        Create zone selection gump with dynamic filtering
        zones_dict: {zone_name: [aliases]}
        """
        try:
            if self.debug:
                print(f"[GumpManager] Creating zone selection gump with {len(zones_dict)} zones")
            
            # Store zones and initialize filter
            self.all_zones = zones_dict
            self.filtered_zones = list(zones_dict.keys())  # Show all initially
            
            # Create gump structure
            gump_width = 500
            gump_height = 450  # Fixed height for scrollable area
            self.zone_gump = self.api.CreateGump(acceptMouseInput=True, canMove=True, keepOpen=False)
            self.zone_gump.SetRect(0, 0, gump_width, gump_height)
            try:
                if hasattr(self.zone_gump, 'CanCloseWithRightClick'):
                    self.zone_gump.CanCloseWithRightClick = False
            except Exception:
                pass
            self.zone_gump.CenterXInViewPort()
            self.zone_gump.CenterYInViewPort()
            
            # Background
            bg = self.api.CreateGumpColorBox(0.9, self.COLOR_BG)
            bg.SetRect(0, 0, gump_width, gump_height)
            self.zone_gump.Add(bg)
            self.controls["background"] = bg
            # Accent header bar
            header = self.api.CreateGumpColorBox(1.0, self.COLOR_HEADER)
            header.SetRect(0, 0, gump_width, 8)
            self.zone_gump.Add(header)
            
            # Title
            title = self.api.CreateGumpLabel("GoldTracker - Select Zone", self.TITLE_HUE)
            title.SetPos(gump_width // 2 - 100, 20)
            self.zone_gump.Add(title)
            self.controls["title"] = title
            
            # Filter textbox (at top)
            filter_label = self.api.CreateGumpLabel("Type to filter zones, or enter new zone name:", self.HUE_PRIMARY)
            filter_label.SetPos(30, 55)
            self.zone_gump.Add(filter_label)
            self.controls["filter_label"] = filter_label
            
            filter_textbox = self.api.CreateGumpTextBox("", width=380, height=30)
            filter_textbox.SetPos(30, 80)
            self.zone_gump.Add(filter_textbox)
            self.controls["filter_input"] = filter_textbox
            
            # Scroll area for radio buttons
            scroll_area = self.api.CreateGumpScrollArea(30, 120, 440, 230)
            self.zone_gump.Add(scroll_area)
            self.controls["scroll_area"] = scroll_area
            
            # Create initial radio buttons (no selection by default)
            self._rebuild_zone_list()
            
            # Start button
            start_btn = self.api.CreateSimpleButton("Start Session", 150, 35)
            start_btn.SetPos(175, 370)
            self.zone_gump.Add(start_btn)
            start_btn.Hue = self.HUE_PRIMARY
            self.controls["start_button"] = start_btn
            
            # Start button callback
            def on_start_click():
                self.start_button_clicked = True
                if self.debug:
                    print("[GumpManager] Start button clicked")
            
            self.api.AddControlOnClick(start_btn, on_start_click)
            
            # Instructions label
            instructions = self.api.CreateGumpLabel("List filters as you type. Click zone to auto-fill.", self.HUE_CYAN)
            instructions.SetPos(65, 410)
            self.zone_gump.Add(instructions)
            self.controls["instructions"] = instructions
            
            # Register dispose callback (event-driven)
            try:
                def _on_zone_disposed():
                    if self._suppress_dispose_handlers:
                        return
                    self._zone_disposed = True
                    if self.logger:
                        self.logger.warning("GUMP", "ZONE_DISPOSED", "Zone selection gump disposed")
                self.api.AddControlOnDisposed(self.zone_gump, _on_zone_disposed)
            except Exception:
                pass

            self.api.AddGump(self.zone_gump)
            
            if self.debug:
                print("[GumpManager] Zone selection gump created with filtering")
            
            if self.logger:
                self.logger.info("GUMP", "ZONE_SELECTION_CREATED", 
                               f"Created gump with {len(zones_dict)} zones")
            
            return True
            
        except Exception as e:
            if self.debug:
                print(f"[GumpManager] ERROR creating zone gump: {e}")
                traceback.print_exc()
            
            if self.logger:
                self.logger.error("GUMP", "ZONE_GUMP_ERROR", str(e), {
                    "traceback": traceback.format_exc()
                })
            return False
    
    def _filter_zones(self, query):
        """
        Filter zones by query (searches in zone name and aliases)
        Returns list of matching zone names
        """
        # Only log final result, not every match (reduces spam during typing)
        if not query or query.strip() == "":
            return list(self.all_zones.keys())
        
        query_lower = query.lower().strip()
        matches = []
        
        for zone_name, aliases in self.all_zones.items():
            # Search in zone name
            if query_lower in zone_name.lower():
                matches.append(zone_name)
                continue
            
            # Search in aliases
            if any(query_lower in alias.lower() for alias in aliases):
                matches.append(zone_name)
        
        # Only log final result (not every keystroke)
        if self.logger and len(matches) <= 3:  # Only log when narrowed down
            self.logger.debug("GUMP", "FILTER_RESULT", f"Query '{query}' → {len(matches)} match(es)", {
                "matches": matches
            })
        
        return matches
    
    def _rebuild_zone_list(self):
        """
        Build radio buttons in scroll area for initial gump creation
        Called only during create_zone_selection_gump
        """
        try:
            scroll_area = self.controls.get("scroll_area")
            if not scroll_area:
                if self.debug:
                    print("[GumpManager] No scroll area found for rebuild")
                return
            
            # Add radio buttons for filtered zones
            self.controls["zone_radios"] = []
            y_pos = 5
            
            if self.logger:
                self.logger.debug("GUMP", "CREATE_RADIOS_START", f"Creating {len(self.filtered_zones)} radio buttons", {
                    "zones": self.filtered_zones[:5]  # First 5
                })
            
            for i, zone_name in enumerate(self.filtered_zones):
                # Create radio button (NO default selection)
                radio = self.api.CreateGumpRadioButton(zone_name, group=1, isChecked=False)
                radio.SetPos(10, y_pos)
                scroll_area.Add(radio)
                
                # Store radio with zone name
                self.controls["zone_radios"].append({
                    "control": radio,
                    "zone_name": zone_name
                })
                
                # Add callback to fill textbox when clicked (no logging spam)
                def make_radio_callback(zone):
                    def on_radio_click():
                        # Fill textbox with zone name (silently)
                        if "filter_input" in self.controls:
                            try:
                                if hasattr(self.controls["filter_input"], "SetText"):
                                    self.controls["filter_input"].SetText(zone)
                                elif hasattr(self.controls["filter_input"], "Clear"):
                                    self.controls["filter_input"].Clear()
                                    for char in zone:
                                        self.controls["filter_input"].OnTextInput(char)
                            except Exception as e:
                                if self.logger:
                                    self.logger.error("GUMP", "INPUT_FILL_ERROR", str(e))
                    return on_radio_click
                
                self.api.AddControlOnClick(radio, make_radio_callback(zone_name))
                
                y_pos += 25
            
            # Only log if significant (not every rebuild)
            if self.logger and len(self.filtered_zones) <= 3:
                self.logger.debug("GUMP", "RADIO_REBUILD", f"Showing {len(self.filtered_zones)} zone(s)")
        
        except Exception as e:
            if self.debug:
                print(f"[GumpManager] ERROR building zone list: {e}")
                traceback.print_exc()
    
    def update_zone_filter(self, query):
        """
        Update zone filter and rebuild radio button list
        Clears and recreates scroll area content (NOT the whole gump)
        """
        try:
            if self.logger:
                self.logger.debug("GUMP", "FILTER_UPDATE_START", f"Query: '{query}'", {
                    "old_filter": self.last_filter_text,
                    "old_filtered_count": len(self.filtered_zones)
                })
            
            # Filter zones
            old_filtered = self.filtered_zones[:]
            self.filtered_zones = self._filter_zones(query)
            
            # Store last filter
            self.last_filter_text = query
            
            if self.logger:
                self.logger.debug("GUMP", "FILTER_UPDATE_COMPLETE", f"Matches: {len(self.filtered_zones)}", {
                    "query": query,
                    "old_count": len(old_filtered),
                    "new_count": len(self.filtered_zones),
                    "filtered_zones": self.filtered_zones[:5]  # First 5 for debugging
                })
            
            # Rebuild the radio button list in scroll area (silently)
            if "scroll_area" in self.controls:
                # Safely dispose previous radio controls (no Clear() on PyScrollArea)
                try:
                    prev_radios = self.controls.get("zone_radios", []) or []
                    for entry in prev_radios:
                        try:
                            ctrl = entry.get("control") if isinstance(entry, dict) else None
                            if ctrl and hasattr(ctrl, "Dispose"):
                                ctrl.Dispose()
                        except Exception:
                            pass
                except Exception:
                    pass
                # Reset stored radios
                self.controls["zone_radios"] = []
                
                # Rebuild radio buttons
                y_pos = 0
                for i, zone_name in enumerate(self.filtered_zones):
                    # Create radio button
                    radio = self.api.CreateGumpRadioButton(zone_name, group=1, isChecked=False)
                    radio.SetPos(10, y_pos)
                    self.controls["scroll_area"].Add(radio)
                    
                    # Store radio with zone name
                    self.controls["zone_radios"].append({
                        "control": radio,
                        "zone_name": zone_name
                    })
                    
                    # Add callback to fill textbox when clicked
                    def make_radio_callback(zone):
                        def on_radio_click():
                            if self.logger:
                                self.logger.debug("GUMP", "RADIO_CLICKED", f"Zone: {zone}")
                            
                            # Fill textbox with zone name
                            if "filter_input" in self.controls:
                                try:
                                    # Try SetText() method first
                                    if hasattr(self.controls["filter_input"], "SetText"):
                                        self.controls["filter_input"].SetText(zone)
                                        if self.logger:
                                            self.logger.debug("GUMP", "INPUT_FILLED", f"Input filled with SetText(): {zone}")
                                    # Try Clear + type simulation (if available)
                                    elif hasattr(self.controls["filter_input"], "Clear"):
                                        self.controls["filter_input"].Clear()
                                        # Simulate typing each character
                                        for char in zone:
                                            self.controls["filter_input"].OnTextInput(char)
                                        if self.logger:
                                            self.logger.debug("GUMP", "INPUT_FILLED", f"Input filled with OnTextInput(): {zone}")
                                    else:
                                        if self.logger:
                                            self.logger.warning("GUMP", "NO_SET_METHOD", f"No SetText or Clear method found. Available methods: {dir(self.controls['filter_input'])}")
                                except Exception as e:
                                    if self.logger:
                                        self.logger.error("GUMP", "INPUT_FILL_ERROR", str(e), {
                                            "zone": zone,
                                            "traceback": traceback.format_exc()
                                        })
                            else:
                                if self.logger:
                                    self.logger.error("GUMP", "NO_INPUT_CONTROL", "filter_input not found in controls")
                        return on_radio_click
                    
                    self.api.AddControlOnClick(radio, make_radio_callback(zone_name))
                    
                    y_pos += 25
        
        except Exception as e:
            if self.debug:
                print(f"[GumpManager] ERROR updating filter: {e}")
                traceback.print_exc()
            
            if self.logger:
                self.logger.error("GUMP", "FILTER_UPDATE_ERROR", str(e), {
                    "traceback": traceback.format_exc()
                })
    
    def get_selected_zone(self):
        """
        Get the selected zone from UI
        ONLY reads from textbox input - radio buttons just fill the textbox
        Returns: (zone_name, exists_in_zones_json)
        """
        # Check if filter_input control exists (no log spam)
        if "filter_input" not in self.controls:
            if self.logger:
                self.logger.error("GUMP", "NO_INPUT_CONTROL", "filter_input not in controls")
            return (None, False)
        
        # Get text from textbox
        try:
            text = self.controls["filter_input"].Text.strip()
        except Exception as e:
            if self.logger:
                self.logger.error("GUMP", "INPUT_READ_ERROR", str(e))
            return (None, False)
        
        if not text:
            return (None, False)
        
        # Check exact match (case-insensitive)
        for zone_name in self.all_zones.keys():
            if text.lower() == zone_name.lower():
                if self.logger:
                    self.logger.info("GUMP", "ZONE_SELECTED", f"Selected: {zone_name}")
                return (zone_name, True)
        
        # Check alias match
        for zone_name, aliases in self.all_zones.items():
            if text.lower() in [a.lower() for a in aliases]:
                if self.logger:
                    self.logger.info("GUMP", "ZONE_SELECTED", f"Selected: {zone_name} (via alias '{text}')")
                return (zone_name, True)
        
        # Not found - new zone
        if self.logger:
            self.logger.info("GUMP", "NEW_ZONE", f"New zone: '{text}'")
        return (text, False)
    
    def _is_modal_gump_open(self):
        """Check if modal gump is still open"""
        try:
            if not hasattr(self, 'modal_gump') or not self.modal_gump:
                return False
            
            if hasattr(self.modal_gump, 'IsDisposed'):
                return not self.modal_gump.IsDisposed
            
            try:
                _ = self.modal_gump.X
                return True
            except:
                return False
        except:
            return False
    
    def _recreate_modal_if_closed(self):
        """Recreate modal gump if it was closed"""
        if not hasattr(self, 'modal_gump') or not hasattr(self, 'modal_zone_name'):
            return False
        
        if not self._is_modal_gump_open():
            if self.logger:
                self.logger.warning("GUMP", "MODAL_CLOSED", "Modal gump was closed, recreating")
            
            if self.debug:
                print("[GumpManager] Modal gump closed, recreating...")
            
            # Store alias text before recreating
            saved_alias_text = ""
            try:
                if hasattr(self, 'modal_alias_textbox') and self.modal_alias_textbox:
                    saved_alias_text = self.modal_alias_textbox.Text
            except:
                pass
            
            # Recreate modal gump (same layout as create_new_zone_prompt)
            zone_name = self.modal_zone_name
            modal_width = 450
            modal_height = 260
            modal_gump = self.api.CreateGump(acceptMouseInput=True, canMove=True, keepOpen=False)
            modal_gump.SetRect(0, 0, modal_width, modal_height)
            try:
                if hasattr(modal_gump, 'CanCloseWithRightClick'):
                    modal_gump.CanCloseWithRightClick = False
            except Exception:
                pass
            modal_gump.CenterXInViewPort()
            modal_gump.CenterYInViewPort()
            
            # Background
            bg = self.api.CreateGumpColorBox(0.95, self.COLOR_BG)
            bg.SetRect(0, 0, modal_width, modal_height)
            modal_gump.Add(bg)
            # Accent header bar
            header = self.api.CreateGumpColorBox(1.0, self.COLOR_HEADER)
            header.SetRect(0, 0, modal_width, 6)
            modal_gump.Add(header)
            
            # Title
            title = self.api.CreateGumpLabel("Create New Zone", self.TITLE_HUE)
            title.SetPos(modal_width // 2 - 70, 20)
            modal_gump.Add(title)
            
            # Instructions (same layout as create_new_zone_prompt, no redundant zone label)
            instr1 = self.api.CreateGumpLabel("Add search aliases (comma-separated):", self.HUE_PRIMARY)
            instr1.SetPos(30, 60)
            modal_gump.Add(instr1)
            
            instr2 = self.api.CreateGumpLabel("First alias will be the zone name.", 0x35)
            instr2.SetPos(30, 80)
            modal_gump.Add(instr2)
            
            instr3 = self.api.CreateGumpLabel("You can type any of these to find this zone.", 0x35)
            instr3.SetPos(30, 100)
            modal_gump.Add(instr3)
            
            instr4 = self.api.CreateGumpLabel("Example: zone name, alias1, alias2, alias3", 0x35)
            instr4.SetPos(30, 120)
            modal_gump.Add(instr4)
            
            # Alias textbox (restore previous text if any)
            alias_textbox = self.api.CreateGumpTextBox(saved_alias_text, width=390, height=30)
            alias_textbox.SetPos(30, 150)
            modal_gump.Add(alias_textbox)
            
            # Buttons (adjusted position after removing zone label)
            create_btn = self.api.CreateSimpleButton("Create", 120, 35)
            create_btn.SetPos(100, 200)
            modal_gump.Add(create_btn)
            
            cancel_btn = self.api.CreateSimpleButton("Cancel", 120, 35)
            cancel_btn.SetPos(230, 200)
            modal_gump.Add(cancel_btn)
            
            # Apply bootstrap-like hues
            create_btn.Hue = self.HUE_SUCCESS
            cancel_btn.Hue = self.HUE_DANGER
            
            # Button callbacks (reuse existing flags)
            create_clicked = self.modal_create_clicked
            cancel_clicked = self.modal_cancel_clicked
            
            def on_create():
                create_clicked[0] = True
                if self.debug:
                    print("[GumpManager] Create zone confirmed")
            
            def on_cancel():
                cancel_clicked[0] = True
                if self.debug:
                    print("[GumpManager] Create zone cancelled")
            
            self.api.AddControlOnClick(create_btn, on_create)
            self.api.AddControlOnClick(cancel_btn, on_cancel)
            
            self.api.AddGump(modal_gump)
            
            # Update references
            self.modal_gump = modal_gump
            self.modal_alias_textbox = alias_textbox
            
            if self.logger:
                self.logger.debug("GUMP", "MODAL_RECREATED", "Modal gump recreated successfully")
            
            return True
        
        return False
    
    def create_new_zone_prompt(self, zone_name):
        """
        Create a modal gump to ask for aliases when creating a new zone
        Returns: (confirmed, alias_list)
        """
        try:
            if self.debug:
                print(f"[GumpManager] Creating new zone prompt for: {zone_name}")
            
            # Create modal gump (increased height for additional instruction line)
            modal_width = 450
            modal_height = 260
            modal_gump = self.api.CreateGump(acceptMouseInput=True, canMove=True, keepOpen=False)
            modal_gump.SetRect(0, 0, modal_width, modal_height)
            try:
                if hasattr(modal_gump, 'CanCloseWithRightClick'):
                    modal_gump.CanCloseWithRightClick = False
            except Exception:
                pass
            modal_gump.CenterXInViewPort()
            modal_gump.CenterYInViewPort()
            
            # Background
            bg = self.api.CreateGumpColorBox(0.95, self.COLOR_BG)
            bg.SetRect(0, 0, modal_width, modal_height)
            modal_gump.Add(bg)
            # Accent header bar
            header = self.api.CreateGumpColorBox(1.0, self.COLOR_HEADER)
            header.SetRect(0, 0, modal_width, 6)
            modal_gump.Add(header)
            
            # Title
            title = self.api.CreateGumpLabel("Create New Zone", self.TITLE_HUE)
            title.SetPos(modal_width // 2 - 70, 20)
            modal_gump.Add(title)
            
            # Instructions (removed redundant zone name label)
            instr1 = self.api.CreateGumpLabel("Add search aliases (comma-separated):", self.HUE_PRIMARY)
            instr1.SetPos(30, 60)
            modal_gump.Add(instr1)
            
            instr2 = self.api.CreateGumpLabel("First alias will be the zone name.", 0x35)
            instr2.SetPos(30, 80)
            modal_gump.Add(instr2)
            
            instr3 = self.api.CreateGumpLabel("You can type any of these to find this zone.", 0x35)
            instr3.SetPos(30, 100)
            modal_gump.Add(instr3)
            
            instr4 = self.api.CreateGumpLabel("Example: zone name, alias1, alias2, alias3", 0x35)
            instr4.SetPos(30, 120)
            modal_gump.Add(instr4)
            
            # Alias textbox - use zone_name as first alias suggestion
            alias_textbox = self.api.CreateGumpTextBox(zone_name, width=390, height=30)
            alias_textbox.SetPos(30, 150)
            modal_gump.Add(alias_textbox)
            
            # Buttons (adjusted position after removing zone label)
            create_btn = self.api.CreateSimpleButton("Create", 120, 35)
            create_btn.SetPos(100, 200)
            modal_gump.Add(create_btn)
            
            cancel_btn = self.api.CreateSimpleButton("Cancel", 120, 35)
            cancel_btn.SetPos(230, 200)
            modal_gump.Add(cancel_btn)
            
            # Apply bootstrap-like hues
            create_btn.Hue = self.HUE_SUCCESS
            cancel_btn.Hue = self.HUE_DANGER
            
            # Button click flags
            create_clicked = [False]  # Use list for closure
            cancel_clicked = [False]
            
            def on_create():
                create_clicked[0] = True
                if self.debug:
                    print("[GumpManager] Create zone confirmed")
            
            def on_cancel():
                cancel_clicked[0] = True
                if self.debug:
                    print("[GumpManager] Create zone cancelled")
            
            self.api.AddControlOnClick(create_btn, on_create)
            self.api.AddControlOnClick(cancel_btn, on_cancel)
            
            self.api.AddGump(modal_gump)
            
            # Store modal gump reference for recreation if closed
            self.modal_gump = modal_gump
            self.modal_zone_name = zone_name
            self.modal_create_clicked = create_clicked
            self.modal_cancel_clicked = cancel_clicked
            self.modal_alias_textbox = alias_textbox
            
            # Wait for user action
            if self.debug:
                print("[GumpManager] Waiting for user action on new zone prompt...")
            
            while not create_clicked[0] and not cancel_clicked[0]:
                self.api.ProcessCallbacks()
                
                # Check if modal was closed and recreate if needed (only if no decision made)
                if not create_clicked[0] and not cancel_clicked[0]:
                    self._recreate_modal_if_closed()
                
                self.api.Pause(0.1)
            
            # Get result
            confirmed = create_clicked[0]
            alias_text = alias_textbox.Text.strip() if confirmed else ""
            
            # Parse aliases
            aliases = []
            final_zone_name = zone_name  # Default to original name
            
            if alias_text:
                aliases = [a.strip() for a in alias_text.split(",") if a.strip()]
                # First alias becomes the zone name (user may have changed it)
                if aliases:
                    final_zone_name = aliases[0]
            
            # Close modal (use stored reference if modal was recreated)
            if self.modal_gump:
                self.modal_gump.Dispose()
                if self.logger:
                    self.logger.debug("GUMP", "MODAL_DISPOSED", "Modal closed via stored reference")
            elif modal_gump:
                modal_gump.Dispose()
                if self.logger:
                    self.logger.debug("GUMP", "MODAL_DISPOSED", "Modal closed via local reference")
            
            # Clean up modal references
            self.modal_gump = None
            self.modal_zone_name = None
            self.modal_create_clicked = None
            self.modal_cancel_clicked = None
            self.modal_alias_textbox = None
            
            if self.debug:
                print(f"[GumpManager] New zone prompt result: confirmed={confirmed}, zone={final_zone_name}, aliases={aliases}")
            
            if self.logger:
                self.logger.info("GUMP", "MODAL_CLOSED_COMPLETE", 
                               f"Modal finished: confirmed={confirmed}, zone={final_zone_name}, aliases={aliases}")
            
            return (confirmed, final_zone_name, aliases)
        
        except Exception as e:
            if self.debug:
                print(f"[GumpManager] ERROR in new zone prompt: {e}")
                traceback.print_exc()
            return (False, [])
    
    def create_session_gump(self, zone, use_stored_position=False):
        """Create session gump (only the full one initially)"""
        try:
            self.current_zone = zone
            
            if self.debug:
                print(f"[GumpManager] Creating full session gump for zone: {zone}")
            
            # Guard against duplicate creation during this build
            self._creating_session_gump = True
            # Clear any stale dispose flag and mark creation time early
            try:
                self._session_disposed = False
                import time as _t
                self._last_session_create = _t.time()
            except Exception:
                self._last_session_create = 0.0
            
            # ===== FULL GUMP (expanded) =====
            gump_width = 450
            gump_height = 380
            self.session_gump = self.api.CreateGump(acceptMouseInput=True, canMove=True, keepOpen=False)
            self.session_gump.SetRect(0, 0, gump_width, gump_height)
            try:
                if hasattr(self.session_gump, 'CanCloseWithRightClick'):
                    self.session_gump.CanCloseWithRightClick = False
            except Exception:
                pass
            
            if use_stored_position and hasattr(self, 'gump_x') and hasattr(self, 'gump_y'): 
                # Use stored position (when expanding from minimized)
                # gump_x, gump_y is the top-right corner, calculate top-left
                full_x = self.gump_x - gump_width
                full_y = self.gump_y
                self.session_gump.SetPos(full_x, full_y)
            else:
                # Center on first creation
                self.session_gump.CenterXInViewPort()
                self.session_gump.CenterYInViewPort()
            
            # Background
            bg = self.api.CreateGumpColorBox(0.9, self.COLOR_BG)
            bg.SetRect(0, 0, gump_width, gump_height)
            self.session_gump.Add(bg)
            # Accent header bar
            header = self.api.CreateGumpColorBox(1.0, self.COLOR_HEADER)
            header.SetRect(0, 0, gump_width, 8)
            self.session_gump.Add(header)
            
            # Title
            title = self.api.CreateGumpLabel("GoldTracker - Active Session", self.TITLE_HUE)
            title.SetPos(gump_width // 2 - 110, 25)
            self.session_gump.Add(title)
            self.controls["title"] = title
            
            # Minimize button (top right)
            minimize_btn = self.api.CreateSimpleButton("-", 30, 30)
            minimize_btn.SetPos(gump_width - 50, 20)
            self.session_gump.Add(minimize_btn)
            minimize_btn.Hue = self.HUE_PRIMARY
            self.controls["minimize_button"] = minimize_btn
            
            def on_minimize_click():
                self.minimize_button_clicked = True
                if self.logger:
                    self.logger.debug("GUMP", "MINIMIZE_CALLBACK", "Minimize button callback executed")
            self.api.AddControlOnClick(minimize_btn, on_minimize_click)
            
            # Zone name (static)
            zone_label = self.api.CreateGumpLabel(f"Zone: {zone}", self.HUE_CYAN)
            zone_label.SetPos(20, 50)
            self.session_gump.Add(zone_label)
            
            # Duration (dynamic)
            duration_label = self.api.CreateGumpLabel("Duration: 00:00:00", self.HUE_CYAN)
            duration_label.SetPos(20, 75)
            self.session_gump.Add(duration_label)
            self.controls["duration"] = duration_label
            
            # Separator
            sep1 = self.api.CreateGumpColorBox(0.5, self.COLOR_SEPARATOR)
            sep1.SetRect(20, 100, 360, 1)
            self.session_gump.Add(sep1)
            
            # Gold looted (dynamic)
            gold_label = self.api.CreateGumpLabel("Gold Looted: +0 gp", self.HUE_CYAN)
            gold_label.SetPos(20, 115)
            self.session_gump.Add(gold_label)
            self.controls["gold_looted"] = gold_label
            
            # Deaths (dynamic)
            deaths_label = self.api.CreateGumpLabel("Deaths: 0", self.HUE_CYAN)
            deaths_label.SetPos(20, 140)
            self.session_gump.Add(deaths_label)
            self.controls["deaths"] = deaths_label
            
            # Insurance (dynamic)
            insurance_label = self.api.CreateGumpLabel("Insurance: -0 gp", 0x21)
            insurance_label.SetPos(20, 165)
            self.session_gump.Add(insurance_label)
            self.controls["insurance"] = insurance_label
            
            # Separator
            sep2 = self.api.CreateGumpColorBox(0.5, self.COLOR_SEPARATOR)
            sep2.SetRect(20, 190, 360, 1)
            self.session_gump.Add(sep2)
            
            # Net profit (dynamic, large)
            profit_label = self.api.CreateGumpLabel("NET PROFIT: 0 gp", self.HUE_CYAN)
            profit_label.SetPos(20, 205)
            self.session_gump.Add(profit_label)
            self.controls["net_profit"] = profit_label
            
            # Separator
            sep3 = self.api.CreateGumpColorBox(0.5, self.COLOR_SEPARATOR)
            sep3.SetRect(20, 230, 360, 1)
            self.session_gump.Add(sep3)
            
            # Manual adjustment section
            adjust_label = self.api.CreateGumpLabel("Manual Adjustment:", self.HUE_CYAN)
            adjust_label.SetPos(20, 245)
            self.session_gump.Add(adjust_label)
            
            adjust_textbox = self.api.CreateGumpTextBox("", width=150, height=25)
            adjust_textbox.SetPos(20, 270)
            self.session_gump.Add(adjust_textbox)
            self.controls["adjust_input"] = adjust_textbox
            
            adjust_btn = self.api.CreateSimpleButton("Apply", 70, 25)
            adjust_btn.SetPos(180, 270)
            self.session_gump.Add(adjust_btn)
            # Use WARNING (yellow/orange) to differentiate from Pause (green) and Finish (blue)
            adjust_btn.Hue = self.HUE_WARNING
            self.controls["adjust_button"] = adjust_btn
            
            # Add click callback to adjust button
            def on_adjust_click():
                self.adjust_button_clicked = True
                if self.debug:
                    print("[GumpManager] Adjust button clicked")
            self.api.AddControlOnClick(adjust_btn, on_adjust_click)
            
            # Last update timestamp (dynamic)
            update_label = self.api.CreateGumpLabel("Last Update: --:--:--", self.HUE_CYAN)
            update_label.SetPos(20, 305)
            self.session_gump.Add(update_label)
            self.controls["last_update"] = update_label
            
            # Pause button
            pause_btn = self.api.CreateSimpleButton("Pause", 80, 30)
            pause_btn.SetPos(50, 340)
            self.session_gump.Add(pause_btn)
            pause_btn.Hue = self.HUE_SUCCESS
            self.controls["pause_button"] = pause_btn
            
            # Add click callback to pause button
            def on_pause_click():
                self.pause_button_clicked = True
                if self.debug:
                    print("[GumpManager] Pause button clicked")
            self.api.AddControlOnClick(pause_btn, on_pause_click)
            
            # Finish button
            stop_btn = self.api.CreateSimpleButton("Finish", 80, 30)
            stop_btn.SetPos(160, 340)
            self.session_gump.Add(stop_btn)
            stop_btn.Hue = self.HUE_PRIMARY
            self.controls["stop_button"] = stop_btn
            
            # Add click callback to Finish button
            def on_stop_click():
                self.stop_button_clicked = True
                if self.debug:
                    print("[GumpManager] Finish button clicked")
            self.api.AddControlOnClick(stop_btn, on_stop_click)
            
            # Cancel button
            cancel_btn = self.api.CreateSimpleButton("Cancel", 80, 30)
            cancel_btn.SetPos(270, 340)
            self.session_gump.Add(cancel_btn)
            cancel_btn.Hue = self.HUE_DANGER
            self.controls["cancel_button"] = cancel_btn
            
            # Add click callback to cancel button
            def on_cancel_click():
                self.cancel_button_clicked = True
                if self.debug:
                    print("[GumpManager] Cancel button clicked")
            self.api.AddControlOnClick(cancel_btn, on_cancel_click)
            
            # Register dispose callback (event-driven)
            try:
                def _on_session_disposed():
                    if self._suppress_dispose_handlers or self.finalizing:
                        return
                    self._session_disposed = True
                    if self.logger:
                        self.logger.warning("GUMP", "SESSION_DISPOSED", "Session gump disposed")
                self.api.AddControlOnDisposed(self.session_gump, _on_session_disposed)
            except Exception:
                pass

            # Add full gump
            self.api.AddGump(self.session_gump)

            # Track this instance to ensure it's fully closed on Finish/cleanup
            try:
                self._session_gump_instances.append(self.session_gump)
                if len(self._session_gump_instances) > 5:
                    self._session_gump_instances = self._session_gump_instances[-5:]
            except Exception:
                pass

            # Mark creation time and clear any stale dispose flag to prevent immediate recreation
            try:
                self._last_session_create = time.time()
            except Exception:
                self._last_session_create = 0.0
            self._session_disposed = False
            
            if self.debug:
                print("[GumpManager] Full session gump created")
            
            if self.logger:
                self.logger.info("GUMP", "SESSION_GUMP_CREATED", f"Created session gump for {zone}")
            
            # Release creation guard
            self._creating_session_gump = False
            return True
            
        except Exception as e:
            if self.debug:
                print(f"[GumpManager] ERROR creating session gump: {e}")
                traceback.print_exc()
            
            if self.logger:
                self.logger.error("GUMP", "SESSION_GUMP_ERROR", str(e), {
                    "traceback": traceback.format_exc()
                })
            return False
    
    def _create_mini_gump(self):
        """Create minimized gump"""
        mini_width = 200
        mini_height = 80
        
        # Calculate position: align top-right corner with stored position
        # gump_x, gump_y is the top-right corner from the full gump
        mini_x = self.gump_x - mini_width
        mini_y = self.gump_y
        
        self.mini_gump = self.api.CreateGump(acceptMouseInput=True, canMove=True, keepOpen=False)
        self.mini_gump.SetRect(mini_x, mini_y, mini_width, mini_height)
        try:
            if hasattr(self.mini_gump, 'CanCloseWithRightClick'):
                self.mini_gump.CanCloseWithRightClick = False
        except Exception:
            pass
        
        # Background
        mini_bg = self.api.CreateGumpColorBox(0.9, self.COLOR_BG)
        mini_bg.SetRect(0, 0, mini_width, mini_height)
        self.mini_gump.Add(mini_bg)
        # Accent header bar
        mini_header = self.api.CreateGumpColorBox(1.0, self.COLOR_HEADER)
        mini_header.SetRect(0, 0, mini_width, 6)
        self.mini_gump.Add(mini_header)
        
        # Expand button (top right)
        expand_btn = self.api.CreateSimpleButton("+", 30, 30)
        expand_btn.SetPos(mini_width - 40, 10)
        self.mini_gump.Add(expand_btn)
        expand_btn.Hue = self.HUE_PRIMARY
        
        def on_expand_click():
            self.minimize_button_clicked = True
            if self.logger:
                self.logger.debug("GUMP", "EXPAND_CALLBACK", "Expand button callback executed")
        self.api.AddControlOnClick(expand_btn, on_expand_click)
        
        # Gold amount (large)
        mini_gold = self.api.CreateGumpLabel("0 gp", self.HUE_CYAN)
        mini_gold.SetPos(20, 15)
        self.mini_gump.Add(mini_gold)
        self.controls["mini_gold"] = mini_gold
        
        # Duration
        mini_duration = self.api.CreateGumpLabel("00:00:00", self.HUE_CYAN)
        mini_duration.SetPos(20, 45)
        self.mini_gump.Add(mini_duration)
        self.controls["mini_duration"] = mini_duration
        
        # Register dispose callback for mini gump
        try:
            def _on_mini_disposed():
                if self._suppress_dispose_handlers or self.finalizing:
                    return
                self._mini_disposed = True
                if self.logger:
                    self.logger.warning("GUMP", "MINI_DISPOSED", "Mini gump disposed")
            self.api.AddControlOnDisposed(self.mini_gump, _on_mini_disposed)
        except Exception:
            pass
        
        self.api.AddGump(self.mini_gump)

        # Track this instance to ensure it's fully closed on Finish/cleanup
        try:
            self._mini_gump_instances.append(self.mini_gump)
            if len(self._mini_gump_instances) > 5:
                self._mini_gump_instances = self._mini_gump_instances[-5:]
        except Exception:
            pass
    
    def toggle_minimize(self):
        """Toggle between full and minimized gump"""
        try:
            if self.logger:
                self.logger.debug("GUMP", "MINIMIZE_START", f"Toggle minimize called, current state: {self.minimized}")
            
            self.minimized = not self.minimized
            
            if self.minimized:
                # Minimize: dispose full, create mini
                if self.logger:
                    self.logger.debug("GUMP", "MINIMIZE_ACTION", "Minimizing - disposing full gump")
                
                # Store top-right corner position (where the minimize button is)
                full_width = 450
                full_x = self.session_gump.GetX()
                full_y = self.session_gump.GetY()
                self.gump_x = full_x + full_width  # Top-right X
                self.gump_y = full_y                # Top-right Y
                
                # Suppress any recreation for a short window during transition
                try:
                    self._recreate_suppressed_until = time.time() + 1.0
                except Exception:
                    pass
                
                # Dispose full with suppressed handler
                _prev = self._suppress_dispose_handlers
                self._suppress_dispose_handlers = True
                try:
                    self.session_gump.Dispose()
                finally:
                    self._suppress_dispose_handlers = _prev
                self.session_gump = None
                
                # Create and show mini (will align top-right)
                self._create_mini_gump()
                
            else:
                # Expand: dispose mini, recreate full
                if self.logger:
                    self.logger.debug("GUMP", "EXPAND_ACTION", "Expanding - disposing mini gump")
                
                # Store top-right corner position from mini gump
                mini_width = 200
                mini_x = self.mini_gump.GetX()
                mini_y = self.mini_gump.GetY()
                self.gump_x = mini_x + mini_width  # Top-right X
                self.gump_y = mini_y                # Top-right Y
                
                # Suppress any recreation for a short window during transition
                try:
                    self._recreate_suppressed_until = time.time() + 1.0
                except Exception:
                    pass
                
                # Dispose mini with suppressed handler
                _prev = self._suppress_dispose_handlers
                self._suppress_dispose_handlers = True
                try:
                    self.mini_gump.Dispose()
                finally:
                    self._suppress_dispose_handlers = _prev
                self.mini_gump = None
                
                # Recreate full at same position (use_stored_position=True)
                self.create_session_gump(self.current_zone, use_stored_position=True)
            
            if self.logger:
                self.logger.info("GUMP", "MINIMIZE_TOGGLE", f"Gump {'minimized' if self.minimized else 'expanded'}")
        
        except Exception as e:
            if self.debug:
                print(f"[GumpManager] ERROR toggling minimize: {e}")
                traceback.print_exc()
            
            if self.logger:
                self.logger.error("GUMP", "MINIMIZE_ERROR", str(e), {
                    "traceback": traceback.format_exc()
                })
    
    def update_session_gump(self, session_data):
        """Update active gump with session data"""
        try:
            if not session_data:
                return
            
            # Format duration
            hours = session_data["duration_seconds"] // 3600
            minutes = (session_data["duration_seconds"] % 3600) // 60
            seconds = session_data["duration_seconds"] % 60
            duration_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            net = session_data["net_profit"]
            
            paused = bool(session_data.get("paused", False))
            # Update Pause/Resume button text
            try:
                btn = self.controls.get("pause_button")
                if btn:
                    new_text = "Resume" if paused else "Pause"
                    if hasattr(btn, "SetText"):
                        btn.SetText(new_text)
                    else:
                        btn.Text = new_text
                    btn.Hue = self.HUE_SUCCESS  # keep success color
            except:
                pass

            # Blink handling while paused (synchronized to wall-clock seconds)
            if paused:
                self._blink_on = (int(time.time()) % 2 == 0)

            if self.minimized and "mini_gold" in self.controls:
                # Update MINI gump
                self.controls["mini_gold"].Text = f"{net:,} gp"
                self.controls["mini_gold"].Hue = self.HUE_CYAN
                self.controls["mini_duration"].Text = duration_text
                if paused and "mini_duration" in self.controls:
                    self.controls["mini_duration"].Hue = self.HUE_WARNING if self._blink_on else self.HUE_CYAN
                elif "mini_duration" in self.controls:
                    self.controls["mini_duration"].Hue = self.HUE_CYAN
            elif not self.minimized and "duration" in self.controls:
                # Update FULL gump
                self.controls["duration"].Text = f"Duration: {duration_text}"
                self.controls["gold_looted"].Text = f"Gold Looted: +{session_data['gold_gained']:,} gp"
                self.controls["deaths"].Text = f"Deaths: {session_data['deaths']}"
                self.controls["insurance"].Text = f"Insurance: -{session_data['insurance_cost']:,} gp"
                self.controls["net_profit"].Text = f"NET PROFIT: {net:,} gp"
                # Use cyan for positive net profit per user preference (instead of green)
                self.controls["net_profit"].Hue = self.HUE_CYAN if net >= 0 else self.HUE_DANGER
                
                # Blink hue for duration label when paused
                if paused:
                    self.controls["duration"].Hue = self.HUE_WARNING if self._blink_on else 0x3F
                else:
                    self.controls["duration"].Hue = self.HUE_CYAN
                
                now_str = datetime.now().strftime("%H:%M:%S")
                self.controls["last_update"].Text = f"Last Update: {now_str}"
            
            if self.debug and session_data["duration_seconds"] % 10 == 0:
                print(f"[GumpManager] Updated gump: {net:,} gp net profit")
            
        except Exception as e:
            if self.debug:
                print(f"[GumpManager] ERROR updating gump: {e}")
                traceback.print_exc()
            
            if self.logger:
                self.logger.error("GUMP", "UPDATE_ERROR", str(e), {
                    "traceback": traceback.format_exc()
                })
    
    def is_session_gump_open(self):
        """Check if full session gump is still open"""
        try:
            if not self.session_gump:
                return False
            
            if hasattr(self.session_gump, 'IsDisposed'):
                return not self.session_gump.IsDisposed
            
            # Fallbacks: try GetX()/GetY() methods before accessing attributes
            try:
                if hasattr(self.session_gump, 'GetX') and callable(getattr(self.session_gump, 'GetX')):
                    _ = self.session_gump.GetX()
                    return True
            except Exception:
                pass
            try:
                _ = getattr(self.session_gump, 'X')
                return True
            except Exception:
                return False
        except Exception:
            return False
    
    def is_mini_gump_open(self):
        """Check if mini gump is still open"""
        try:
            if not self.mini_gump:
                return False
            
            if hasattr(self.mini_gump, 'IsDisposed'):
                return not self.mini_gump.IsDisposed
            
            try:
                _ = self.mini_gump.X
                return True
            except:
                return False
        except:
            return False
    
    def recreate_session_gump_if_closed(self):
        """Recreate active gump if it was closed"""
        if not self.current_zone:
            return False
        # Do not recreate if we're finalizing (Finish clicked)
        if getattr(self, 'finalizing', False):
            return False
        
        # Global suppression window (used around minimize/expand and Finish)
        try:
            if time.time() < getattr(self, '_recreate_suppressed_until', 0.0):
                return False
        except Exception:
            pass
        
        # Do not recreate while we're in the middle of creating a session gump
        if getattr(self, '_creating_session_gump', False):
            return False
        
        # Cooldown after creation to prevent duplicate gumps from race conditions
        try:
            if time.time() - getattr(self, '_last_session_create', 0.0) < 1.0:
                return False
        except Exception:
            pass
        
        if self.minimized:
            # Prefer event-driven recreation
            if self._mini_disposed:
                # Guard against stale dispose during creation or right after creation
                try:
                    if getattr(self, '_creating_session_gump', False) or (time.time() - getattr(self, '_last_session_create', 0.0) < 1.0):
                        self._mini_disposed = False
                        return False
                except Exception:
                    pass
                self._mini_disposed = False
                if self.logger:
                    self.logger.warning("GUMP", "MINI_GUMP_DISPOSED", "Mini gump disposed, recreating")
                if self.debug:
                    print("[GumpManager] Mini gump disposed (event), recreating...")
                self._create_mini_gump()
                return True
            # Fallback: polling check
            if not self.is_mini_gump_open():
                if self.logger:
                    self.logger.warning("GUMP", "GUMP_CLOSED", "Mini gump was closed, recreating")
                
                if self.debug:
                    print("[GumpManager] Mini gump closed, recreating...")
                
                # Recreate mini gump at stored position
                self._create_mini_gump()
                return True
        else:
            # Prefer event-driven recreation for full gump
            if self._session_disposed:
                # Guard against stale dispose during creation or right after creation
                try:
                    if getattr(self, '_creating_session_gump', False) or (time.time() - getattr(self, '_last_session_create', 0.0) < 1.0):
                        self._session_disposed = False
                        return False
                except Exception:
                    pass
                self._session_disposed = False
                if self.logger:
                    self.logger.warning("GUMP", "SESSION_GUMP_DISPOSED", "Session gump disposed, recreating")
                if self.debug:
                    print("[GumpManager] Session gump disposed (event), recreating...")
                use_stored = hasattr(self, 'gump_x') and hasattr(self, 'gump_y')
                self.create_session_gump(self.current_zone, use_stored_position=use_stored)
                return True
            # Fallback: polling check
            if not self.is_session_gump_open():
                if self.logger:
                    self.logger.warning("GUMP", "GUMP_CLOSED", "Session gump was closed, recreating")
                
                if self.debug:
                    print("[GumpManager] Session gump closed, recreating...")
                
                # Recreate full gump (use stored position if available)
                use_stored = hasattr(self, 'gump_x') and hasattr(self, 'gump_y')
                self.create_session_gump(self.current_zone, use_stored_position=use_stored)
                return True
        
        return False
    
    def close_active_session_gump(self):
        """Close active session and mini gumps for summary phase.
        Strongly enforces closure even after minimize/expand cycles:
        - Disposes primary and inner containers
        - Falls back to moving gumps off-screen and shrinking if dispose fails
        - Prevents any auto-recreation by setting finalizing and clearing refs/controls
        """
        try:
            # Block any recreation while we close
            self.finalizing = True
            # Suppress any recreation attempts for a short window during Finish transition
            try:
                import time as _t
                self._recreate_suppressed_until = _t.time() + 2.0
            except Exception:
                pass
            _prev = self._suppress_dispose_handlers
            self._suppress_dispose_handlers = True
            try:
                # Helper to aggressively dispose/hide a gump instance
                def _dispose_or_hide(g):
                    try:
                        if hasattr(g, 'Dispose'):
                            g.Dispose()
                    except Exception:
                        pass
                    try:
                        if hasattr(g, 'Gump') and getattr(g, 'Gump'):
                            g.Gump.Dispose()
                    except Exception:
                        pass
                    # Give the client a tick
                    try:
                        self.api.ProcessCallbacks()
                    except Exception:
                        pass
                    # If still present, push off-screen and shrink as a visual fallback
                    try:
                        still_here = False
                        if hasattr(g, 'IsDisposed'):
                            still_here = not g.IsDisposed
                        else:
                            try:
                                _ = g.GetX() if hasattr(g, 'GetX') else g.X
                                still_here = True
                            except Exception:
                                still_here = False
                        if still_here:
                            # Move far off-screen and shrink to 1x1
                            if hasattr(g, 'SetRect'):
                                g.SetRect(-5000, -5000, 1, 1)
                            else:
                                if hasattr(g, 'SetPos'):
                                    g.SetPos(-5000, -5000)
                                if hasattr(g, 'SetWidth'):
                                    g.SetWidth(1)
                                if hasattr(g, 'SetHeight'):
                                    g.SetHeight(1)
                    except Exception:
                        pass
                # Dispose full session gump if exists
                if getattr(self, 'session_gump', None):
                    _dispose_or_hide(self.session_gump)
                    # Drop reference regardless to avoid updates
                    self.session_gump = None
                # Dispose mini gump if exists
                if getattr(self, 'mini_gump', None):
                    _dispose_or_hide(self.mini_gump)
                    self.mini_gump = None
                
                # Aggressively close any historical/duplicate instances (race-safe)
                try:
                    for g in list(getattr(self, '_session_gump_instances', []) or []):
                        _dispose_or_hide(g)
                except Exception:
                    pass
                try:
                    for g in list(getattr(self, '_mini_gump_instances', []) or []):
                        _dispose_or_hide(g)
                except Exception:
                    pass
                # Clear the instance registries
                try:
                    self._session_gump_instances = []
                    self._mini_gump_instances = []
                except Exception:
                    pass
            finally:
                self._suppress_dispose_handlers = _prev
            # Clear control map to avoid touching stale controls
            try:
                self.controls.clear()
            except Exception:
                pass
            # Final callback pump
            try:
                self.api.ProcessCallbacks()
            except Exception:
                pass
            if self.logger:
                self.logger.info("GUMP", "SESSION_GUMP_CLOSED", "Session/mini gumps closed (or hidden) for summary phase")
        except Exception as e:
            if self.logger:
                self.logger.error("GUMP", "SESSION_GUMP_CLOSE_ERROR", str(e), {"traceback": traceback.format_exc()})
    
    def is_zone_gump_open(self):
        """Check if zone selection gump is still open"""
        try:
            if not self.zone_gump:
                return False
            
            if hasattr(self.zone_gump, 'IsDisposed'):
                return not self.zone_gump.IsDisposed
            
            try:
                _ = self.zone_gump.X
                return True
            except:
                return False
        except:
            return False
    
    def recreate_zone_selection_if_closed(self):
        """Recreate zone selection gump if it was closed"""
        if not self.all_zones:
            return False
        
        # Prefer event-driven recreation
        if getattr(self, '_zone_disposed', False):
            self._zone_disposed = False
            if self.logger:
                self.logger.warning("GUMP", "ZONE_GUMP_DISPOSED", "Zone selection gump disposed, recreating")
            if self.debug:
                print("[GumpManager] Zone selection gump disposed (event), recreating...")
            self.create_zone_selection_gump(self.all_zones)
            if self.last_filter_text and "filter_input" in self.controls:
                try:
                    self.controls["filter_input"].SetText(self.last_filter_text)
                    if self.logger:
                        self.logger.debug("GUMP", "FILTER_RESTORED", f"Restored filter: '{self.last_filter_text}'")
                except Exception as e:
                    if self.logger:
                        self.logger.error("GUMP", "FILTER_RESTORE_FAILED", str(e))
            return True
        
        # Fallback to polling if necessary
        if not self.is_zone_gump_open():
            if self.logger:
                self.logger.warning("GUMP", "ZONE_GUMP_CLOSED", "Zone selection gump was closed, recreating")
            
            if self.debug:
                print("[GumpManager] Zone selection gump closed, recreating...")
            
            # Recreate zone gump
            self.create_zone_selection_gump(self.all_zones)
            
            # Restore filter text if it was set
            if self.last_filter_text and "filter_input" in self.controls:
                try:
                    self.controls["filter_input"].SetText(self.last_filter_text)
                    if self.logger:
                        self.logger.debug("GUMP", "FILTER_RESTORED", f"Restored filter: '{self.last_filter_text}'")
                except Exception as e:
                    if self.logger:
                        self.logger.error("GUMP", "FILTER_RESTORE_FAILED", str(e))
            
            return True
        
        return False
    
    def create_summary_gump(self, session_data):
        """Create summary gump showing final session stats and Confirm/Back buttons."""
        try:
            # Reset flags
            self.summary_save_clicked = False
            self.summary_discard_clicked = False
            
            width = 480
            height = 320
            self.summary_gump = self.api.CreateGump(acceptMouseInput=True, canMove=True, keepOpen=False)
            self.summary_gump.SetRect(0, 0, width, height)
            try:
                if hasattr(self.summary_gump, 'CanCloseWithRightClick'):
                    self.summary_gump.CanCloseWithRightClick = False
            except Exception:
                pass
            self.summary_gump.CenterXInViewPort()
            self.summary_gump.CenterYInViewPort()
            
            bg = self.api.CreateGumpColorBox(0.95, self.COLOR_BG)
            bg.SetRect(0, 0, width, height)
            self.summary_gump.Add(bg)
            # Accent header bar
            header = self.api.CreateGumpColorBox(1.0, self.COLOR_HEADER)
            header.SetRect(0, 0, width, 8)
            self.summary_gump.Add(header)
            
            title = self.api.CreateGumpLabel("Session Summary", self.TITLE_HUE)
            title.SetPos(width // 2 - 80, 20)
            self.summary_gump.Add(title)
            
            # Build lines
            y = 60
            line_gap = 24
            def add_line(text):
                nonlocal y
                lbl = self.api.CreateGumpLabel(text, 0x3F)
                lbl.SetPos(30, y)
                self.summary_gump.Add(lbl)
                y += line_gap
            
            # Extract values with safe defaults
            add_line(f"Start: {session_data.get('start_time_str', '--')}")
            add_line(f"End: {session_data.get('end_time_preview_str', '--')}")
            add_line(f"Paused: {session_data.get('paused_time_str', '00:00:00')}")
            add_line(f"Session Time: {session_data.get('session_duration_str', '00:00:00')}")
            add_line(f"Gold (gross): +{session_data.get('gold_gained', 0):,} gp")
            add_line(f"Deaths (insured): -{session_data.get('insurance_cost', 0):,} gp")
            net = session_data.get('net_profit', 0)
            add_line(f"Gold (net): {net:,} gp")
            
            # Buttons
            save_btn = self.api.CreateSimpleButton("Save", 120, 35)
            save_btn.SetPos(100, height - 60)
            self.summary_gump.Add(save_btn)
            discard_btn = self.api.CreateSimpleButton("Discard", 120, 35)
            discard_btn.SetPos(260, height - 60)
            self.summary_gump.Add(discard_btn)
            # Apply hues
            save_btn.Hue = self.HUE_PRIMARY
            discard_btn.Hue = self.HUE_DANGER
            
            def on_save():
                self.summary_save_clicked = True
                if self.debug:
                    print("[GumpManager] Summary Save clicked")
            def on_discard():
                self.summary_discard_clicked = True
                if self.debug:
                    print("[GumpManager] Summary Discard clicked")
            
            self.api.AddControlOnClick(save_btn, on_save)
            self.api.AddControlOnClick(discard_btn, on_discard)
            
            # Register dispose callback for summary gump
            try:
                def _on_summary_disposed():
                    if self._suppress_dispose_handlers:
                        return
                    self._summary_disposed = True
                    self.summary_disposed = True
                    if self.logger:
                        self.logger.warning("GUMP", "SUMMARY_DISPOSED", "Summary gump disposed")
                self.api.AddControlOnDisposed(self.summary_gump, _on_summary_disposed)
            except Exception:
                pass
            
            self.api.AddGump(self.summary_gump)
            
            if self.logger:
                self.logger.info("GUMP", "SUMMARY_CREATED", "Summary gump created")
            return True
        except Exception as e:
            if self.debug:
                print(f"[GumpManager] ERROR creating summary gump: {e}")
                traceback.print_exc()
            if self.logger:
                self.logger.error("GUMP", "SUMMARY_ERROR", str(e), {"traceback": traceback.format_exc()})
            return False
    
    def cleanup(self):
        """Cleanup gumps on exit"""
        try:
            # Prevent dispose event noise/recreation during cleanup
            _prev = self._suppress_dispose_handlers
            self._suppress_dispose_handlers = True
            self.finalizing = True
            try:
                for name in ("zone_gump", "session_gump", "summary_gump", "mini_gump"):
                    g = getattr(self, name, None)
                    if g:
                        # Try direct dispose
                        try:
                            if hasattr(g, 'Dispose'):
                                g.Dispose()
                        except Exception:
                            pass
                        # Try inner container if available
                        try:
                            if hasattr(g, 'Gump') and getattr(g, 'Gump'):
                                g.Gump.Dispose()
                        except Exception:
                            pass
                        # Drop reference
                        setattr(self, name, None)
                # Give the client a tick to process disposals
                try:
                    self.api.ProcessCallbacks()
                except Exception:
                    pass
            finally:
                self._suppress_dispose_handlers = _prev
            
            if self.debug:
                print("[GumpManager] Cleanup complete")
            
        except Exception as e:
            if self.debug:
                print(f"[GumpManager] ERROR during cleanup: {e}")
