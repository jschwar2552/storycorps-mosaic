#!/usr/bin/env python3
"""
Simple test of Mosaic pattern discovery using only urllib
This works without needing to install any packages
"""
import json
import urllib.request
import urllib.parse
import ssl
import os
from collections import defaultdict

# SSL context for HTTPS
ssl_context = ssl.create_default_context()

def test_claude_api():
    """Test Claude API using urllib"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return False
        
    print(f"✅ Found API key: {api_key[:20]}...")
    
    # Test Claude API
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 100,
        "messages": [{
            "role": "user",
            "content": "Say 'Mosaic test successful!' and nothing else."
        }]
    }
    
    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers
    )
    
    try:
        with urllib.request.urlopen(request, context=ssl_context) as response:
            result = json.loads(response.read().decode())
            message = result['content'][0]['text']
            print(f"\n🤖 Claude says: {message}")
            return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def fetch_storycorps_data():
    """Fetch some StoryCorps interviews"""
    print("\n📊 Fetching StoryCorps data...")
    
    url = "https://archive.storycorps.org/wp-json/storycorps/v1/interviews?per_page=20"
    headers = {'User-Agent': 'Mozilla/5.0 (Mosaic/1.0)'}
    
    request = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(request, context=ssl_context) as response:
            interviews = json.loads(response.read().decode())
            
            # Analyze themes
            theme_counts = defaultdict(int)
            family_stories = []
            
            for interview in interviews:
                keywords = interview.get('keywords', [])
                for keyword in keywords:
                    if 'family' in keyword.lower():
                        theme_counts['family'] += 1
                        family_stories.append(interview)
                    elif 'work' in keyword.lower():
                        theme_counts['work'] += 1
                    elif 'love' in keyword.lower():
                        theme_counts['love'] += 1
            
            print(f"\n✅ Analyzed {len(interviews)} interviews")
            print("\nTheme counts:")
            for theme, count in theme_counts.items():
                print(f"  - {theme}: {count}")
                
            return family_stories[:5]  # Return 5 family stories
            
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return []

def analyze_with_claude(stories):
    """Have Claude analyze story patterns"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key or not stories:
        return None
        
    print(f"\n🔍 Analyzing {len(stories)} family stories with Claude...")
    
    # Prepare prompt
    prompt = "Analyze these StoryCorps interviews about family from different locations.\n\n"
    
    for i, story in enumerate(stories):
        location = story.get('location', {})
        region = location.get('region', ['Unknown'])[0] if location.get('region') else 'Unknown'
        
        prompt += f"Story {i+1} ({region}):\n"
        prompt += f"Title: {story.get('title', 'Untitled')}\n"
        prompt += f"Description: {story.get('description', '')[:200]}...\n"
        prompt += f"Keywords: {', '.join(story.get('keywords', [])[:5])}\n\n"
    
    prompt += """
Please analyze:
1. What unites these family stories across different locations?
2. Rate the unity score from 0.0 to 1.0
3. What surprising connections do you see?

Format your response as:
UNITY_SCORE: [number]
COMMON_THEMES: [list]
INSIGHTS: [paragraph]
"""
    
    # Call Claude
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 500,
        "messages": [{
            "role": "user",
            "content": prompt
        }]
    }
    
    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers
    )
    
    try:
        with urllib.request.urlopen(request, context=ssl_context) as response:
            result = json.loads(response.read().decode())
            analysis = result['content'][0]['text']
            
            print("\n✨ Claude's Analysis:")
            print("=" * 60)
            print(analysis)
            print("=" * 60)
            
            return analysis
            
    except Exception as e:
        print(f"❌ Error analyzing: {e}")
        return None

def main():
    """Run the Mosaic test"""
    print("🎭 Mosaic Pattern Discovery Test")
    print("=" * 60)
    
    # Test Claude API
    if not test_claude_api():
        print("\n⚠️  Claude API test failed. Check your API key.")
        return
    
    # Fetch StoryCorps data
    family_stories = fetch_storycorps_data()
    
    if not family_stories:
        print("\n⚠️  No family stories found")
        return
    
    # Analyze with Claude
    analysis = analyze_with_claude(family_stories)
    
    if analysis:
        print("\n✅ Test complete! Mosaic can discover unity patterns.")
        print("\nNext steps:")
        print("1. Build REST API to serve this data")
        print("2. Create React frontend with visualizations")
        print("3. Deploy to GitHub Pages + Vercel")
    
    # Regarding REST API question
    print("\n" + "=" * 60)
    print("Do we need a REST API?")
    print("=" * 60)
    print("For a static GitHub Pages site, we have options:")
    print("1. Pre-generate all patterns and serve as JSON files (no API needed)")
    print("2. Use serverless functions on Vercel for on-demand analysis")
    print("3. Build a simple FastAPI backend for dynamic queries")
    print("\nRecommendation: Start with option 1 - pre-generate patterns")
    print("This is simpler and costs less!")

if __name__ == "__main__":
    main()