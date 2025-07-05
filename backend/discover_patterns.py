#!/usr/bin/env python3
"""
Script to discover unity patterns in StoryCorps data
"""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.pattern_discovery import PatternDiscoveryEngine
from src.intelligent_query import IntelligentQuerySystem

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


async def test_pattern_discovery():
    """Test the pattern discovery system"""
    
    print("=" * 60)
    print("Mosaic Pattern Discovery Test")
    print("=" * 60)
    
    # First, analyze keyword distribution
    query_system = IntelligentQuerySystem()
    
    print("\n1. Analyzing keyword distribution in StoryCorps...")
    theme_counts = await query_system.analyze_keyword_distribution(sample_size=50)
    
    # Pick top themes for analysis
    top_themes = list(theme_counts.keys())[:5]
    print(f"\nTop themes to analyze: {top_themes}")
    
    # Test finding demographic intersections
    if top_themes:
        test_theme = top_themes[0]
        print(f"\n2. Finding demographic intersections for '{test_theme}'...")
        intersections = await query_system.find_demographic_intersections(test_theme, limit=30)
        
        # Test story pair finding
        print(f"\n3. Finding story pairs for '{test_theme}'...")
        pairs = await query_system.find_story_pairs(test_theme)
        print(f"Found {len(pairs)} potential pairs")
    
    # Test Claude integration if API key is available
    if os.getenv("ANTHROPIC_API_KEY"):
        print("\n4. Testing Claude pattern analysis...")
        discovery_engine = PatternDiscoveryEngine()
        
        # Discover pattern for one theme
        if top_themes:
            pattern = await discovery_engine.discover_unity_pattern(top_themes[0])
            
            print(f"\nUnity Pattern Discovered:")
            print(f"Theme: {pattern.theme}")
            print(f"Unity Score: {pattern.unity_score}")
            print(f"Demographics: {pattern.demographic_groups}")
            print(f"Sample Size: {pattern.sample_size}")
            print(f"\nInsights (first 500 chars):")
            print(pattern.insights[:500])
            
            # Try finding a story pair
            print(f"\n5. Finding powerful story pair for '{top_themes[0]}'...")
            pair = await discovery_engine.find_powerful_story_pair(top_themes[0])
            
            if pair:
                print(f"\nStory Pair Found:")
                print(f"Story A: {pair.story_a.title}")
                print(f"Story B: {pair.story_b.title}")
                print(f"Unity Score: {pair.unity_score}")
                print(f"Surface Differences: {pair.surface_differences[:3]}")
                print(f"Deep Connections: {pair.deep_connections[:3]}")
    else:
        print("\n⚠️  ANTHROPIC_API_KEY not found. Skipping Claude analysis.")
        print("Set your API key to test pattern discovery:")
        print("export ANTHROPIC_API_KEY='your-key-here'")
    
    print("\n" + "=" * 60)
    print("Pattern discovery test complete!")
    print("=" * 60)


async def discover_all_patterns():
    """Discover patterns for multiple themes"""
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY required for pattern discovery")
        return
    
    discovery_engine = PatternDiscoveryEngine()
    
    # Create patterns directory
    os.makedirs("patterns", exist_ok=True)
    
    # Discover patterns for top themes
    patterns = await discovery_engine.discover_macro_patterns()
    
    # Get dashboard data
    dashboard_data = discovery_engine.get_unity_dashboard_data()
    
    print("\n" + "=" * 60)
    print("Unity Dashboard Data")
    print("=" * 60)
    print(f"Patterns discovered: {len(dashboard_data['patterns'])}")
    print(f"Demographic bridges: {len(dashboard_data['demographic_bridges'])}")
    print("\nUnity scores by theme:")
    for theme, score in dashboard_data['unity_scores'].items():
        print(f"  - {theme}: {score:.2f}")


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_pattern_discovery())