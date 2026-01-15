"""
Entity Resolution Service

Maps player names from news text to player IDs in the database.
Handles name variations, nicknames, and fuzzy matching.
"""

import logging
from typing import Optional, Dict, List
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class EntityResolver:
    """
    Resolves player names to database player IDs.
    
    Uses multiple strategies:
    1. Exact match against full_name
    2. Alias lookup (nickname → full name)
    3. Fuzzy matching with confidence threshold
    """
    
    # Common player name aliases and nicknames
    PLAYER_ALIASES = {
        'LeBron': 'LeBron James',
        'Bron': 'LeBron James',
        'King James': 'LeBron James',
        'Giannis': 'Giannis Antetokounmpo',
        'Greek Freak': 'Giannis Antetokounmpo',
        'KD': 'Kevin Durant',
        'Steph': 'Stephen Curry',
        'Chef Curry': 'Stephen Curry',
        'Luka': 'Luka Doncic',
        'Jokic': 'Nikola Jokic',
        'Joker': 'Nikola Jokic',
        'AD': 'Anthony Davis',
        'PG': 'Paul George',
        'PG13': 'Paul George',
        'Dame': 'Damian Lillard',
        'Dame Time': 'Damian Lillard',
        'Kawhi': 'Kawhi Leonard',
        'The Klaw': 'Kawhi Leonard',
        'Embiid': 'Joel Embiid',
        'The Process': 'Joel Embiid',
        'Harden': 'James Harden',
        'The Beard': 'James Harden',
        'Kyrie': 'Kyrie Irving',
        'Uncle Drew': 'Kyrie Irving',
        'Jimmy': 'Jimmy Butler',
        'Jimmy Buckets': 'Jimmy Butler',
        'Tatum': 'Jayson Tatum',
        'JT': 'Jayson Tatum',
        'Booker': 'Devin Booker',
        'Book': 'Devin Booker',
        'Zion': 'Zion Williamson',
        'Ja': 'Ja Morant',
        'Trae': 'Trae Young',
        'Ice Trae': 'Trae Young',
        'SGA': 'Shai Gilgeous-Alexander',
        'Ant': 'Anthony Edwards',
        'Ant-Man': 'Anthony Edwards',
        'Wemby': 'Victor Wembanyama',
        'Alien': 'Victor Wembanyama',
    }
    
    def __init__(self, db_connection=None):
        """
        Initialize the entity resolver.
        
        Args:
            db_connection: Database connection for player lookups
        """
        self.db = db_connection
        self.player_cache = {}
        self._load_player_cache()
    
    def _load_player_cache(self):
        """Load all active players into memory cache"""
        if not self.db:
            logger.warning("No database connection, using empty player cache")
            return
        
        try:
            # This would query your players table
            # For now, we'll use a placeholder
            # In production, replace with actual DB query
            logger.info("Loading player cache from database")
            # players = self.db.query("SELECT id, full_name, first_name, last_name FROM players WHERE active = true")
            # for player in players:
            #     self.player_cache[player['full_name'].lower()] = player['id']
        except Exception as e:
            logger.error(f"Error loading player cache: {str(e)}")
    
    def _exact_match(self, name: str) -> Optional[int]:
        """
        Attempt exact match against player cache.
        
        Args:
            name: Player name to match
            
        Returns:
            Player ID or None
        """
        name_lower = name.lower()
        return self.player_cache.get(name_lower)
    
    def _alias_lookup(self, name: str) -> Optional[str]:
        """
        Look up full name from alias.
        
        Args:
            name: Alias or nickname
            
        Returns:
            Full name or None
        """
        return self.PLAYER_ALIASES.get(name)
    
    def _fuzzy_match(self, name: str, threshold: float = 0.85) -> Optional[int]:
        """
        Fuzzy match against player cache.
        
        Args:
            name: Player name to match
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            Player ID or None
        """
        if not self.player_cache:
            return None
        
        name_lower = name.lower()
        best_match = None
        best_score = 0.0
        
        for cached_name, player_id in self.player_cache.items():
            score = SequenceMatcher(None, name_lower, cached_name).ratio()
            if score > best_score:
                best_score = score
                best_match = player_id
        
        if best_score >= threshold:
            logger.info(f"Fuzzy matched '{name}' with confidence {best_score:.2f}")
            return best_match
        
        return None
    
    def resolve(self, name: str) -> Optional[int]:
        """
        Resolve a player name to a player ID.
        
        Args:
            name: Player name from news text
            
        Returns:
            Player ID or None if not found
        """
        # Strategy 1: Exact match
        player_id = self._exact_match(name)
        if player_id:
            logger.debug(f"Exact match: '{name}' -> {player_id}")
            return player_id
        
        # Strategy 2: Alias lookup
        full_name = self._alias_lookup(name)
        if full_name:
            player_id = self._exact_match(full_name)
            if player_id:
                logger.debug(f"Alias match: '{name}' -> '{full_name}' -> {player_id}")
                return player_id
        
        # Strategy 3: Fuzzy match
        player_id = self._fuzzy_match(name)
        if player_id:
            logger.debug(f"Fuzzy match: '{name}' -> {player_id}")
            return player_id
        
        logger.warning(f"Could not resolve player name: '{name}'")
        return None
    
    def resolve_batch(self, names: List[str]) -> Dict[str, Optional[int]]:
        """
        Resolve multiple player names in batch.
        
        Args:
            names: List of player names
            
        Returns:
            Dict mapping names to player IDs
        """
        results = {}
        for name in names:
            results[name] = self.resolve(name)
        
        resolved_count = sum(1 for pid in results.values() if pid is not None)
        logger.info(f"Resolved {resolved_count}/{len(names)} player names")
        
        return results
    
    def add_alias(self, alias: str, full_name: str):
        """
        Add a custom alias to the resolver.
        
        Args:
            alias: Nickname or alias
            full_name: Full player name
        """
        self.PLAYER_ALIASES[alias] = full_name
        logger.info(f"Added alias: '{alias}' -> '{full_name}'")
    
    def refresh_cache(self):
        """Refresh the player cache from database"""
        self.player_cache.clear()
        self._load_player_cache()
        logger.info("Player cache refreshed")
