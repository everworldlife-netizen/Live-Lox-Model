"""
News Ingestion Service for Live Lox

This module provides automated ingestion of NBA injury news, lineup updates,
and player status changes from multiple free sources including:
- Official NBA injury reports
- RSS feeds (RotoWire, RealGM, HoopsRumors)
- Twitter/X accounts (Underdog NBA, FantasyLabs)
"""

from .rss_poller import RSSPoller
from .twitter_monitor import TwitterMonitor
from .official_report_fetcher import OfficialReportFetcher
from .parsers import NewsParser
from .entity_resolver import EntityResolver
from .assumption_engine import AssumptionEngine

__all__ = [
    'RSSPoller',
    'TwitterMonitor',
    'OfficialReportFetcher',
    'NewsParser',
    'EntityResolver',
    'AssumptionEngine',
]
