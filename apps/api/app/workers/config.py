"""
Configuration for News Ingestion Worker

Defines polling schedules and source priorities.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)


class NewsIngestionConfig:
    """Configuration for news ingestion service"""
    
    # Polling intervals (in minutes)
    RSS_POLL_INTERVAL_NORMAL = 15
    RSS_POLL_INTERVAL_NEAR_LOCK = 5
    
    TWITTER_POLL_INTERVAL_NORMAL = 10
    TWITTER_POLL_INTERVAL_NEAR_LOCK = 2
    
    OFFICIAL_REPORT_INTERVAL = 60  # Check every hour
    
    # Near-lock window (hours in ET)
    NEAR_LOCK_START_HOUR = 16  # 4 PM ET
    NEAR_LOCK_END_HOUR = 22    # 10 PM ET
    
    # Source priorities (1 = highest)
    SOURCE_PRIORITIES = {
        'official_nba_injury_report': 1,
        'underdog_nba_twitter': 2,
        'fantasylabs_nba_twitter': 2,
        'rotowire_rss': 2,
        'realgm_rss': 2,
        'beat_writer_twitter': 3,
        'general_news_rss': 3,
    }


def setup_scheduler(worker):
    """
    Set up APScheduler with cron jobs for news ingestion.
    
    Args:
        worker: NewsIngestionWorker instance
        
    Returns:
        Configured scheduler
    """
    scheduler = BackgroundScheduler()
    
    # Job 1: Normal polling (every 15 minutes during off-peak)
    scheduler.add_job(
        func=lambda: worker.run_full_pipeline(near_lock=False),
        trigger=CronTrigger(minute='*/15', hour='0-15,23'),  # Off-peak hours
        id='news_ingestion_normal',
        name='News Ingestion (Normal)',
        replace_existing=True
    )
    
    # Job 2: Near-lock polling (every 5 minutes during peak)
    scheduler.add_job(
        func=lambda: worker.run_full_pipeline(near_lock=True),
        trigger=CronTrigger(minute='*/5', hour='16-22'),  # Peak hours (4 PM - 10 PM ET)
        id='news_ingestion_near_lock',
        name='News Ingestion (Near-Lock)',
        replace_existing=True
    )
    
    # Job 3: Official report fetch (every hour at :05)
    scheduler.add_job(
        func=lambda: worker.official_fetcher.fetch_and_parse_latest(),
        trigger=CronTrigger(minute='5'),
        id='official_report_fetch',
        name='Official NBA Injury Report Fetch',
        replace_existing=True
    )
    
    logger.info("News ingestion scheduler configured")
    return scheduler


def start_news_ingestion_service(redis_client=None, db_connection=None):
    """
    Start the news ingestion service with scheduled jobs.
    
    Args:
        redis_client: Redis client for caching
        db_connection: Database connection
    """
    from .run_news_ingestion import NewsIngestionWorker
    
    # Initialize worker
    worker = NewsIngestionWorker(
        redis_client=redis_client,
        db_connection=db_connection
    )
    
    # Set up scheduler
    scheduler = setup_scheduler(worker)
    
    # Start scheduler
    scheduler.start()
    logger.info("News ingestion service started")
    
    return scheduler
