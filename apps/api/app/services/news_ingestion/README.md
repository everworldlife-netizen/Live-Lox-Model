# News Ingestion Service

## Overview

The News Ingestion Service automatically monitors multiple free NBA data sources to capture real-time injury news, lineup changes, and player status updates. It converts this unstructured news into quantitative projection assumptions that enhance the accuracy of Live Lox's pregame projections.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    News Ingestion Pipeline                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │         Data Collection Layer          │
         ├────────────────────────────────────────┤
         │  • RSS Poller (5 feeds)                │
         │  • Twitter Monitor (34+ accounts)      │
         │  • Official NBA Reports (nbainjuries)  │
         └────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │         Parsing & Extraction           │
         ├────────────────────────────────────────┤
         │  • Keyword Detection                   │
         │  • Player Name Extraction              │
         │  • Status/Injury/Lineup Parsing        │
         └────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │         Entity Resolution              │
         ├────────────────────────────────────────┤
         │  • Exact Match                         │
         │  • Alias Lookup                        │
         │  • Fuzzy Matching                      │
         └────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │        Assumption Generation           │
         ├────────────────────────────────────────┤
         │  • Status → Minutes Multiplier         │
         │  • Minutes Keywords → Caps             │
         │  • Confidence Scoring                  │
         └────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │      Database & Projection Update      │
         ├────────────────────────────────────────┤
         │  • Save Assumptions                    │
         │  • Trigger Recalculation               │
         │  • Log Changes                         │
         └────────────────────────────────────────┘
```

## Data Sources

### Tier 1: Official & High-Speed (Highest Priority)

1. **Official NBA Injury Reports** (via `nbainjuries` package)
   - Source: NBA.com official reports
   - Update frequency: Hourly (5 PM & 1 PM ET reporting windows)
   - Reliability: 100% (official source)
   - Data structure: Highly structured JSON/DataFrame

2. **Underdog NBA** (@UnderdogNBA on Twitter/X)
   - Source: Twitter via Nitter RSS bridge
   - Update frequency: Real-time (2-5 min polling)
   - Reliability: 95% (industry standard)
   - Data structure: Templated tweets

3. **FantasyLabs NBA** (@FantasyLabsNBA on Twitter/X)
   - Source: Twitter via Nitter RSS bridge
   - Update frequency: Real-time (2-5 min polling)
   - Reliability: 95%
   - Data structure: Structured alerts

### Tier 2: Reliable News Sources

4. **RotoWire NBA News RSS**
   - URL: https://www.rotowire.com/rss/news.php?sport=NBA
   - Update frequency: 10-15 minutes
   - Reliability: 90% (fantasy-focused)
   - Data structure: Structured titles

5. **RealGM Injury Wiretap RSS**
   - URL: https://basketball.realgm.com/rss/wiretap
   - Update frequency: 30 minutes
   - Reliability: 85%
   - Data structure: Article format with tags

6. **Hoops Rumors RSS**
   - URL: https://hoopsrumors.com/feed
   - Update frequency: 30 minutes
   - Reliability: 85%
   - Data structure: Article headlines

### Tier 3: Contextual & Beat Writers

7. **Team Official Accounts** (30 NBA teams)
   - Source: Twitter via Nitter
   - Update frequency: 10 minutes
   - Reliability: 100% for lineup announcements
   - Data structure: Natural language

8. **Beat Writers** (curated list)
   - Source: Twitter via Nitter
   - Update frequency: 10 minutes
   - Reliability: 75% (early signals)
   - Data structure: Natural language

## Installation

### 1. Install Dependencies

```bash
cd apps/api
pip install -r requirements_news_ingestion.txt
```

Key dependencies:
- `nbainjuries==1.0.0` - Official NBA injury reports
- `feedparser==6.0.11` - RSS feed parsing
- `thefuzz==0.22.1` - Fuzzy string matching
- `APScheduler==3.10.4` - Job scheduling
- `redis==5.0.1` - Caching

### 2. Install Java (Required for nbainjuries)

The `nbainjuries` package uses `tabula-py` which requires Java 8+.

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install default-jre

# Verify installation
java -version
```

