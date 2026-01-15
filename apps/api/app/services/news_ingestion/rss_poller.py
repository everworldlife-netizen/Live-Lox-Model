"""
RSS Feed Polling Service

Polls multiple NBA news RSS feeds and extracts relevant injury/lineup information.
"""

import feedparser
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RSSFeedConfig:
    """Configuration for an RSS feed source"""
    name: str
    url: str
    priority: int  # 1 = highest, 3 = lowest
    poll_interval_minutes: int
    near_lock_interval_minutes: int


class RSSPoller:
    """
    Polls RSS feeds for NBA news and extracts structured data.
    
    Supported feeds:
    - RotoWire NBA News
    - RealGM Injury Wiretap
    - Hoops Rumors
    - HoopsWire
    - General NBA news feeds
    """
    
    # RSS Feed configurations
    FEEDS = [
        RSSFeedConfig(
            name="RotoWire NBA",
            url="https://www.rotowire.com/rss/news.php?sport=NBA",
            priority=1,
            poll_interval_minutes=10,
            near_lock_interval_minutes=2
        ),
        RSSFeedConfig(
            name="RealGM Injury",
            url="https://basketball.realgm.com/rss/wiretap",
            priority=1,
            poll_interval_minutes=30,
            near_lock_interval_minutes=15
        ),
        RSSFeedConfig(
            name="Hoops Rumors",
            url="https://hoopsrumors.com/feed",
            priority=2,
            poll_interval_minutes=30,
            near_lock_interval_minutes=15
        ),
        RSSFeedConfig(
            name="HoopsWire",
            url="https://hoopswire.com/feed",
            priority=2,
            poll_interval_minutes=30,
            near_lock_interval_minutes=15
        ),
        RSSFeedConfig(
            name="HoopsHype",
            url="https://hoopshype.com/feed",
            priority=2,
            poll_interval_minutes=60,
            near_lock_interval_minutes=30
        ),
    ]
    
    def __init__(self, redis_client=None):
        """
        Initialize the RSS poller.
        
        Args:
            redis_client: Redis client for caching (optional)
        """
        self.redis_client = redis_client
        self.seen_hashes = set()
    
    def _generate_content_hash(self, url: str, title: str) -> str:
        """Generate a unique hash for deduplication"""
        content = f"{url}|{title}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _is_duplicate(self, content_hash: str) -> bool:
        """Check if this content has been seen before"""
        if self.redis_client:
            # Check Redis cache (24-hour TTL)
            key = f"rss:seen:{content_hash}"
            if self.redis_client.exists(key):
                return True
            self.redis_client.setex(key, 86400, "1")  # 24 hours
            return False
        else:
            # Fallback to in-memory set
            if content_hash in self.seen_hashes:
                return True
            self.seen_hashes.add(content_hash)
            return False
    
    def poll_feed(self, feed_config: RSSFeedConfig) -> List[Dict]:
        """
        Poll a single RSS feed and return parsed items.
        
        Args:
            feed_config: Configuration for the feed to poll
            
        Returns:
            List of dictionaries containing parsed feed items
        """
        try:
            logger.info(f"Polling RSS feed: {feed_config.name}")
            feed = feedparser.parse(feed_config.url)
            
            items = []
            for entry in feed.entries:
                # Generate content hash for deduplication
                content_hash = self._generate_content_hash(
                    entry.get('link', ''),
                    entry.get('title', '')
                )
                
                if self._is_duplicate(content_hash):
                    continue
                
                # Extract relevant fields
                item = {
                    'source': feed_config.name,
                    'source_priority': feed_config.priority,
                    'title': entry.get('title', ''),
                    'description': entry.get('description', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'content_hash': content_hash,
                    'fetched_at': datetime.utcnow().isoformat()
                }
                
                items.append(item)
            
            logger.info(f"Fetched {len(items)} new items from {feed_config.name}")
            return items
            
        except Exception as e:
            logger.error(f"Error polling {feed_config.name}: {str(e)}")
            return []
    
    def poll_all_feeds(self, near_lock: bool = False) -> List[Dict]:
        """
        Poll all configured RSS feeds.
        
        Args:
            near_lock: If True, use near-lock polling intervals
            
        Returns:
            List of all parsed feed items from all sources
        """
        all_items = []
        
        for feed_config in self.FEEDS:
            items = self.poll_feed(feed_config)
            all_items.extend(items)
        
        logger.info(f"Total items fetched from all feeds: {len(all_items)}")
        return all_items
    
    def get_feed_by_name(self, name: str) -> Optional[RSSFeedConfig]:
        """Get a specific feed configuration by name"""
        for feed in self.FEEDS:
            if feed.name == name:
                return feed
        return None
