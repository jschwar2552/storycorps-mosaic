"""Tests for pattern discovery system"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import json

from src.models import Interview, Location, UnityPattern, StoryPair
from src.intelligent_query import IntelligentQuerySystem
from src.pattern_discovery import PatternDiscoveryEngine


class TestModels:
    """Test data models"""
    
    def test_interview_from_api(self):
        """Test creating Interview from API response"""
        api_data = {
            "id": 123,
            "interview_id": "INT123",
            "title": "Test Story",
            "description": "A test description",
            "keywords": ["family", "love", "home"],
            "location": {
                "region": ["Ohio"],
                "country": ["United States"]
            },
            "audio": {
                "url": "https://example.com/audio.mp3",
                "length": 300
            }
        }
        
        interview = Interview.from_api(api_data)
        
        assert interview.id == 123
        assert interview.title == "Test Story"
        assert len(interview.keywords) == 3
        assert interview.location.region == "Ohio"
        assert interview.audio_length == 300
    
    def test_interview_get_themes(self):
        """Test theme extraction from keywords"""
        interview = Interview(
            id=1,
            interview_id="INT1",
            title="Test",
            description="Test",
            keywords=["family life", "mother and child", "working hard", "immigrant journey"],
            location=Location()
        )
        
        themes = interview.get_themes()
        
        assert "family" in themes
        assert "work" in themes
        assert "immigration" in themes
        assert len(themes) == 3


class TestIntelligentQuery:
    """Test intelligent query system"""
    
    @pytest.mark.asyncio
    async def test_keyword_distribution(self):
        """Test keyword analysis"""
        # Mock HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1,
                "title": "Story 1",
                "description": "Test",
                "keywords": ["family", "love", "home"],
                "location": {"region": ["Ohio"]}
            },
            {
                "id": 2,
                "title": "Story 2", 
                "description": "Test",
                "keywords": ["work", "family", "struggle"],
                "location": {"region": ["Texas"]}
            }
        ]
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            query_system = IntelligentQuerySystem()
            theme_counts = await query_system.analyze_keyword_distribution(sample_size=2)
            
            assert theme_counts["family"] == 2
            assert theme_counts["work"] == 1
            assert theme_counts["love"] == 1
    
    def test_location_key_generation(self):
        """Test demographic key generation"""
        query_system = IntelligentQuerySystem()
        
        # Test urban classification
        location = Location(region="New York")
        assert "urban" in query_system._get_location_key(location)
        
        # Test rural classification
        location = Location(region="Montana")
        assert "rural" in query_system._get_location_key(location)
        
        # Test mixed classification
        location = Location(region="Texas")
        assert "mixed" in query_system._get_location_key(location)
    
    def test_demographic_contrast_calculation(self):
        """Test contrast calculation between groups"""
        query_system = IntelligentQuerySystem()
        
        # High contrast (urban vs rural)
        contrast = query_system._calculate_demographic_contrast("urban_newyork", "rural_montana")
        assert contrast == 0.9
        
        # Medium contrast (different states)
        contrast = query_system._calculate_demographic_contrast("mixed_texas", "mixed_ohio")
        assert contrast == 0.7
        
        # Low contrast (same state)
        contrast = query_system._calculate_demographic_contrast("urban_newyork", "mixed_newyork")
        assert contrast == 0.3


class TestPatternDiscovery:
    """Test pattern discovery with Claude"""
    
    @pytest.mark.asyncio
    async def test_unity_pattern_discovery(self):
        """Test discovering unity patterns"""
        # Mock Claude response
        mock_claude_response = Mock()
        mock_claude_response.content = [Mock(text="""
UNITY_SCORE: 0.85
COMMON_THREADS: Family bonds, overcoming hardship, finding belonging
INSIGHTS: The theme of family transcends all demographic boundaries...
SURPRISING_CONNECTIONS: Rural and urban families share similar struggles...
        """)]
        
        # Mock interview data
        mock_interviews = [
            Interview(
                id=1, interview_id="INT1", title="Rural Family",
                description="Story about family farm",
                keywords=["family", "farm", "tradition"],
                location=Location(region="Iowa")
            ),
            Interview(
                id=2, interview_id="INT2", title="Urban Family",
                description="Story about city family",
                keywords=["family", "city", "change"],
                location=Location(region="New York")
            )
        ]
        
        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            # Setup mocks
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=mock_claude_response)
            
            with patch.object(IntelligentQuerySystem, 'adaptive_sampling', 
                            return_value=mock_interviews):
                
                engine = PatternDiscoveryEngine("test-api-key")
                pattern = await engine.discover_unity_pattern("family")
                
                assert pattern.theme == "family"
                assert pattern.unity_score == 0.85
                assert len(pattern.sample_stories) == 2
                assert "transcends all demographic boundaries" in pattern.insights
    
    @pytest.mark.asyncio
    async def test_story_pair_analysis(self):
        """Test story pair analysis"""
        # Create test interviews
        story_a = Interview(
            id=1, interview_id="INT1", title="Rural Farmer's Story",
            description="A farmer talks about losing the family farm",
            keywords=["loss", "family", "resilience"],
            location=Location(region="Iowa", country="United States")
        )
        
        story_b = Interview(
            id=2, interview_id="INT2", title="Urban Immigrant's Tale",
            description="An immigrant discusses leaving everything behind",
            keywords=["loss", "family", "hope", "journey"],
            location=Location(region="New York", country="United States")
        )
        
        # Mock Claude response
        mock_response = Mock()
        mock_response.content = [Mock(text="""
SURFACE_DIFFERENCES:
- Rural Iowa farmer vs Urban New York immigrant
- Native-born vs foreign-born
- Agricultural life vs city life

DEEP_CONNECTIONS:
- Both experienced profound loss
- Family as source of strength
- Resilience in face of change
- Hope for future generations

UNITY_SCORE: 0.92

ANALYSIS: These two stories powerfully illustrate how loss and resilience are universal human experiences...
        """)]
        
        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            
            engine = PatternDiscoveryEngine("test-api-key")
            pair = await engine._analyze_story_pair(story_a, story_b)
            
            assert pair.unity_score == 0.92
            assert len(pair.surface_differences) > 0
            assert len(pair.deep_connections) > 0
            assert "Rural Iowa farmer vs Urban New York immigrant" in pair.surface_differences[0]
            assert "loss" in pair.deep_connections[0].lower()


@pytest.mark.asyncio
async def test_end_to_end_pattern_discovery():
    """Test complete pattern discovery flow"""
    # This test would run with real API if ANTHROPIC_API_KEY is set
    import os
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    
    engine = PatternDiscoveryEngine()
    
    # Test with a simple theme
    pattern = await engine.discover_unity_pattern("family", sample_size="20")
    
    assert pattern is not None
    assert pattern.theme == "family"
    assert pattern.unity_score > 0
    assert len(pattern.insights) > 0
    print(f"\nDiscovered pattern: {pattern.theme}")
    print(f"Unity score: {pattern.unity_score}")
    print(f"Insights preview: {pattern.insights[:200]}...")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])