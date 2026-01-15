"""
Official NBA Injury Report Fetcher

Uses the nbainjuries package to fetch official NBA injury reports.
This is the most authoritative source for player status.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio

logger = logging.getLogger(__name__)


class OfficialReportFetcher:
    """
    Fetches official NBA injury reports using the nbainjuries package.
    
    Official reporting times:
    - 5:00 PM local time (day before game) for most games
    - 1:00 PM local time (day of game) for back-to-backs
    
    Status values:
    - OUT: Player will not play
    - QUESTIONABLE: 50% chance of playing
    - DOUBTFUL: 25% chance of playing
    - AVAILABLE: Player will play (may have restrictions)
    - PROBABLE: 75% chance of playing (rarely used)
    """
    
    def __init__(self):
        """Initialize the official report fetcher"""
        self.last_fetch_time = None
        self._check_package_availability()
    
    def _check_package_availability(self):
        """Check if nbainjuries package is installed"""
        try:
            import nbainjuries
            self.nbainjuries_available = True
            logger.info("nbainjuries package is available")
        except ImportError:
            self.nbainjuries_available = False
            logger.warning(
                "nbainjuries package not installed. "
                "Install with: pip install nbainjuries"
            )
    
    def fetch_latest_report(self, as_dataframe: bool = False) -> Optional[List[Dict]]:
        """
        Fetch the most recent official injury report.
        
        Args:
            as_dataframe: If True, return pandas DataFrame instead of dict list
            
        Returns:
            List of injury report entries or None if unavailable
        """
        if not self.nbainjuries_available:
            logger.error("Cannot fetch report: nbainjuries package not installed")
            return None
        
        try:
            from nbainjuries import injury
            
            # Fetch the latest report (current time)
            logger.info("Fetching latest official NBA injury report")
            report_data = injury.get_reportdata(
                datetime.now(),
                return_df=as_dataframe
            )
            
            self.last_fetch_time = datetime.utcnow()
            
            if as_dataframe:
                # Convert DataFrame to list of dicts
                report_list = report_data.to_dict('records')
            else:
                report_list = report_data
            
            logger.info(f"Fetched {len(report_list)} injury report entries")
            return report_list
            
        except Exception as e:
            logger.error(f"Error fetching official injury report: {str(e)}")
            return None
    
    def fetch_report_for_date(
        self,
        target_date: datetime,
        hour: int = 17,
        minute: int = 0
    ) -> Optional[List[Dict]]:
        """
        Fetch injury report for a specific date and time.
        
        Args:
            target_date: Date to fetch report for
            hour: Hour of day (0-23, default 17 for 5 PM)
            minute: Minute of hour (0-59, default 0)
            
        Returns:
            List of injury report entries or None if unavailable
        """
        if not self.nbainjuries_available:
            return None
        
        try:
            from nbainjuries import injury
            
            report_datetime = target_date.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )
            
            logger.info(f"Fetching injury report for {report_datetime}")
            report_data = injury.get_reportdata(report_datetime)
            
            logger.info(f"Fetched {len(report_data)} entries for {report_datetime}")
            return report_data
            
        except Exception as e:
            logger.error(f"Error fetching report for {target_date}: {str(e)}")
            return None
    
    async def fetch_batch_reports_async(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Fetch multiple injury reports asynchronously for a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Combined list of all injury report entries
        """
        if not self.nbainjuries_available:
            return []
        
        try:
            from nbainjuries import injury_asy
            import asyncio
            
            logger.info(f"Fetching batch reports from {start_date} to {end_date}")
            
            # Use the async module for better performance
            all_reports = await injury_asy.get_reportdata_batch(
                start_date,
                end_date
            )
            
            logger.info(f"Fetched {len(all_reports)} total entries in batch")
            return all_reports
            
        except Exception as e:
            logger.error(f"Error in batch fetch: {str(e)}")
            return []
    
    def parse_report_entry(self, entry: Dict) -> Dict:
        """
        Parse a single injury report entry into standardized format.
        
        Args:
            entry: Raw entry from nbainjuries package
            
        Returns:
            Standardized injury report dict
        """
        return {
            'source': 'Official NBA Injury Report',
            'source_priority': 1,  # Highest priority
            'game_date': entry.get('Game Date'),
            'game_time': entry.get('Game Time'),
            'matchup': entry.get('Matchup'),
            'team': entry.get('Team'),
            'player_name': entry.get('Player Name'),
            'status': entry.get('Current Status'),
            'reason': entry.get('Reason'),
            'fetched_at': datetime.utcnow().isoformat()
        }
    
    def fetch_and_parse_latest(self) -> List[Dict]:
        """
        Fetch the latest report and parse all entries.
        
        Returns:
            List of parsed injury report entries
        """
        raw_report = self.fetch_latest_report()
        
        if not raw_report:
            return []
        
        parsed_entries = [
            self.parse_report_entry(entry)
            for entry in raw_report
        ]
        
        return parsed_entries
    
    def should_fetch_now(self) -> bool:
        """
        Determine if we should fetch a new report based on timing.
        
        Returns:
            True if it's time to fetch a new report
        """
        now = datetime.now()
        hour = now.hour
        
        # Fetch more frequently during key reporting windows
        if 16 <= hour <= 18:  # 4-6 PM ET (5 PM reporting window)
            return True
        elif 12 <= hour <= 14:  # 12-2 PM ET (1 PM back-to-back window)
            return True
        elif hour >= 19:  # Evening (games in progress)
            return True
        
        # Otherwise, fetch every hour
        if self.last_fetch_time is None:
            return True
        
        time_since_last = datetime.utcnow() - self.last_fetch_time
        return time_since_last > timedelta(hours=1)
    
    def get_status_confidence(self, status: str) -> str:
        """
        Map official status to confidence level.
        
        Args:
            status: Official status (OUT, QUESTIONABLE, etc.)
            
        Returns:
            Confidence level string
        """
        status_upper = status.upper()
        
        if status_upper == 'OUT':
            return 'HIGH'  # Certain they won't play
        elif status_upper == 'AVAILABLE':
            return 'HIGH'  # Certain they will play
        elif status_upper == 'PROBABLE':
            return 'MEDIUM'  # Likely to play
        elif status_upper == 'QUESTIONABLE':
            return 'LOW'  # Uncertain
        elif status_upper == 'DOUBTFUL':
            return 'LOW'  # Unlikely but not certain
        else:
            return 'VERY_LOW'  # Unknown status
    
    def get_minutes_multiplier(self, status: str) -> float:
        """
        Get the minutes adjustment multiplier based on status.
        
        Args:
            status: Official status
            
        Returns:
            Multiplier for projected minutes (0.0 to 1.0)
        """
        status_upper = status.upper()
        
        if status_upper == 'OUT':
            return 0.0  # No minutes
        elif status_upper == 'DOUBTFUL':
            return 0.25  # Assume 25% of normal minutes if they play
        elif status_upper == 'QUESTIONABLE':
            return 0.85  # Assume 85% of normal minutes if they play
        elif status_upper == 'PROBABLE':
            return 0.95  # Assume 95% of normal minutes
        elif status_upper == 'AVAILABLE':
            return 1.0  # Full minutes (may have restrictions noted in reason)
        else:
            return 1.0  # Default to no adjustment
