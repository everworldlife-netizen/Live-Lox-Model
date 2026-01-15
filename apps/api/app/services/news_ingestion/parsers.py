"""
News Parsing Service

Extracts structured information from unstructured news text.
Identifies player names, status keywords, and injury details.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParsedSignal:
    """Structured representation of a parsed news signal"""
    player_name: str
    status_keyword: Optional[str] = None
    minutes_keyword: Optional[str] = None
    lineup_keyword: Optional[str] = None
    injury_detail: Optional[str] = None
    confidence: str = 'MEDIUM'
    raw_text: str = ''


class NewsParser:
    """
    Parses news text to extract player injury and lineup signals.
    
    Uses keyword dictionaries and regex patterns to identify:
    - Player status (OUT, QUESTIONABLE, etc.)
    - Minutes restrictions
    - Lineup changes
    - Injury details
    """
    
    # Status keywords (ordered by priority)
    STATUS_KEYWORDS = {
        'OUT': ['out', 'ruled out', 'won\'t return', 'will not play', 'sidelined'],
        'QUESTIONABLE': ['questionable', 'game-time decision', 'gtd', 'game time decision'],
        'DOUBTFUL': ['doubtful', 'unlikely to play', 'not expected to play'],
        'PROBABLE': ['probable', 'likely to play', 'expected to play'],
        'AVAILABLE': ['available', 'cleared to play', 'will play', 'active'],
    }
    
    # Minutes-related keywords
    MINUTES_KEYWORDS = {
        'RESTRICTION': ['minutes restriction', 'minutes limit', 'limited minutes', 'restricted'],
        'FULL_GO': ['full go', 'no restrictions', 'unrestricted', 'full minutes'],
        'LIMITED': ['limited', 'cautious', 'eased back', 'monitored'],
    }
    
    # Lineup keywords
    LINEUP_KEYWORDS = {
        'STARTING': ['will start', 'starting', 'moves into starting lineup', 'joins starting lineup'],
        'BENCH': ['moves to bench', 'coming off bench', 'bench role'],
        'STARTING_LINEUP': ['starting lineup', 'starters'],
    }
    
    # Injury body parts for detail extraction
    INJURY_PARTS = [
        'ankle', 'knee', 'hamstring', 'back', 'shoulder', 'wrist', 'hand',
        'foot', 'calf', 'quad', 'hip', 'groin', 'achilles', 'finger',
        'elbow', 'neck', 'head', 'concussion', 'illness', 'covid'
    ]
    
    def __init__(self):
        """Initialize the news parser"""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        # Pattern for player names (capitalized words, 2-4 words)
        self.player_name_pattern = re.compile(
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        )
        
        # Pattern for injury details in parentheses
        self.injury_detail_pattern = re.compile(
            r'\(([^)]+(?:injury|strain|sprain|tear|fracture|surgery|illness|covid))\)',
            re.IGNORECASE
        )
    
    def extract_player_names(self, text: str) -> List[str]:
        """
        Extract potential player names from text.
        
        Args:
            text: Input text
            
        Returns:
            List of potential player names
        """
        matches = self.player_name_pattern.findall(text)
        
        # Filter out common false positives
        false_positives = {'The', 'This', 'That', 'With', 'From', 'Will', 'Can'}
        names = [name for name in matches if name not in false_positives]
        
        return names
    
    def extract_status_keyword(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Extract status keyword from text.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (status_category, matched_keyword) or None
        """
        text_lower = text.lower()
        
        # Check each status category
        for status, keywords in self.STATUS_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return (status, keyword)
        
        return None
    
    def extract_minutes_keyword(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Extract minutes-related keyword from text.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (minutes_category, matched_keyword) or None
        """
        text_lower = text.lower()
        
        for category, keywords in self.MINUTES_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return (category, keyword)
        
        return None
    
    def extract_lineup_keyword(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Extract lineup-related keyword from text.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (lineup_category, matched_keyword) or None
        """
        text_lower = text.lower()
        
        for category, keywords in self.LINEUP_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return (category, keyword)
        
        return None
    
    def extract_injury_detail(self, text: str) -> Optional[str]:
        """
        Extract injury detail from text.
        
        Args:
            text: Input text
            
        Returns:
            Injury detail string or None
        """
        # First try to find injury in parentheses
        match = self.injury_detail_pattern.search(text)
        if match:
            return match.group(1)
        
        # Otherwise look for injury body parts
        text_lower = text.lower()
        for part in self.INJURY_PARTS:
            if part in text_lower:
                # Extract context around the injury part
                idx = text_lower.index(part)
                start = max(0, idx - 20)
                end = min(len(text), idx + 30)
                return text[start:end].strip()
        
        return None
    
    def parse_rss_item(self, item: Dict) -> Optional[ParsedSignal]:
        """
        Parse an RSS feed item.
        
        Args:
            item: RSS item dict from RSSPoller
            
        Returns:
            ParsedSignal or None if no relevant info found
        """
        title = item.get('title', '')
        description = item.get('description', '')
        combined_text = f"{title} {description}"
        
        # Extract player names
        player_names = self.extract_player_names(combined_text)
        if not player_names:
            return None
        
        # Use the first player name found
        player_name = player_names[0]
        
        # Extract keywords
        status_result = self.extract_status_keyword(combined_text)
        minutes_result = self.extract_minutes_keyword(combined_text)
        lineup_result = self.extract_lineup_keyword(combined_text)
        injury_detail = self.extract_injury_detail(combined_text)
        
        # Determine confidence based on source priority
        source_priority = item.get('source_priority', 2)
        if source_priority == 1:
            confidence = 'HIGH'
        elif source_priority == 2:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        return ParsedSignal(
            player_name=player_name,
            status_keyword=status_result[0] if status_result else None,
            minutes_keyword=minutes_result[0] if minutes_result else None,
            lineup_keyword=lineup_result[0] if lineup_result else None,
            injury_detail=injury_detail,
            confidence=confidence,
            raw_text=combined_text
        )
    
    def parse_tweet(self, tweet: Dict) -> Optional[ParsedSignal]:
        """
        Parse a Twitter/X tweet.
        
        Args:
            tweet: Tweet dict from TwitterMonitor
            
        Returns:
            ParsedSignal or None if no relevant info found
        """
        text = tweet.get('text', '')
        
        # Extract player names
        player_names = self.extract_player_names(text)
        if not player_names:
            return None
        
        player_name = player_names[0]
        
        # Extract keywords
        status_result = self.extract_status_keyword(text)
        minutes_result = self.extract_minutes_keyword(text)
        lineup_result = self.extract_lineup_keyword(text)
        injury_detail = self.extract_injury_detail(text)
        
        # Twitter alerts are generally high confidence
        source_priority = tweet.get('source_priority', 1)
        confidence = 'HIGH' if source_priority == 1 else 'MEDIUM'
        
        return ParsedSignal(
            player_name=player_name,
            status_keyword=status_result[0] if status_result else None,
            minutes_keyword=minutes_result[0] if minutes_result else None,
            lineup_keyword=lineup_result[0] if lineup_result else None,
            injury_detail=injury_detail,
            confidence=confidence,
            raw_text=text
        )
    
    def parse_official_report(self, entry: Dict) -> ParsedSignal:
        """
        Parse an official NBA injury report entry.
        
        Args:
            entry: Official report entry from OfficialReportFetcher
            
        Returns:
            ParsedSignal (always returns, never None for official reports)
        """
        return ParsedSignal(
            player_name=entry.get('player_name', ''),
            status_keyword=entry.get('status', ''),
            injury_detail=entry.get('reason', ''),
            confidence='HIGH',  # Official reports are always high confidence
            raw_text=f"{entry.get('player_name')} - {entry.get('status')} - {entry.get('reason')}"
        )
    
    def batch_parse(self, items: List[Dict], item_type: str = 'rss') -> List[ParsedSignal]:
        """
        Parse multiple items in batch.
        
        Args:
            items: List of items to parse
            item_type: Type of items ('rss', 'tweet', or 'official')
            
        Returns:
            List of ParsedSignals
        """
        signals = []
        
        for item in items:
            try:
                if item_type == 'rss':
                    signal = self.parse_rss_item(item)
                elif item_type == 'tweet':
                    signal = self.parse_tweet(item)
                elif item_type == 'official':
                    signal = self.parse_official_report(item)
                else:
                    logger.warning(f"Unknown item type: {item_type}")
                    continue
                
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error parsing item: {str(e)}")
                continue
        
        logger.info(f"Parsed {len(signals)} signals from {len(items)} items")
        return signals
