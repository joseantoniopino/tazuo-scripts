# Gump Manager - Dynamic Gump UI Controller
# Handles zone selection and session tracking gumps

import traceback
from datetime import datetime


class GumpManager:
    """Manages gump UI for GoldTracker"""
    
    def __init__(self, api, logger=None, debug=False):
        self.api = api  # API reference passed from main script
        self.logger = logger
        self.debug = debug
        self.zone_gump = None
        self.session_gump = None
        self.controls = {}
        
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
        
        if self.debug:
            print("[GumpManager] Initialized")
    
    def create_zone_selection_gump(self, zones):
        """Create zone selection gump ONCE"""
        try:
            if self.debug:
                print(f"[GumpManager] Creating zone selection gump with {len(zones)} zones")
            
            gump_width = 450
            gump_height = 350 + (len(zones) * 30)
            self.zone_gump = self.api.CreateGump(acceptMouseInput=True, canMove=True, keepOpen=False)
            self.zone_gump.SetRect(0, 0, gump_width, gump_height)
            self.zone_gump.CenterXInViewPort()
            self.zone_gump.CenterYInViewPort()
            
            # Background
            bg = self.api.CreateGumpColorBox(0.9, "#1a1a2e")
            bg.SetRect(0, 0, gump_width, gump_height)
            self.zone_gump.Add(bg)
            
            # Title (centered)
            title = self.api.CreateGumpLabel("GoldTracker - Select Zone", 0x0481)  # Gold color
            title.SetPos(gump_width // 2 - 100, 25)
            self.zone_gump.Add(title)
            
            # Zone radio buttons
            y_offset = 60
            self.controls["zone_radios"] = []
            for i, zone in enumerate(zones):
                radio = self.api.CreateGumpRadioButton(zone, group=1, isChecked=(i == 0))
                radio.SetPos(40, y_offset)
                self.zone_gump.Add(radio)
                self.controls["zone_radios"].append(radio)
                y_offset += 30
            
            # New zone section
            new_zone_label = self.api.CreateGumpLabel("Or create new zone:", 0x44)
            new_zone_label.SetPos(40, y_offset + 20)
            self.zone_gump.Add(new_zone_label)
            
            new_zone_textbox = self.api.CreateGumpTextBox("", width=300, height=30)
            new_zone_textbox.SetPos(40, y_offset + 45)
            self.zone_gump.Add(new_zone_textbox)
            self.controls["new_zone_input"] = new_zone_textbox
            
            # Start button with callback
            start_btn = self.api.CreateSimpleButton("Start Session", 150, 35)
            start_btn.SetPos(125, y_offset + 90)
            self.zone_gump.Add(start_btn)
            self.controls["start_button"] = start_btn
            
            # Add click callback to start button
            def on_start_click():
                self.start_button_clicked = True
                if self.debug:
                    print("[GumpManager] Start button clicked")
            
            self.api.AddControlOnClick(start_btn, on_start_click)
            
            self.api.AddGump(self.zone_gump)
            
            if self.debug:
                print("[GumpManager] Zone selection gump created")
            
            if self.logger:
                self.logger.info("GUMP", "ZONE_SELECTION_CREATED", f"Created gump with {len(zones)} zones")
            
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
    
    def create_session_gump(self, zone, use_stored_position=False):
        """Create session gump (only the full one initially)"""
        try:
            self.current_zone = zone
            
            if self.debug:
                print(f"[GumpManager] Creating full session gump for zone: {zone}")
            
            # ===== FULL GUMP (expanded) =====
            gump_width = 450
            gump_height = 380
            self.session_gump = self.api.CreateGump(acceptMouseInput=True, canMove=True, keepOpen=True)
            self.session_gump.SetRect(0, 0, gump_width, gump_height)
            
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
            bg = self.api.CreateGumpColorBox(0.9, "#1a1a2e")
            bg.SetRect(0, 0, gump_width, gump_height)
            self.session_gump.Add(bg)
            
            # Title
            title = self.api.CreateGumpLabel("GoldTracker - Active Session", 0x0481)
            title.SetPos(gump_width // 2 - 110, 25)
            self.session_gump.Add(title)
            self.controls["title"] = title
            
            # Minimize button (top right)
            minimize_btn = self.api.CreateSimpleButton("-", 30, 30)
            minimize_btn.SetPos(gump_width - 50, 20)
            self.session_gump.Add(minimize_btn)
            self.controls["minimize_button"] = minimize_btn
            
            def on_minimize_click():
                self.minimize_button_clicked = True
                if self.logger:
                    self.logger.debug("GUMP", "MINIMIZE_CALLBACK", "Minimize button callback executed")
            self.api.AddControlOnClick(minimize_btn, on_minimize_click)
            
            # Zone name (static)
            zone_label = self.api.CreateGumpLabel(f"Zone: {zone}", 0x44)
            zone_label.SetPos(20, 50)
            self.session_gump.Add(zone_label)
            
            # Duration (dynamic)
            duration_label = self.api.CreateGumpLabel("Duration: 00:00:00", 0x3F)
            duration_label.SetPos(20, 75)
            self.session_gump.Add(duration_label)
            self.controls["duration"] = duration_label
            
            # Separator
            sep1 = self.api.CreateGumpColorBox(0.5, "#444444")
            sep1.SetRect(20, 100, 360, 1)
            self.session_gump.Add(sep1)
            
            # Gold looted (dynamic)
            gold_label = self.api.CreateGumpLabel("Gold Looted: +0 gp", 0x3F)
            gold_label.SetPos(20, 115)
            self.session_gump.Add(gold_label)
            self.controls["gold_looted"] = gold_label
            
            # Deaths (dynamic)
            deaths_label = self.api.CreateGumpLabel("Deaths: 0", 0x3F)
            deaths_label.SetPos(20, 140)
            self.session_gump.Add(deaths_label)
            self.controls["deaths"] = deaths_label
            
            # Insurance (dynamic)
            insurance_label = self.api.CreateGumpLabel("Insurance: -0 gp", 0x21)
            insurance_label.SetPos(20, 165)
            self.session_gump.Add(insurance_label)
            self.controls["insurance"] = insurance_label
            
            # Separator
            sep2 = self.api.CreateGumpColorBox(0.5, "#444444")
            sep2.SetRect(20, 190, 360, 1)
            self.session_gump.Add(sep2)
            
            # Net profit (dynamic, large)
            profit_label = self.api.CreateGumpLabel("NET PROFIT: 0 gp", 0x44)
            profit_label.SetPos(20, 205)
            self.session_gump.Add(profit_label)
            self.controls["net_profit"] = profit_label
            
            # Separator
            sep3 = self.api.CreateGumpColorBox(0.5, "#444444")
            sep3.SetRect(20, 230, 360, 1)
            self.session_gump.Add(sep3)
            
            # Manual adjustment section
            adjust_label = self.api.CreateGumpLabel("Manual Adjustment:", 0x3F)
            adjust_label.SetPos(20, 245)
            self.session_gump.Add(adjust_label)
            
            adjust_textbox = self.api.CreateGumpTextBox("", width=150, height=25)
            adjust_textbox.SetPos(20, 270)
            self.session_gump.Add(adjust_textbox)
            self.controls["adjust_input"] = adjust_textbox
            
            adjust_btn = self.api.CreateSimpleButton("Apply", 70, 25)
            adjust_btn.SetPos(180, 270)
            self.session_gump.Add(adjust_btn)
            self.controls["adjust_button"] = adjust_btn
            
            # Add click callback to adjust button
            def on_adjust_click():
                self.adjust_button_clicked = True
                if self.debug:
                    print("[GumpManager] Adjust button clicked")
            self.api.AddControlOnClick(adjust_btn, on_adjust_click)
            
            # Last update timestamp (dynamic)
            update_label = self.api.CreateGumpLabel("Last Update: --:--:--", 0x3F)
            update_label.SetPos(20, 305)
            self.session_gump.Add(update_label)
            self.controls["last_update"] = update_label
            
            # Pause button
            pause_btn = self.api.CreateSimpleButton("Pause", 80, 30)
            pause_btn.SetPos(50, 340)
            self.session_gump.Add(pause_btn)
            self.controls["pause_button"] = pause_btn
            
            # Add click callback to pause button
            def on_pause_click():
                self.pause_button_clicked = True
                if self.debug:
                    print("[GumpManager] Pause button clicked")
            self.api.AddControlOnClick(pause_btn, on_pause_click)
            
            # Stop button
            stop_btn = self.api.CreateSimpleButton("Stop", 80, 30)
            stop_btn.SetPos(160, 340)
            self.session_gump.Add(stop_btn)
            self.controls["stop_button"] = stop_btn
            
            # Add click callback to stop button
            def on_stop_click():
                self.stop_button_clicked = True
                if self.debug:
                    print("[GumpManager] Stop button clicked")
            self.api.AddControlOnClick(stop_btn, on_stop_click)
            
            # Cancel button
            cancel_btn = self.api.CreateSimpleButton("Cancel", 80, 30)
            cancel_btn.SetPos(270, 340)
            self.session_gump.Add(cancel_btn)
            self.controls["cancel_button"] = cancel_btn
            
            # Add click callback to cancel button
            def on_cancel_click():
                self.cancel_button_clicked = True
                if self.debug:
                    print("[GumpManager] Cancel button clicked")
            self.api.AddControlOnClick(cancel_btn, on_cancel_click)
            
            # Add full gump
            self.api.AddGump(self.session_gump)
            
            if self.debug:
                print("[GumpManager] Full session gump created")
            
            if self.logger:
                self.logger.info("GUMP", "SESSION_GUMP_CREATED", f"Created session gump for {zone}")
            
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
        
        self.mini_gump = self.api.CreateGump(acceptMouseInput=True, canMove=True, keepOpen=True)
        self.mini_gump.SetRect(mini_x, mini_y, mini_width, mini_height)
        
        # Background
        mini_bg = self.api.CreateGumpColorBox(0.9, "#1a1a2e")
        mini_bg.SetRect(0, 0, mini_width, mini_height)
        self.mini_gump.Add(mini_bg)
        
        # Expand button (top right)
        expand_btn = self.api.CreateSimpleButton("+", 30, 30)
        expand_btn.SetPos(mini_width - 40, 10)
        self.mini_gump.Add(expand_btn)
        
        def on_expand_click():
            self.minimize_button_clicked = True
            if self.logger:
                self.logger.debug("GUMP", "EXPAND_CALLBACK", "Expand button callback executed")
        self.api.AddControlOnClick(expand_btn, on_expand_click)
        
        # Gold amount (large)
        mini_gold = self.api.CreateGumpLabel("0 gp", 0x0481)
        mini_gold.SetPos(20, 15)
        self.mini_gump.Add(mini_gold)
        self.controls["mini_gold"] = mini_gold
        
        # Duration
        mini_duration = self.api.CreateGumpLabel("00:00:00", 0x3F)
        mini_duration.SetPos(20, 45)
        self.mini_gump.Add(mini_duration)
        self.controls["mini_duration"] = mini_duration
        
        self.api.AddGump(self.mini_gump)
    
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
                
                # Dispose full
                self.session_gump.Dispose()
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
                
                # Dispose mini
                self.mini_gump.Dispose()
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
            
            if self.minimized and "mini_gold" in self.controls:
                # Update MINI gump
                self.controls["mini_gold"].Text = f"{net:,} gp"
                self.controls["mini_gold"].Hue = 0x44 if net >= 0 else 0x21
                self.controls["mini_duration"].Text = duration_text
            elif not self.minimized and "duration" in self.controls:
                # Update FULL gump
                self.controls["duration"].Text = f"Duration: {duration_text}"
                self.controls["gold_looted"].Text = f"Gold Looted: +{session_data['gold_gained']:,} gp"
                self.controls["deaths"].Text = f"Deaths: {session_data['deaths']}"
                self.controls["insurance"].Text = f"Insurance: -{session_data['insurance_cost']:,} gp"
                self.controls["net_profit"].Text = f"NET PROFIT: {net:,} gp"
                self.controls["net_profit"].Hue = 0x44 if net >= 0 else 0x21
                
                now = datetime.now().strftime("%H:%M:%S")
                self.controls["last_update"].Text = f"Last Update: {now}"
            
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
            
            try:
                _ = self.session_gump.X
                return True
            except:
                return False
        except:
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
        
        if self.minimized:
            # Check mini gump
            if not self.is_mini_gump_open():
                if self.logger:
                    self.logger.warning("GUMP", "GUMP_CLOSED", "Mini gump was closed, recreating")
                
                if self.debug:
                    print("[GumpManager] Mini gump closed, recreating...")
                
                # Recreate mini gump at stored position
                self._create_mini_gump()
                return True
        else:
            # Check full gump
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
    
    def cleanup(self):
        """Cleanup gumps on exit"""
        try:
            if self.zone_gump:
                if hasattr(self.zone_gump, 'Dispose'):
                    self.zone_gump.Dispose()
            
            if self.session_gump:
                if hasattr(self.session_gump, 'Dispose'):
                    self.session_gump.Dispose()
            
            if self.debug:
                print("[GumpManager] Cleanup complete")
            
        except Exception as e:
            if self.debug:
                print(f"[GumpManager] ERROR during cleanup: {e}")
