"""
Twitter/X Monitoring Service

Monitors key NBA Twitter accounts for injury and lineup alerts.
Supports both Twitter API v2 and RSS-to-Twitter bridge fallback.
"""

import logging
import hashlib
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
import feedparser

logger = logging.getLogger(__name__)


@dataclass
class TwitterAccountConfig:
    """Configuration for a Twitter account to monitor"""
    handle: str
    display_name: str
    priority: int  # 1 = highest
    rss_bridge_url: Optional[str] = None


class TwitterMonitor:
    """
    Monitors Twitter/X accounts for NBA news using RSS bridges.
    
    Key accounts monitored:
    - @UnderdogNBA (fastest injury alerts)
    - @FantasyLabsNBA (structured lineup news)
    - @RotoWireNBA (fantasy-focused updates)
    - Team beat writers (30 accounts)
    """
    
    # Twitter account configurations
    ACCOUNTS = [
        TwitterAccountConfig(
            handle="UnderdogNBA",
            display_name="Underdog NBA",
            priority=1,
            rss_bridge_url="https://nitter.net/UnderdogNBA/rss"
        ),
        TwitterAccountConfig(
            handle="FantasyLabsNBA",
            display_name="FantasyLabs NBA",
            priority=1,
            rss_bridge_url="https://nitter.net/FantasyLabsNBA/rss"
        ),
        TwitterAccountConfig(
            handle="RotoWireNBA",
            display_name="RotoWire NBA",
            priority=1,
            rss_bridge_url="https://nitter.net/RotoWireNBA/rss"
        ),
        TwitterAccountConfig(
            handle="InStreetClothes",
            display_name="Jeff Stotts (Injury Expert)",
            priority=2,
            rss_bridge_url="https://nitter.net/InStreetClothes/rss"
        ),
    ]
    
    # Alert keywords for filtering
    ALERT_KEYWORDS = [
        'status alert',
        'lineup alert',
        'injury alert',
        'OUT',
        'QUESTIONABLE',
        'DOUBTFUL',
        'GTD',
        'won\'t return',
        'ruled out',
        'starting lineup',
        'will start',
        'moves to bench',
    ]
    
    def __init__(self, redis_client=None, twitter_api_key: Optional[str] = None):
        """
        Initialize the Twitter monitor.
        
        Args:
            redis_client: Redis client for caching (optional)
            twitter_api_key: Twitter API v2 bearer token (optional)
        """
        self.redis_client = redis_client
        self.twitter_api_key = twitter_api_key
        self.seen_hashes = set()
    
    def _generate_tweet_hash(self, handle: str, text: str, timestamp: str) -> str:
        """Generate a unique hash for tweet deduplication"""
        content = f"{handle}|{text}|{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _is_duplicate(self, tweet_hash: str) -> bool:
        """Check if this tweet has been seen before"""
        if self.redis_client:
            key = f"twitter:seen:{tweet_hash}"
            if self.redis_client.exists(key):
                return True
            self.redis_client.setex(key, 86400, "1")  # 24 hours
            return False
        else:
            if tweet_hash in self.seen_hashes:
                return True
            self.seen_hashes.add(tweet_hash)
            return False
    
    def _contains_alert_keyword(self, text: str) -> bool:
        """Check if tweet contains any alert keywords"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.ALERT_KEYWORDS)
    
    def _monitor_via_rss_bridge(self, account: TwitterAccountConfig) -> List[Dict]:
        """
        Monitor a Twitter account using RSS bridge (Nitter).
        
        Args:
            account: Account configuration
            
        Returns:
            List of parsed tweets
        """
        if not account.rss_bridge_url:
            return []
        
        try:
            logger.info(f"Monitoring @{account.handle} via RSS bridge")
            feed = feedparser.parse(account.rss_bridge_url)
            
            tweets = []
            for entry in feed.entries:
                text = entry.get('title', '') or entry.get('description', '')
                
                # Filter for relevant tweets
                if not self._contains_alert_keyword(text):
                    continue
                
                # Generate hash for deduplication
                tweet_hash = self._generate_tweet_hash(
                    account.handle,
                    text,
                    entry.get('published', '')
                )
                
                if self._is_duplicate(tweet_hash):
                    continue
                
                tweet = {
                    'source': f"Twitter/@{account.handle}",
                    'source_priority': account.priority,
                    'handle': account.handle,
                    'display_name': account.display_name,
                    'text': text,
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'tweet_hash': tweet_hash,
                    'fetched_at': datetime.utcnow().isoformat()
                }
                
                tweets.append(tweet)
            
            logger.info(f"Fetched {len(tweets)} relevant tweets from @{account.handle}")
            return tweets
            
        except Exception as e:
            logger.error(f"Error monitoring @{account.handle}: {str(e)}")
            return []
    
    def monitor_all_accounts(self) -> List[Dict]:
        """
        Monitor all configured Twitter accounts.
        
        Returns:
            List of all relevant tweets from all accounts
        """
        all_tweets = []
        
        for account in self.ACCOUNTS:
            tweets = self._monitor_via_rss_bridge(account)
            all_tweets.extend(tweets)
        
        logger.info(f"Total relevant tweets fetched: {len(all_tweets)}")
        return all_tweets
    
    def add_custom_account(self, handle: str, display_name: str, priority: int = 2):
        """
        Add a custom Twitter account to monitor (e.g., team beat writer).
        
        Args:
            handle: Twitter handle without @
            display_name: Display name for the account
            priority: Priority level (1-3)
        """
        account = TwitterAccountConfig(
            handle=handle,
            display_name=display_name,
            priority=priority,
            rss_bridge_url=f"https://nitter.net/{handle}/rss"
        )
        self.ACCOUNTS.append(account)
        logger.info(f"Added custom account: @{handle}")
    
    def add_beat_writers(self):
        """
        Add all 30 NBA team beat writers to monitoring.
        This is a curated list of the most reliable beat writers per team.
        """
        beat_writers = [
            ("ChrisBHaynes", "Chris Haynes (General)", 2),
            ("ShamsCharania", "Shams Charania (General)", 2),
            ("wojespn", "Adrian Wojnarowski (General)", 2),
            ("JaredWeissNBA", "Jared Weiss (Celtics)", 2),
            ("NYPost_Lewis", "Brian Lewis (Nets)", 2),
            ("IanBegley", "Ian Begley (Knicks)", 2),
            ("SerenaWinters", "Serena Winters (76ers)", 2),
            ("JLew1050", "Josh Lewenberg (Raptors)", 2),
            ("KCJHoop", "KC Johnson (Bulls)", 2),
            ("CavsFredNBA", "Chris Fedor (Cavaliers)", 2),
            ("JLEdwardsIII", "James Edwards III (Pistons)", 2),
            ("JimOwczarski", "Jim Owczarski (Bucks)", 2),
            ("Pacers", "Indiana Pacers (Official)", 1),
            ("ByJayKing", "Jay King (Celtics)", 2),
            ("CharlotteHornets", "Charlotte Hornets (Official)", 1),
            ("MiamiHEAT", "Miami Heat (Official)", 1),
            ("OrlandoMagic", "Orlando Magic (Official)", 1),
            ("ATLHawks", "Atlanta Hawks (Official)", 1),
            ("WashWizards", "Washington Wizards (Official)", 1),
            ("nuggets", "Denver Nuggets (Official)", 1),
            ("Timberwolves", "Minnesota Timberwolves (Official)", 1),
            ("okcthunder", "Oklahoma City Thunder (Official)", 1),
            ("trailblazers", "Portland Trail Blazers (Official)", 1),
            ("utahjazz", "Utah Jazz (Official)", 1),
            ("warriors", "Golden State Warriors (Official)", 1),
            ("LAClippers", "LA Clippers (Official)", 1),
            ("Lakers", "Los Angeles Lakers (Official)", 1),
            ("Suns", "Phoenix Suns (Official)", 1),
            ("SacramentoKings", "Sacramento Kings (Official)", 1),
            ("dallasmavs", "Dallas Mavericks (Official)", 1),
            ("HoustonRockets", "Houston Rockets (Official)", 1),
            ("memgrizz", "Memphis Grizzlies (Official)", 1),
            ("PelicansNBA", "New Orleans Pelicans (Official)", 1),
            ("spurs", "San Antonio Spurs (Official)", 1),
        ]
        
        for handle, display_name, priority in beat_writers:
            self.add_custom_account(handle, display_name, priority)
        
        logger.info(f"Added {len(beat_writers)} beat writers and team accounts")
