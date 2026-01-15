"""
News Ingestion Worker

Orchestrates the entire news ingestion pipeline:
1. Poll RSS feeds
2. Monitor Twitter accounts
3. Fetch official NBA injury reports
4. Parse all signals
5. Resolve player entities
6. Create projection assumptions
7. Trigger projection updates

Runs on a schedule using APScheduler.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.news_ingestion import (
    RSSPoller,
    TwitterMonitor,
    OfficialReportFetcher,
    NewsParser,
    EntityResolver,
    AssumptionEngine
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsIngestionWorker:
    """
    Main worker that orchestrates the news ingestion pipeline.
    """
    
    def __init__(self, redis_client=None, db_connection=None):
        """
        Initialize the worker with all required services.
        
        Args:
            redis_client: Redis client for caching
            db_connection: Database connection
        """
        self.redis_client = redis_client
        self.db = db_connection
        
        # Initialize all services
        self.rss_poller = RSSPoller(redis_client=redis_client)
        self.twitter_monitor = TwitterMonitor(redis_client=redis_client)
        self.official_fetcher = OfficialReportFetcher()
        self.parser = NewsParser()
        self.entity_resolver = EntityResolver(db_connection=db_connection)
        self.assumption_engine = AssumptionEngine(db_connection=db_connection)
        
        logger.info("News Ingestion Worker initialized")
    
    def run_full_pipeline(self, near_lock: bool = False):
        """
        Run the complete news ingestion pipeline.
        
        Args:
            near_lock: If True, use near-lock polling intervals
        """
        logger.info(f"Starting news ingestion pipeline (near_lock={near_lock})")
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Fetch all news from all sources
            all_items = self._fetch_all_news(near_lock)
            logger.info(f"Fetched {len(all_items)} total news items")
            
            # Step 2: Parse all items into signals
            all_signals = self._parse_all_items(all_items)
            logger.info(f"Parsed {len(all_signals)} signals")
            
            # Step 3: Resolve player entities
            player_ids = self._resolve_entities(all_signals)
            logger.info(f"Resolved {len(player_ids)} player entities")
            
            # Step 4: Create assumptions
            assumptions = self._create_assumptions(all_signals, player_ids)
            logger.info(f"Created {len(assumptions)} assumptions")
            
            # Step 5: Save assumptions and trigger updates
            self._save_and_trigger(assumptions)
            
            # Log completion
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Pipeline completed in {duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error in news ingestion pipeline: {str(e)}", exc_info=True)
    
    def _fetch_all_news(self, near_lock: bool) -> list:
        """Fetch news from all sources"""
        all_items = []
        
        # Fetch RSS feeds
        try:
            rss_items = self.rss_poller.poll_all_feeds(near_lock=near_lock)
            all_items.extend([{**item, 'item_type': 'rss'} for item in rss_items])
        except Exception as e:
            logger.error(f"Error fetching RSS feeds: {str(e)}")
        
        # Fetch Twitter
        try:
            tweets = self.twitter_monitor.monitor_all_accounts()
            all_items.extend([{**tweet, 'item_type': 'tweet'} for tweet in tweets])
        except Exception as e:
            logger.error(f"Error monitoring Twitter: {str(e)}")
        
        # Fetch official reports (if it's time)
        try:
            if self.official_fetcher.should_fetch_now():
                official_entries = self.official_fetcher.fetch_and_parse_latest()
                all_items.extend([{**entry, 'item_type': 'official'} for entry in official_entries])
        except Exception as e:
            logger.error(f"Error fetching official reports: {str(e)}")
        
        return all_items
    
    def _parse_all_items(self, items: list) -> list:
        """Parse all items into signals"""
        signals = []
        
        # Group by type
        rss_items = [item for item in items if item.get('item_type') == 'rss']
        tweets = [item for item in items if item.get('item_type') == 'tweet']
        official = [item for item in items if item.get('item_type') == 'official']
        
        # Parse each type
        if rss_items:
            signals.extend(self.parser.batch_parse(rss_items, 'rss'))
        
        if tweets:
            signals.extend(self.parser.batch_parse(tweets, 'tweet'))
        
        if official:
            signals.extend(self.parser.batch_parse(official, 'official'))
        
        return signals
    
    def _resolve_entities(self, signals: list) -> dict:
        """Resolve player names to IDs"""
        player_names = [signal.player_name for signal in signals]
        return self.entity_resolver.resolve_batch(player_names)
    
    def _create_assumptions(self, signals: list, player_ids: dict) -> list:
        """Create assumptions from signals"""
        return self.assumption_engine.batch_create_assumptions(
            signals,
            player_ids,
            source='news_ingestion_worker'
        )
    
    def _save_and_trigger(self, assumptions: list):
        """Save assumptions and trigger projection updates"""
        for assumption in assumptions:
            try:
                # Save assumption
                self.assumption_engine.save_assumption(assumption)
                
                # Log impact
                impact = self.assumption_engine.get_impact_summary(assumption)
                logger.info(f"Assumption impact: {impact}")
                
                # TODO: Trigger projection recalculation
                # This would call your projection service to update
                # projections for the affected player
                
            except Exception as e:
                logger.error(f"Error saving assumption: {str(e)}")


def run_scheduled_job():
    """
    Entry point for scheduled job.
    This function is called by APScheduler.
    """
    logger.info("=== Starting scheduled news ingestion job ===")
    
    # TODO: Initialize Redis and DB connections
    # redis_client = redis.Redis(...)
    # db_connection = ...
    
    worker = NewsIngestionWorker(
        redis_client=None,  # Replace with actual Redis client
        db_connection=None   # Replace with actual DB connection
    )
    
    # Determine if we're in near-lock window
    now = datetime.now()
    hour = now.hour
    near_lock = (16 <= hour <= 20)  # 4 PM to 8 PM ET
    
    worker.run_full_pipeline(near_lock=near_lock)
    
    logger.info("=== Scheduled news ingestion job completed ===")


if __name__ == "__main__":
    # For manual testing
    run_scheduled_job()
