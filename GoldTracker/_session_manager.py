# Session Manager - CSV and Session CRUD Operations
# Handles session data persistence and auto-save

import os
import csv
import traceback
from datetime import datetime


class SessionManager:
    """Manages farming session data and CSV operations"""
    
    def __init__(self, csv_file="sessions.csv", logger=None, debug=False):
        self.csv_file = csv_file
        self.logger = logger
        self.debug = debug
        self.current_session = None
        self.next_session_id = self._get_next_id()
        
        self._ensure_csv_exists()
        
        if self.debug:
            print(f"[SessionManager] Initialized. Next ID: {self.next_session_id}")
    
    def _ensure_csv_exists(self):
        """Create CSV with headers if doesn't exist"""
        try:
            if not os.path.exists(self.csv_file):
                with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "session_id", "zone", "start_time", "end_time",
                        "session_duration", "paused_time", "gold_gained", "deaths",
                        "insurance_cost", "net_profit", "notes",
                        "merged", "merged_from"
                    ])
                
                if self.debug:
                    print(f"[SessionManager] Created CSV file: {self.csv_file}")
                
                if self.logger:
                    self.logger.info("SESSION_MGR", "CSV_CREATED", f"Created {self.csv_file}")
        
        except Exception as e:
            if self.debug:
                print(f"[SessionManager] ERROR creating CSV: {e}")
                traceback.print_exc()
            
            if self.logger:
                self.logger.error("SESSION_MGR", "CSV_ERROR", str(e), {
                    "traceback": traceback.format_exc()
                })
    
    def _get_next_id(self):
        """Get next available session ID"""
        max_id = 0
        
        try:
            if os.path.exists(self.csv_file):
                with open(self.csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            session_id = int(row["session_id"])
                            max_id = max(max_id, session_id)
                        except (ValueError, KeyError):
                            pass
        except Exception as e:
            if self.debug:
                print(f"[SessionManager] ERROR reading CSV for next ID: {e}")
        
        return max_id + 1
    
    def start_session(self, zone, initial_gold):
        """Initialize new session"""
        self.current_session = {
            "session_id": self.next_session_id,
            "zone": zone,
            "start_time": datetime.now(),
            "end_time": None,
            "initial_gold": initial_gold,
            "gold_looted": 0,
            "deaths": 0,
            "insurance_cost": 0,
            "manual_adjustments": 0,
            "notes": "",
            "paused": False,
            "paused_started_at": None,
            "paused_total_seconds": 0
        }
        
        self.next_session_id += 1
        
        # Write initial CSV row immediately
        self._write_initial_csv_row()
        
        if self.debug:
            print(f"[SessionManager] Started session #{self.current_session['session_id']} in {zone}")
        
        if self.logger:
            self.logger.info("SESSION_MGR", "SESSION_START", f"Session #{self.current_session['session_id']} started", {
                "zone": zone,
                "initial_gold": initial_gold,
                "session_id": self.current_session['session_id']
            })
        
        return self.current_session
    
    def _write_initial_csv_row(self):
        """Write initial session row to CSV immediately after starting"""
        try:
            # Read existing rows
            rows = []
            if os.path.exists(self.csv_file):
                with open(self.csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
            
            # Append initial session row
            rows.append(self._format_session_for_csv(ongoing=True))
            
            # Write back
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "session_id", "zone", "start_time", "end_time",
                    "session_duration", "paused_time", "gold_gained", "deaths",
                    "insurance_cost", "net_profit", "notes",
                    "merged", "merged_from"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            if self.debug:
                print(f"[SessionManager] Initial CSV row written for session #{self.current_session['session_id']}")
            
            if self.logger:
                self.logger.info("SESSION_MGR", "INITIAL_CSV_WRITE", f"Session #{self.current_session['session_id']} written to CSV")
        
        except Exception as e:
            if self.debug:
                print(f"[SessionManager] ERROR writing initial CSV row: {e}")
                traceback.print_exc()
            
            if self.logger:
                self.logger.error("SESSION_MGR", "INITIAL_CSV_WRITE_ERROR", str(e), {
                    "traceback": traceback.format_exc()
                })
    
    def update_session_data(self, **kwargs):
        """Update current session data"""
        if not self.current_session:
            if self.debug:
                print("[SessionManager] WARNING: No active session to update")
            return
        
        self.current_session.update(kwargs)
        
        if self.debug:
            print(f"[SessionManager] Updated session data: {list(kwargs.keys())}")
    
    def toggle_pause(self):
        """Toggle pause state and accumulate paused_total_seconds."""
        if not self.current_session:
            return False
        now = datetime.now()
        if not self.current_session.get("paused"):
            # Start pause
            self.current_session["paused"] = True
            self.current_session["paused_started_at"] = now
        else:
            # End pause, accumulate
            started = self.current_session.get("paused_started_at")
            if started:
                self.current_session["paused_total_seconds"] = int(self.current_session.get("paused_total_seconds", 0) or 0) + int((now - started).total_seconds())
            self.current_session["paused"] = False
            self.current_session["paused_started_at"] = None
        return self.current_session["paused"]
    
    def auto_save(self):
        """Auto-save current session to CSV (called periodically)"""
        if not self.current_session:
            return
        
        try:
            # Read existing rows
            rows = []
            session_found = False
            
            if os.path.exists(self.csv_file):
                with open(self.csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                    # Check if current session exists
                    for row in rows:
                        if int(row["session_id"]) == self.current_session["session_id"]:
                            session_found = True
                            # Update this row
                            row.update(self._format_session_for_csv(ongoing=True))
            
            # Write back to CSV
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "session_id", "zone", "start_time", "end_time",
                    "session_duration", "paused_time", "gold_gained", "deaths",
                    "insurance_cost", "net_profit", "notes",
                    "merged", "merged_from"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                if session_found:
                    writer.writerows(rows)
                else:
                    writer.writerows(rows)
                    writer.writerow(self._format_session_for_csv(ongoing=True))
            
            if self.debug:
                print(f"[SessionManager] Auto-saved session #{self.current_session['session_id']}")
            
            if self.logger:
                self.logger.debug("SESSION_MGR", "AUTO_SAVE", f"Session #{self.current_session['session_id']} auto-saved")
        
        except Exception as e:
            if self.debug:
                print(f"[SessionManager] ERROR auto-saving: {e}")
                traceback.print_exc()
            
            if self.logger:
                self.logger.error("SESSION_MGR", "AUTO_SAVE_ERROR", str(e), {
                    "traceback": traceback.format_exc()
                })
    
    def end_session(self):
        """Finalize and save session"""
        if not self.current_session:
            return
        
        try:
            session_id = self.current_session["session_id"]
            # Fix end_time at finalization
            self.current_session["end_time"] = datetime.now()
            
            # Read existing rows
            rows = []
            if os.path.exists(self.csv_file):
                with open(self.csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
            
            # Update or append final session data
            session_found = False
            for row in rows:
                if int(row["session_id"]) == session_id:
                    row.update(self._format_session_for_csv(ongoing=False))
                    session_found = True
                    break
            
            if not session_found:
                rows.append(self._format_session_for_csv(ongoing=False))
            
            # Write back
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "session_id", "zone", "start_time", "end_time",
                    "session_duration", "paused_time", "gold_gained", "deaths",
                    "insurance_cost", "net_profit", "notes",
                    "merged", "merged_from"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            if self.debug:
                print(f"[SessionManager] Ended session #{session_id}")
            
            if self.logger:
                self.logger.info("SESSION_MGR", "SESSION_END", f"Session #{session_id} finalized", {
                    "zone": self.current_session["zone"],
                    "duration": self._get_duration_minutes(),
                    "net_profit": self._calculate_net_profit()
                })
            
            self.current_session = None
        
        except Exception as e:
            if self.debug:
                print(f"[SessionManager] ERROR ending session: {e}")
                traceback.print_exc()
            
            if self.logger:
                self.logger.error("SESSION_MGR", "END_SESSION_ERROR", str(e), {
                    "traceback": traceback.format_exc()
                })
    
    def delete_current_session(self):
        """Delete current session from CSV without saving"""
        if not self.current_session:
            return
        
        try:
            session_id = self.current_session["session_id"]
            
            # Read existing rows
            rows = []
            if os.path.exists(self.csv_file):
                with open(self.csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
            
            # Filter out current session
            rows = [row for row in rows if int(row["session_id"]) != session_id]
            
            # Write back
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "session_id", "zone", "start_time", "end_time",
                    "session_duration", "paused_time", "gold_gained", "deaths",
                    "insurance_cost", "net_profit", "notes",
                    "merged", "merged_from"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            if self.debug:
                print(f"[SessionManager] Deleted session #{session_id}")
            
            if self.logger:
                self.logger.info("SESSION_MGR", "SESSION_DELETED", f"Session #{session_id} deleted", {
                    "zone": self.current_session["zone"]
                })
            
            self.current_session = None
        
        except Exception as e:
            if self.debug:
                print(f"[SessionManager] ERROR deleting session: {e}")
                traceback.print_exc()
            
            if self.logger:
                self.logger.error("SESSION_MGR", "DELETE_SESSION_ERROR", str(e), {
                    "traceback": traceback.format_exc()
                })
        
    def mark_finished_now(self, finish_dt=None):
        """Fix end_time at the moment of Finish click and persist final row.
        Does not clear current_session (allows Save/Discard flow)."""
        if not self.current_session:
            return
        try:
            session_id = self.current_session["session_id"]
            # Fix end_time
            from datetime import datetime as _dt
            end_dt = finish_dt or _dt.now()
            self.current_session["end_time"] = end_dt
            
            # Read existing rows
            rows = []
            if os.path.exists(self.csv_file):
                with open(self.csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
            
            # Update or append final session data
            session_found = False
            for row in rows:
                if int(row["session_id"]) == session_id:
                    row.update(self._format_session_for_csv(ongoing=False))
                    session_found = True
                    break
            if not session_found:
                rows.append(self._format_session_for_csv(ongoing=False))
            
            # Write back
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "session_id", "zone", "start_time", "end_time",
                    "session_duration", "paused_time", "gold_gained", "deaths",
                    "insurance_cost", "net_profit", "notes",
                    "merged", "merged_from"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            if self.debug:
                print(f"[SessionManager] Marked session #{session_id} finished at {end_dt}")
            if self.logger:
                self.logger.info("SESSION_MGR", "MARK_FINISHED", f"Session #{session_id} marked finished", {
                    "end_time": end_dt.strftime("%Y-%m-%d %H:%M:%S")
                })
        except Exception as e:
            if self.debug:
                print(f"[SessionManager] ERROR marking finished: {e}")
                traceback.print_exc()
            if self.logger:
                self.logger.error("SESSION_MGR", "MARK_FINISHED_ERROR", str(e), {
                    "traceback": traceback.format_exc()
                })
        
    def clear_current_session(self):
        """Clear session from memory without modifying CSV (used after Save)."""
        if not self.current_session:
            return
        if self.debug:
            print(f"[SessionManager] Clearing current session #{self.current_session['session_id']} from memory")
        self.current_session = None
        if self.logger:
            self.logger.info("SESSION_MGR", "SESSION_CLEARED", "Cleared current session from memory")
        
    def _format_session_for_csv(self, ongoing=True):
        """Format current session data for CSV row, including pause-aware duration."""
        session = self.current_session
        if not session:
            return {}
        
        start_time = session["start_time"]
        if ongoing:
            end_time = datetime.now()
            end_time_str = ""
        else:
            end_time = session.get("end_time") or datetime.now()
            end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Compute paused seconds up to end_time
        paused_seconds = int(session.get("paused_total_seconds", 0) or 0)
        if session.get("paused") and session.get("paused_started_at"):
            paused_seconds += int((end_time - session["paused_started_at"]).total_seconds())
        
        # Effective duration
        total_seconds = max(0, int((end_time - start_time).total_seconds()) - paused_seconds)
        
        def fmt_hms(sec: int) -> str:
            h = sec // 3600
            m = (sec % 3600) // 60
            s = sec % 60
            return f"{h:02d}:{m:02d}:{s:02d}"
        
        session_duration = fmt_hms(total_seconds)
        paused_time = fmt_hms(paused_seconds)
        
        # Totals
        gold_gained = session["gold_looted"] + session["manual_adjustments"]
        total_insurance = session["deaths"] * session["insurance_cost"]
        net_profit = gold_gained - total_insurance
        
        return {
            "session_id": session["session_id"],
            "zone": session["zone"],
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time_str,
            "session_duration": session_duration,
            "paused_time": paused_time,
            "gold_gained": gold_gained,
            "deaths": session["deaths"],
            "insurance_cost": total_insurance,
            "net_profit": net_profit,
            "notes": session.get("notes", ""),
            "merged": "false",
            "merged_from": ""
        }
    
    def _get_duration_minutes(self):
        """Get current session duration in minutes (pause-aware)."""
        if not self.current_session:
            return 0
        now = datetime.now()
        start = self.current_session["start_time"]
        paused = int(self.current_session.get("paused_total_seconds", 0) or 0)
        if self.current_session.get("paused") and self.current_session.get("paused_started_at"):
            paused += int((now - self.current_session["paused_started_at"]).total_seconds())
        effective_seconds = max(0, int((now - start).total_seconds()) - paused)
        return int(effective_seconds / 60)
    
    def _calculate_net_profit(self):
        """Calculate current net profit"""
        if not self.current_session:
            return 0
        
        gold_gained = self.current_session["gold_looted"] + self.current_session["manual_adjustments"]
        total_insurance = self.current_session["deaths"] * self.current_session["insurance_cost"]
        return gold_gained - total_insurance
    
    def get_session_data(self, now_override=None):
        """Get current session data for display (pause-aware).
        Optionally provide now_override (datetime) to freeze the snapshot time."""
        if not self.current_session:
            return None
        now = now_override or datetime.now()
        start = self.current_session["start_time"]
        paused_seconds = int(self.current_session.get("paused_total_seconds", 0) or 0)
        if self.current_session.get("paused") and self.current_session.get("paused_started_at"):
            paused_seconds += int((now - self.current_session["paused_started_at"]).total_seconds())
        effective_seconds = max(0, int((now - start).total_seconds()) - paused_seconds)
        
        def fmt_hms(sec: int) -> str:
            h = sec // 3600
            m = (sec % 3600) // 60
            s = sec % 60
            return f"{h:02d}:{m:02d}:{s:02d}"
        
        gold_gained = self.current_session["gold_looted"] + self.current_session["manual_adjustments"]
        total_insurance = self.current_session["deaths"] * self.current_session["insurance_cost"]
        net_profit = gold_gained - total_insurance
        
        return {
            "zone": self.current_session["zone"],
            "duration_seconds": int(effective_seconds),
            "gold_looted": self.current_session["gold_looted"],
            "gold_gained": gold_gained,
            "deaths": self.current_session["deaths"],
            "insurance_cost": total_insurance,
            "net_profit": net_profit,
            "paused": self.current_session["paused"],
            "paused_time_str": fmt_hms(paused_seconds),
            "session_duration_str": fmt_hms(effective_seconds),
            "start_time_str": start.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time_preview_str": now.strftime("%Y-%m-%d %H:%M:%S")
        }
