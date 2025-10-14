# Zone Manager - Zone and Alias Management
# Handles zone normalization and alias system

import os
import json
import traceback
from datetime import datetime


class ZoneManager:
    """Manages zones and their aliases for GoldTracker"""
    
    def __init__(self, zones_file="zones.json", debug=False):
        self.zones_file = zones_file
        self.debug = debug
        self.zones = self.load_zones()
        
        if self.debug:
            print(f"[ZoneManager] Initialized with {len(self.zones)} zones")
    
    def load_zones(self):
        """Load zones from JSON file"""
        try:
            if os.path.exists(self.zones_file):
                with open(self.zones_file, "r", encoding="utf-8") as f:
                    zones = json.load(f)
                    if self.debug:
                        print(f"[ZoneManager] Loaded {len(zones)} zones from {self.zones_file}")
                    return zones
            else:
                if self.debug:
                    print(f"[ZoneManager] zones.json not found, creating default")
                # Return default zones with common farming locations
                default_zones = {
                    "Tomb of Kings": ["tok", "tomb", "tomb of kings", "tumba"],
                    "Shadowguard": ["shadowguard", "sg", "roof"],
                    "Citadel": ["citadel", "ciudadela", "ninjas"],
                    "Wind": ["wind", "viento", "elementales"],
                    "Doom": ["doom", "gauntlet"],
                    "Covetous": ["covetous", "cov"],
                    "Despise": ["despise", "desp"],
                    "Destard": ["destard", "dest"],
                    "Shame": ["shame"],
                    "Wrong": ["wrong"],
                    "Deceit": ["deceit"],
                    "Hythloth": ["hythloth", "hyth"],
                    "Khaldun": ["khaldun", "khal"]
                }
                self.zones = default_zones
                self.save_zones()
                return default_zones
                
        except Exception as e:
            if self.debug:
                print(f"[ZoneManager] ERROR loading zones: {e}")
                traceback.print_exc()
            return {}
    
    def save_zones(self):
        """Save zones to JSON file"""
        try:
            with open(self.zones_file, "w", encoding="utf-8") as f:
                json.dump(self.zones, f, indent=2, ensure_ascii=False)
                
            if self.debug:
                print(f"[ZoneManager] Saved {len(self.zones)} zones to {self.zones_file}")
            return True
            
        except Exception as e:
            if self.debug:
                print(f"[ZoneManager] ERROR saving zones: {e}")
                traceback.print_exc()
            return False
    
    def get_zone_list(self):
        """Get list of canonical zone names"""
        zone_list = list(self.zones.keys())
        if self.debug:
            print(f"[ZoneManager] Zone list: {zone_list}")
        return zone_list
    
    def normalize_zone_name(self, user_input):
        """
        Normalize user input to canonical zone name
        Returns canonical name or None if not found
        """
        if not user_input:
            return None
        
        user_lower = user_input.lower().strip()
        
        if self.debug:
            print(f"[ZoneManager] Normalizing '{user_input}' (lower: '{user_lower}')")
        
        # Check if it's already a canonical name
        for canonical in self.zones.keys():
            if canonical.lower() == user_lower:
                if self.debug:
                    print(f"[ZoneManager] Match found (canonical): {canonical}")
                return canonical
        
        # Check aliases
        for canonical, aliases in self.zones.items():
            if user_lower in [a.lower() for a in aliases]:
                if self.debug:
                    print(f"[ZoneManager] Match found (alias): {canonical}")
                return canonical
        
        if self.debug:
            print(f"[ZoneManager] No match found for '{user_input}'")
        return None
    
    def add_zone(self, zone_name):
        """Add new zone with initial alias"""
        if not zone_name or not zone_name.strip():
            if self.debug:
                print(f"[ZoneManager] ERROR: Empty zone name")
            return False
        
        zone_name = zone_name.strip()
        
        # Check if already exists
        if zone_name in self.zones:
            if self.debug:
                print(f"[ZoneManager] Zone '{zone_name}' already exists")
            return True
        
        # Add new zone with lowercase alias
        self.zones[zone_name] = [zone_name.lower()]
        
        if self.debug:
            print(f"[ZoneManager] Added new zone: {zone_name}")
        
        return self.save_zones()
    
    def add_alias(self, canonical_name, alias):
        """Add alias to existing zone"""
        if canonical_name not in self.zones:
            if self.debug:
                print(f"[ZoneManager] ERROR: Zone '{canonical_name}' not found")
            return False
        
        alias_lower = alias.lower().strip()
        
        # Check if alias already exists
        if alias_lower in [a.lower() for a in self.zones[canonical_name]]:
            if self.debug:
                print(f"[ZoneManager] Alias '{alias}' already exists for {canonical_name}")
            return True
        
        # Add alias
        self.zones[canonical_name].append(alias_lower)
        
        if self.debug:
            print(f"[ZoneManager] Added alias '{alias}' to {canonical_name}")
        
        return self.save_zones()
    
    def get_zone_info(self, zone_name):
        """Get zone info including aliases"""
        canonical = self.normalize_zone_name(zone_name)
        
        if not canonical:
            return None
        
        return {
            "canonical": canonical,
            "aliases": self.zones[canonical]
        }