### 3. Configure Environment Variables

Add to your `.env` file:

```bash
# Redis (for deduplication caching)
REDIS_URL=redis://redis:6379

# Optional: Twitter API (for direct API access instead of RSS bridge)
TWITTER_API_KEY=your_twitter_api_key_here
```

## Usage

### Running Manually

```python
from app.services.news_ingestion import (
    RSSPoller,
    TwitterMonitor,
    OfficialReportFetcher,
    NewsParser,
    EntityResolver,
    AssumptionEngine
)

# Initialize services
rss_poller = RSSPoller()
twitter_monitor = TwitterMonitor()
official_fetcher = OfficialReportFetcher()

# Fetch news
rss_items = rss_poller.poll_all_feeds()
tweets = twitter_monitor.monitor_all_accounts()
official_reports = official_fetcher.fetch_and_parse_latest()

# Parse signals
parser = NewsParser()
signals = parser.batch_parse(rss_items, 'rss')

# Resolve players
resolver = EntityResolver()
player_ids = resolver.resolve_batch([s.player_name for s in signals])

# Create assumptions
engine = AssumptionEngine()
assumptions = engine.batch_create_assumptions(signals, player_ids)
```

### Running as Scheduled Worker

```python
from app.workers.config import start_news_ingestion_service

# Start the service (runs in background)
scheduler = start_news_ingestion_service(
    redis_client=redis_client,
    db_connection=db_connection
)

# Service will run on schedule:
# - Every 15 minutes during off-peak (12 AM - 3 PM ET)
# - Every 5 minutes during peak (4 PM - 10 PM ET)
# - Official reports fetched hourly
```

### Integrating with FastAPI

Add to your `main.py`:

```python
from app.workers.config import start_news_ingestion_service
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start news ingestion service
    scheduler = start_news_ingestion_service(
        redis_client=redis_client,
        db_connection=db
    )
    
    yield
    
    # Shutdown: Stop scheduler
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
```

## Configuration

### Polling Intervals

Edit `apps/api/app/workers/config.py`:

```python
class NewsIngestionConfig:
    RSS_POLL_INTERVAL_NORMAL = 15      # minutes
    RSS_POLL_INTERVAL_NEAR_LOCK = 5    # minutes
    
    TWITTER_POLL_INTERVAL_NORMAL = 10  # minutes
    TWITTER_POLL_INTERVAL_NEAR_LOCK = 2 # minutes
    
    NEAR_LOCK_START_HOUR = 16  # 4 PM ET
    NEAR_LOCK_END_HOUR = 22    # 10 PM ET
```

### Adding Custom Sources

#### Add RSS Feed

```python
from app.services.news_ingestion import RSSPoller, RSSFeedConfig

poller = RSSPoller()
custom_feed = RSSFeedConfig(
    name="Custom NBA News",
    url="https://example.com/nba/rss",
    priority=2,
    poll_interval_minutes=30,
    near_lock_interval_minutes=15
)
poller.FEEDS.append(custom_feed)
```

#### Add Twitter Account

```python
from app.services.news_ingestion import TwitterMonitor

monitor = TwitterMonitor()
monitor.add_custom_account(
    handle="CustomNBAReporter",
    display_name="Custom NBA Reporter",
    priority=2
)
```

#### Add Player Alias

```python
from app.services.news_ingestion import EntityResolver

resolver = EntityResolver()
resolver.add_alias("Spida", "Donovan Mitchell")
```

## Keyword Detection

### Status Keywords

The parser recognizes these status keywords:

- **OUT**: `out`, `ruled out`, `won't return`, `will not play`, `sidelined`
- **QUESTIONABLE**: `questionable`, `game-time decision`, `gtd`
- **DOUBTFUL**: `doubtful`, `unlikely to play`, `not expected to play`
- **PROBABLE**: `probable`, `likely to play`, `expected to play`
- **AVAILABLE**: `available`, `cleared to play`, `will play`, `active`

