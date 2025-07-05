#!/usr/bin/env python3
"""
Test pattern discovery with real Claude API
Run this after setting ANTHROPIC_API_KEY in your .env file
"""
import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not installed. Set ANTHROPIC_API_KEY manually.")

from src.pattern_discovery import PatternDiscoveryEngine
from src.intelligent_query import IntelligentQuerySystem


async def test_with_claude():
    """Test the system with real Claude API"""
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not found!")
        print("\nTo test with Claude:")
        print("1. Get your API key from https://console.anthropic.com/")
        print("2. Add to .env file: ANTHROPIC_API_KEY=your-key-here")
        print("3. Run this script again")
        return
    
    print("=" * 60)
    print("🎭 Mosaic Pattern Discovery - Testing with Claude")
    print("=" * 60)
    
    # Initialize systems
    query_system = IntelligentQuerySystem()
    discovery_engine = PatternDiscoveryEngine()
    
    # Step 1: Find promising themes
    print("\n📊 Step 1: Analyzing keyword distribution...")
    theme_counts = await query_system.analyze_keyword_distribution(sample_size=30)
    
    # Pick a theme to analyze
    test_theme = "family" if "family" in theme_counts else list(theme_counts.keys())[0]
    print(f"\n🎯 Selected theme for analysis: '{test_theme}'")
    
    # Step 2: Discover unity pattern
    print(f"\n🔍 Step 2: Discovering unity pattern for '{test_theme}'...")
    print("(This will use Claude to analyze the interviews)")
    
    try:
        pattern = await discovery_engine.discover_unity_pattern(test_theme, sample_size="adaptive")
        
        print("\n✨ Unity Pattern Discovered!")
        print("=" * 60)
        print(f"Theme: {pattern.theme}")
        print(f"Unity Score: {pattern.unity_score:.2f} (0=divided, 1=universal)")
        print(f"Demographics analyzed: {', '.join(pattern.demographic_groups)}")
        print(f"Sample size: {pattern.sample_size} interviews")
        print(f"\n📝 Claude's Insights:")
        print("-" * 60)
        print(pattern.insights)
        print("-" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during pattern discovery: {e}")
        print("This might be due to rate limits or API issues.")
        return
    
    # Step 3: Find a powerful story pair
    print(f"\n💫 Step 3: Finding powerful story pair for '{test_theme}'...")
    
    try:
        pair = await discovery_engine.find_powerful_story_pair(test_theme)
        
        if pair:
            print("\n🤝 Story Pair Found!")
            print("=" * 60)
            print(f"\n📖 Story A: {pair.story_a.title}")
            print(f"   Location: {pair.story_a.location.region or 'Unknown'}")
            print(f"   Preview: {pair.story_a.description[:150]}...")
            
            print(f"\n📖 Story B: {pair.story_b.title}")
            print(f"   Location: {pair.story_b.location.region or 'Unknown'}")
            print(f"   Preview: {pair.story_b.description[:150]}...")
            
            print(f"\n🌍 Surface Differences:")
            for diff in pair.surface_differences[:3]:
                print(f"   - {diff}")
            
            print(f"\n❤️  Deep Connections:")
            for conn in pair.deep_connections[:3]:
                print(f"   - {conn}")
            
            print(f"\n✨ Unity Score: {pair.unity_score:.2f}")
            
            print(f"\n📝 Claude's Analysis:")
            print("-" * 60)
            print(pair.claude_analysis)
            print("-" * 60)
        else:
            print("No story pairs found for this theme.")
            
    except Exception as e:
        print(f"\n❌ Error finding story pair: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 Test Complete!")
    print("=" * 60)
    print("\nWhat we discovered:")
    print(f"1. Theme '{test_theme}' has a unity score of {pattern.unity_score:.2f}")
    print(f"2. Found patterns across {len(pattern.demographic_groups)} demographic groups")
    if pair:
        print(f"3. Identified a powerful story pair with {pair.unity_score:.2f} unity score")
    
    print("\n💡 Next steps:")
    print("1. Test with more themes to build pattern library")
    print("2. Build REST API to serve this data")
    print("3. Create beautiful visualizations in the frontend")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/test_results_{timestamp}.txt"
    os.makedirs("data", exist_ok=True)
    
    with open(filename, "w") as f:
        f.write(f"Test Results - {datetime.now()}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Pattern: {pattern.theme}\n")
        f.write(f"Unity Score: {pattern.unity_score}\n")
        f.write(f"Insights: {pattern.insights}\n")
        if pair:
            f.write(f"\nStory Pair:\n")
            f.write(f"A: {pair.story_a.title}\n")
            f.write(f"B: {pair.story_b.title}\n")
            f.write(f"Analysis: {pair.claude_analysis}\n")
    
    print(f"\n💾 Results saved to: {filename}")


if __name__ == "__main__":
    asyncio.run(test_with_claude())