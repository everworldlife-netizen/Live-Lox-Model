"""
Assumption Engine

Converts parsed news signals into quantitative projection assumptions.
Applies rules to translate status keywords into minutes adjustments,
confidence levels, and other projection parameters.
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ProjectionAssumption:
    """
    A quantitative assumption that affects player projections.
    """
    player_id: int
    game_id: Optional[str] = None
    assumption_type: str = 'injury_status'  # injury_status, minutes_cap, lineup_change
    
    # Minutes adjustments
    minutes_multiplier: Optional[float] = None  # 0.0 to 1.0
    minutes_cap: Optional[int] = None  # Hard cap on minutes
    
    # Confidence
    confidence_level: str = 'MEDIUM'  # HIGH, MEDIUM, LOW, VERY_LOW
    
    # Metadata
    reason: str = ''
    source: str = ''
    timestamp: str = ''
    requires_verification: bool = False
    
    # Raw data
    raw_signal: Optional[Dict] = None


class AssumptionEngine:
    """
    Converts parsed news signals into projection assumptions.
    
    Applies a rule-based system to map:
    - Status keywords → Minutes multipliers
    - Minutes keywords → Minutes caps
    - Lineup keywords → Usage adjustments
    - Confidence levels → Projection confidence
    """
    
    # Status → Minutes Multiplier mapping
    STATUS_MULTIPLIERS = {
        'OUT': 0.0,
        'DOUBTFUL': 0.25,
        'QUESTIONABLE': 0.85,
        'PROBABLE': 0.95,
        'AVAILABLE': 1.0,
    }
    
    # Status → Confidence mapping
    STATUS_CONFIDENCE = {
        'OUT': 'HIGH',
        'DOUBTFUL': 'LOW',
        'QUESTIONABLE': 'LOW',
        'PROBABLE': 'MEDIUM',
        'AVAILABLE': 'HIGH',
    }
    
    # Minutes keywords → Estimated cap
    MINUTES_CAPS = {
        'RESTRICTION': 24,  # Typical minutes restriction
        'LIMITED': 28,      # Limited but not severe
        'FULL_GO': None,    # No cap
    }
    
    def __init__(self, db_connection=None):
        """
        Initialize the assumption engine.
        
        Args:
            db_connection: Database connection for storing assumptions
        """
        self.db = db_connection
    
    def create_assumption_from_signal(
        self,
        parsed_signal,
        player_id: int,
        game_id: Optional[str] = None,
        source: str = 'news'
    ) -> Optional[ProjectionAssumption]:
        """
        Create a projection assumption from a parsed signal.
        
        Args:
            parsed_signal: ParsedSignal object
            player_id: Resolved player ID
            game_id: Game ID (if known)
            source: Source identifier
            
        Returns:
            ProjectionAssumption or None
        """
        # Determine assumption type
        if parsed_signal.status_keyword:
            assumption_type = 'injury_status'
        elif parsed_signal.minutes_keyword:
            assumption_type = 'minutes_cap'
        elif parsed_signal.lineup_keyword:
            assumption_type = 'lineup_change'
        else:
            logger.warning("No actionable keyword found in signal")
            return None
        
        # Create base assumption
        assumption = ProjectionAssumption(
            player_id=player_id,
            game_id=game_id,
            assumption_type=assumption_type,
            source=source,
            timestamp=datetime.utcnow().isoformat(),
            raw_signal=asdict(parsed_signal) if parsed_signal else None
        )
        
        # Apply status rules
        if parsed_signal.status_keyword:
            self._apply_status_rules(assumption, parsed_signal)
        
        # Apply minutes rules
        if parsed_signal.minutes_keyword:
            self._apply_minutes_rules(assumption, parsed_signal)
        
        # Apply lineup rules
        if parsed_signal.lineup_keyword:
            self._apply_lineup_rules(assumption, parsed_signal)
        
        # Set confidence
        assumption.confidence_level = parsed_signal.confidence
        
        # Build reason string
        assumption.reason = self._build_reason_string(parsed_signal)
        
        return assumption
    
    def _apply_status_rules(self, assumption: ProjectionAssumption, signal):
        """Apply rules for status keywords"""
        status = signal.status_keyword
        
        if status in self.STATUS_MULTIPLIERS:
            assumption.minutes_multiplier = self.STATUS_MULTIPLIERS[status]
            
            # Adjust confidence based on status
            if status in self.STATUS_CONFIDENCE:
                assumption.confidence_level = self.STATUS_CONFIDENCE[status]
        
        # Special case: OUT status requires no further adjustments
        if status == 'OUT':
            assumption.minutes_multiplier = 0.0
            assumption.confidence_level = 'HIGH'
    
    def _apply_minutes_rules(self, assumption: ProjectionAssumption, signal):
        """Apply rules for minutes keywords"""
        minutes_keyword = signal.minutes_keyword
        
        if minutes_keyword in self.MINUTES_CAPS:
            cap = self.MINUTES_CAPS[minutes_keyword]
            if cap:
                assumption.minutes_cap = cap
                assumption.confidence_level = 'MEDIUM'
    
    def _apply_lineup_rules(self, assumption: ProjectionAssumption, signal):
        """Apply rules for lineup keywords"""
        lineup_keyword = signal.lineup_keyword
        
        if lineup_keyword == 'STARTING':
            # Player moving to starting lineup
            assumption.minutes_multiplier = 1.15  # Expect more minutes
            assumption.confidence_level = 'MEDIUM'
        elif lineup_keyword == 'BENCH':
            # Player moving to bench
            assumption.minutes_multiplier = 0.75  # Expect fewer minutes
            assumption.confidence_level = 'MEDIUM'
    
    def _build_reason_string(self, signal) -> str:
        """Build a human-readable reason string"""
        parts = []
        
        if signal.status_keyword:
            parts.append(signal.status_keyword)
        
        if signal.injury_detail:
            parts.append(f"({signal.injury_detail})")
        
        if signal.minutes_keyword:
            parts.append(signal.minutes_keyword)
        
        if signal.lineup_keyword:
            parts.append(signal.lineup_keyword)
        
        reason = " - ".join(parts) if parts else "News update"
        
        # Add source info
        if signal.raw_text:
            reason += f" | Source: {signal.raw_text[:100]}"
        
        return reason
    
    def merge_assumptions(
        self,
        existing: ProjectionAssumption,
        new: ProjectionAssumption
    ) -> ProjectionAssumption:
        """
        Merge a new assumption with an existing one.
        Uses source priority to resolve conflicts.
        
        Args:
            existing: Existing assumption
            new: New assumption
            
        Returns:
            Merged assumption
        """
        # Determine which source has higher priority
        source_priority = {
            'official_nba_injury_report': 1,
            'underdog_nba_twitter': 2,
            'rotowire_rss': 2,
            'beat_writer_twitter': 3,
            'general_news': 4,
        }
        
        existing_priority = source_priority.get(existing.source, 5)
        new_priority = source_priority.get(new.source, 5)
        
        # Higher priority source wins (lower number = higher priority)
        if new_priority < existing_priority:
            logger.info(f"New assumption has higher priority, replacing existing")
            return new
        elif new_priority == existing_priority:
            # Same priority, use most recent
            logger.info(f"Same priority, using most recent assumption")
            return new if new.timestamp > existing.timestamp else existing
        else:
            logger.info(f"Existing assumption has higher priority, keeping it")
            return existing
    
    def save_assumption(self, assumption: ProjectionAssumption) -> bool:
        """
        Save assumption to database.
        
        Args:
            assumption: Assumption to save
            
        Returns:
            True if saved successfully
        """
        if not self.db:
            logger.warning("No database connection, cannot save assumption")
            return False
        
        try:
            # This would insert into your player_assumptions table
            # For now, we'll just log it
            logger.info(f"Saving assumption: {assumption}")
            
            # In production, replace with actual DB insert:
            # self.db.execute(
            #     """
            #     INSERT INTO player_assumptions 
            #     (player_id, game_id, assumption_type, minutes_multiplier, 
            #      minutes_cap, confidence_level, reason, source, timestamp)
            #     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            #     """,
            #     (assumption.player_id, assumption.game_id, assumption.assumption_type,
            #      assumption.minutes_multiplier, assumption.minutes_cap,
            #      assumption.confidence_level, assumption.reason,
            #      assumption.source, assumption.timestamp)
            # )
            
            return True
        except Exception as e:
            logger.error(f"Error saving assumption: {str(e)}")
            return False
    
    def batch_create_assumptions(
        self,
        signals: List,
        player_ids: Dict[str, int],
        game_id: Optional[str] = None,
        source: str = 'news'
    ) -> List[ProjectionAssumption]:
        """
        Create assumptions for multiple signals in batch.
        
        Args:
            signals: List of ParsedSignal objects
            player_ids: Dict mapping player names to IDs
            game_id: Game ID (if known)
            source: Source identifier
            
        Returns:
            List of created assumptions
        """
        assumptions = []
        
        for signal in signals:
            player_id = player_ids.get(signal.player_name)
            if not player_id:
                logger.warning(f"No player ID for {signal.player_name}, skipping")
                continue
            
            assumption = self.create_assumption_from_signal(
                signal,
                player_id,
                game_id,
                source
            )
            
            if assumption:
                assumptions.append(assumption)
        
        logger.info(f"Created {len(assumptions)} assumptions from {len(signals)} signals")
        return assumptions
    
    def get_impact_summary(self, assumption: ProjectionAssumption) -> Dict:
        """
        Generate a summary of how this assumption impacts projections.
        
        Args:
            assumption: Assumption to summarize
            
        Returns:
            Dict with impact summary
        """
        summary = {
            'player_id': assumption.player_id,
            'impact_type': assumption.assumption_type,
            'confidence': assumption.confidence_level,
            'reason': assumption.reason,
        }
        
        if assumption.minutes_multiplier is not None:
            summary['minutes_impact'] = f"{assumption.minutes_multiplier * 100:.0f}%"
        
        if assumption.minutes_cap is not None:
            summary['minutes_cap'] = assumption.minutes_cap
        
        return summary