### Minutes Keywords

- **RESTRICTION**: `minutes restriction`, `minutes limit`, `limited minutes`
- **FULL_GO**: `full go`, `no restrictions`, `unrestricted`
- **LIMITED**: `limited`, `cautious`, `eased back`, `monitored`

### Lineup Keywords

- **STARTING**: `will start`, `starting`, `moves into starting lineup`
- **BENCH**: `moves to bench`, `coming off bench`, `bench role`

## Assumption Rules

### Status → Minutes Multiplier

| Status | Multiplier | Confidence |
|--------|-----------|------------|
| OUT | 0.0 | HIGH |
| DOUBTFUL | 0.25 | LOW |
| QUESTIONABLE | 0.85 | LOW |
| PROBABLE | 0.95 | MEDIUM |
| AVAILABLE | 1.0 | HIGH |

### Minutes Keywords → Caps

| Keyword | Minutes Cap |
|---------|-------------|
| RESTRICTION | 24 |
| LIMITED | 28 |
| FULL_GO | None |

### Lineup Changes

| Change | Multiplier |
|--------|-----------|
| STARTING | 1.15 |
| BENCH | 0.75 |

## Deduplication

The service uses two-layer deduplication:

1. **Content Hash**: SHA256 of `(url, title)` cached in Redis for 24 hours
2. **Signal Hash**: SHA256 of `(player_id, status, source)` to prevent duplicate assumptions

## Error Handling

- Failed RSS fetches are logged but don't stop the pipeline
- Unresolved player names are logged and skipped
- Parsing errors are caught per-item, not per-batch
- All errors include full stack traces in logs

## Monitoring

### Logs

All operations are logged with timestamps:

```
2026-01-15 10:00:00 - RSSPoller - INFO - Polling RSS feed: RotoWire NBA
2026-01-15 10:00:02 - RSSPoller - INFO - Fetched 5 new items from RotoWire NBA
2026-01-15 10:00:03 - NewsParser - INFO - Parsed 5 signals from 5 items
2026-01-15 10:00:04 - EntityResolver - INFO - Resolved 5/5 player names
2026-01-15 10:00:05 - AssumptionEngine - INFO - Created 5 assumptions from 5 signals
```

### Metrics to Track

- Items fetched per source per hour
- Signals parsed per hour
- Player resolution success rate
- Assumptions created per hour
- Average pipeline duration

## Troubleshooting

### nbainjuries package not working

**Error**: `ImportError: No module named 'nbainjuries'`

**Solution**:
```bash
pip install nbainjuries
```

**Error**: `Java not found`

**Solution**:
```bash
sudo apt-get install default-jre
java -version  # Verify
```

### RSS feeds not updating

**Check**:
1. Is Redis running? `redis-cli ping`
2. Are feeds accessible? `curl https://www.rotowire.com/rss/news.php?sport=NBA`
3. Check logs for HTTP errors

### Player names not resolving

**Solution**:
1. Check if player is in database: `SELECT * FROM players WHERE full_name LIKE '%Player%'`
2. Add alias if needed: `resolver.add_alias("Nickname", "Full Name")`
3. Lower fuzzy match threshold (default 0.85)

### Scheduler not running

**Check**:
1. Is APScheduler installed? `pip show APScheduler`
2. Is scheduler started? Check logs for "News ingestion scheduler configured"
3. Verify cron expressions in `config.py`

## Future Enhancements

1. **Advanced NLP**: Use spaCy or transformers for better entity extraction
2. **Sentiment Analysis**: Gauge injury severity from language
3. **Historical Tracking**: Log all signals for model training
4. **Real-time Webhooks**: Replace polling with webhooks where available
5. **Machine Learning**: Train a model to predict minutes impact from news text

## License

This service uses publicly available data sources. Ensure compliance with each source's terms of service:

- Official NBA data: Public domain
- RSS feeds: Respect robots.txt and rate limits
- Twitter: Comply with Twitter's Developer Agreement (if using API)

For internal, non-commercial use only.
