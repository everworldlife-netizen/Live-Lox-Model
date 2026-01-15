"""
Tests for News Ingestion Service

Run with: pytest tests/test_news_ingestion.py -v
"""

import pytest
from datetime import datetime
from app.services.news_ingestion import (
    RSSPoller,
    TwitterMonitor,
    OfficialReportFetcher,
    NewsParser,
    EntityResolver,
    AssumptionEngine
)
from app.services.news_ingestion.parsers import ParsedSignal


class TestRSSPoller:
    """Tests for RSS polling service"""
    
    def test_initialization(self):
        poller = RSSPoller()
        assert len(poller.FEEDS) >= 5
        assert poller.seen_hashes == set()
    
    def test_content_hash_generation(self):
        poller = RSSPoller()
        hash1 = poller._generate_content_hash("url1", "title1")
        hash2 = poller._generate_content_hash("url1", "title1")
        hash3 = poller._generate_content_hash("url2", "title2")
        
        assert hash1 == hash2  # Same content = same hash
        assert hash1 != hash3  # Different content = different hash
    
    def test_duplicate_detection(self):
        poller = RSSPoller()
        hash1 = "test_hash_123"
        
        assert not poller._is_duplicate(hash1)  # First time
        assert poller._is_duplicate(hash1)      # Second time (duplicate)


class TestTwitterMonitor:
    """Tests for Twitter monitoring service"""
    
    def test_initialization(self):
        monitor = TwitterMonitor()
        assert len(monitor.ACCOUNTS) >= 4
        assert len(monitor.ALERT_KEYWORDS) > 0
    
    def test_alert_keyword_detection(self):
        monitor = TwitterMonitor()
        
        assert monitor._contains_alert_keyword("Status alert: LeBron OUT")
        assert monitor._contains_alert_keyword("Lineup alert: Steph will start")
        assert not monitor._contains_alert_keyword("Random tweet about basketball")
    
    def test_add_custom_account(self):
        monitor = TwitterMonitor()
        initial_count = len(monitor.ACCOUNTS)
        
        monitor.add_custom_account("TestAccount", "Test Account", 2)
        assert len(monitor.ACCOUNTS) == initial_count + 1


class TestOfficialReportFetcher:
    """Tests for official NBA injury report fetcher"""
    
    def test_initialization(self):
        fetcher = OfficialReportFetcher()
        assert fetcher.last_fetch_time is None
    
    def test_status_confidence_mapping(self):
        fetcher = OfficialReportFetcher()
        
        assert fetcher.get_status_confidence('OUT') == 'HIGH'
        assert fetcher.get_status_confidence('QUESTIONABLE') == 'LOW'
        assert fetcher.get_status_confidence('AVAILABLE') == 'HIGH'
    
    def test_minutes_multiplier_mapping(self):
        fetcher = OfficialReportFetcher()
        
        assert fetcher.get_minutes_multiplier('OUT') == 0.0
        assert fetcher.get_minutes_multiplier('DOUBTFUL') == 0.25
        assert fetcher.get_minutes_multiplier('QUESTIONABLE') == 0.85
        assert fetcher.get_minutes_multiplier('AVAILABLE') == 1.0
    
    def test_should_fetch_now(self):
        fetcher = OfficialReportFetcher()
        # Should always return True on first call
        assert fetcher.should_fetch_now() == True


class TestNewsParser:
    """Tests for news parsing service"""
    
    def test_initialization(self):
        parser = NewsParser()
        assert len(parser.STATUS_KEYWORDS) > 0
        assert len(parser.MINUTES_KEYWORDS) > 0
    
    def test_player_name_extraction(self):
        parser = NewsParser()
        text = "LeBron James is questionable for tonight's game"
        names = parser.extract_player_names(text)
        
        assert "LeBron James" in names
    
    def test_status_keyword_extraction(self):
        parser = NewsParser()
        
        result = parser.extract_status_keyword("Player is OUT tonight")
        assert result is not None
        assert result[0] == 'OUT'
        
        result = parser.extract_status_keyword("Player is questionable")
        assert result is not None
        assert result[0] == 'QUESTIONABLE'
    
    def test_minutes_keyword_extraction(self):
        parser = NewsParser()
        
        result = parser.extract_minutes_keyword("Player has minutes restriction")
        assert result is not None
        assert result[0] == 'RESTRICTION'
    
    def test_lineup_keyword_extraction(self):
        parser = NewsParser()
        
        result = parser.extract_lineup_keyword("Player will start tonight")
        assert result is not None
        assert result[0] == 'STARTING'
    
    def test_parse_rss_item(self):
        parser = NewsParser()
        
        item = {
            'title': 'LeBron James: Ruled out for Wednesday',
            'description': 'LeBron will miss the game due to ankle injury',
            'source_priority': 1
        }
        
        signal = parser.parse_rss_item(item)
        assert signal is not None
        assert signal.player_name == 'LeBron James'
        assert signal.status_keyword == 'OUT'
        assert signal.confidence == 'HIGH'


class TestEntityResolver:
    """Tests for entity resolution service"""
    
    def test_initialization(self):
        resolver = EntityResolver()
        assert len(resolver.PLAYER_ALIASES) > 0
    
    def test_alias_lookup(self):
        resolver = EntityResolver()
        
        assert resolver._alias_lookup('LeBron') == 'LeBron James'
        assert resolver._alias_lookup('Giannis') == 'Giannis Antetokounmpo'
        assert resolver._alias_lookup('KD') == 'Kevin Durant'
    
    def test_add_custom_alias(self):
        resolver = EntityResolver()
        resolver.add_alias('Test Nickname', 'Test Player')
        
        assert resolver._alias_lookup('Test Nickname') == 'Test Player'


class TestAssumptionEngine:
    """Tests for assumption generation engine"""
    
    def test_initialization(self):
        engine = AssumptionEngine()
        assert len(engine.STATUS_MULTIPLIERS) > 0
        assert len(engine.STATUS_CONFIDENCE) > 0
    
    def test_status_multiplier_mapping(self):
        engine = AssumptionEngine()
        
        assert engine.STATUS_MULTIPLIERS['OUT'] == 0.0
        assert engine.STATUS_MULTIPLIERS['QUESTIONABLE'] == 0.85
        assert engine.STATUS_MULTIPLIERS['AVAILABLE'] == 1.0
    
    def test_create_assumption_from_signal(self):
        engine = AssumptionEngine()
        
        signal = ParsedSignal(
            player_name='LeBron James',
            status_keyword='OUT',
            injury_detail='ankle sprain',
            confidence='HIGH',
            raw_text='LeBron James ruled out with ankle sprain'
        )
        
        assumption = engine.create_assumption_from_signal(
            signal,
            player_id=2544,
            game_id='game_123',
            source='test'
        )
        
        assert assumption is not None
        assert assumption.player_id == 2544
        assert assumption.minutes_multiplier == 0.0
        assert assumption.confidence_level == 'HIGH'
        assert 'OUT' in assumption.reason
    
    def test_minutes_cap_application(self):
        engine = AssumptionEngine()
        
        signal = ParsedSignal(
            player_name='Test Player',
            minutes_keyword='RESTRICTION',
            confidence='MEDIUM',
            raw_text='Player has minutes restriction'
        )
        
        assumption = engine.create_assumption_from_signal(
            signal,
            player_id=1234,
            source='test'
        )
        
        assert assumption is not None
        assert assumption.minutes_cap == 24
    
    def test_get_impact_summary(self):
        engine = AssumptionEngine()
        
        signal = ParsedSignal(
            player_name='Test Player',
            status_keyword='QUESTIONABLE',
            confidence='LOW',
            raw_text='Test'
        )
        
        assumption = engine.create_assumption_from_signal(
            signal,
            player_id=1234,
            source='test'
        )
        
        summary = engine.get_impact_summary(assumption)
        
        assert 'player_id' in summary
        assert 'confidence' in summary
        assert summary['player_id'] == 1234


class TestIntegration:
    """Integration tests for the full pipeline"""
    
    def test_full_pipeline_mock(self):
        """Test the full pipeline with mock data"""
        
        # Step 1: Parse a mock RSS item
        parser = NewsParser()
        mock_item = {
            'title': 'Stephen Curry: Questionable for tonight',
            'description': 'Curry is questionable with ankle soreness',
            'source_priority': 1
        }
        signal = parser.parse_rss_item(mock_item)
        assert signal is not None
        
        # Step 2: Resolve player (mock)
        resolver = EntityResolver()
        # In real test, would resolve to actual ID
        mock_player_id = 201939
        
        # Step 3: Create assumption
        engine = AssumptionEngine()
        assumption = engine.create_assumption_from_signal(
            signal,
            player_id=mock_player_id,
            source='test'
        )
        
        assert assumption is not None
        assert assumption.player_id == mock_player_id
        assert assumption.minutes_multiplier == 0.85  # QUESTIONABLE
        assert assumption.confidence_level == 'LOW'


# Pytest fixtures
@pytest.fixture
def sample_rss_item():
    return {
        'title': 'LeBron James: OUT (ankle)',
        'description': 'LeBron will miss tonight\'s game',
        'link': 'https://example.com/news/123',
        'source': 'RotoWire NBA',
        'source_priority': 1
    }


@pytest.fixture
def sample_tweet():
    return {
        'text': 'Status alert: Giannis Antetokounmpo (knee) OUT Wednesday',
        'handle': 'UnderdogNBA',
        'display_name': 'Underdog NBA',
        'source_priority': 1
    }


@pytest.fixture
def sample_official_entry():
    return {
        'player_name': 'Kevin Durant',
        'status': 'QUESTIONABLE',
        'reason': 'Injury/Illness - Right Ankle; Sprain',
        'team': 'Phoenix Suns',
        'game_date': '01/15/2026'
    }


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
