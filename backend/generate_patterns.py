#!/usr/bin/env python3
"""
Generate all patterns and story pairs for static site
This pre-generates all data so we don't need a REST API
"""
import json
import urllib.request
import ssl
import os
from collections import defaultdict
from datetime import datetime

ssl_context = ssl.create_default_context()

def call_claude(prompt, api_key):
    """Call Claude API with a prompt"""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1000,
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
    
    with urllib.request.urlopen(request, context=ssl_context) as response:
        result = json.loads(response.read().decode())
        return result['content'][0]['text']

def fetch_interviews_by_theme(theme, limit=50):
    """Fetch interviews containing a specific theme"""
    print(f"  Fetching interviews for theme: {theme}")
    
    interviews_with_theme = []
    page = 1
    
    while len(interviews_with_theme) < limit and page < 20:
        url = f"https://archive.storycorps.org/wp-json/storycorps/v1/interviews?per_page=10&page={page}"
        headers = {'User-Agent': 'Mozilla/5.0 (Mosaic/1.0)'}
        
        request = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(request, context=ssl_context) as response:
                interviews = json.loads(response.read().decode())
                
                for interview in interviews:
                    keywords = [k.lower() for k in interview.get('keywords', [])]
                    if any(theme in k for k in keywords):
                        interviews_with_theme.append(interview)
                        
                page += 1
                
        except Exception as e:
            print(f"    Error: {e}")
            break
    
    print(f"    Found {len(interviews_with_theme)} interviews")
    return interviews_with_theme

def generate_pattern(theme, interviews, api_key):
    """Generate a unity pattern for a theme"""
    if not interviews:
        return None
        
    # Group by location
    by_location = defaultdict(list)
    for interview in interviews:
        location = interview.get('location', {})
        region = location.get('region', ['Unknown'])[0] if location.get('region') else 'Unknown'
        by_location[region].append(interview)
    
    # Create prompt for Claude
    prompt = f"Analyze these StoryCorps interviews about '{theme}' from different locations:\n\n"
    
    for region, stories in list(by_location.items())[:5]:  # Max 5 regions
        prompt += f"\n{region} ({len(stories)} stories):\n"
        for story in stories[:3]:  # Max 3 stories per region
            prompt += f"- {story.get('title', 'Untitled')}: {story.get('description', '')[:150]}...\n"
    
    prompt += """
Analyze the unity of this theme across demographics:
1. UNITY_SCORE: [0.0-1.0, where 1.0 means completely universal]
2. COMMON_EXPERIENCES: List specific shared experiences
3. INSIGHTS: 2-3 sentences about what unites people on this theme
4. SURPRISING_CONNECTIONS: Any unexpected similarities

Be specific and insightful."""
    
    analysis = call_claude(prompt, api_key)
    
    # Parse unity score
    unity_score = 0.7  # Default
    for line in analysis.split('\n'):
        if 'UNITY_SCORE:' in line:
            try:
                unity_score = float(line.split(':')[1].strip())
            except:
                pass
    
    return {
        "theme": theme,
        "unity_score": unity_score,
        "sample_count": len(interviews),
        "locations": list(by_location.keys()),
        "analysis": analysis,
        "generated_at": datetime.now().isoformat()
    }

def find_story_pair(theme, interviews, api_key):
    """Find a powerful story pair for a theme"""
    if len(interviews) < 2:
        return None
        
    # Find contrasting locations
    by_location = defaultdict(list)
    for interview in interviews:
        location = interview.get('location', {})
        region = location.get('region', ['Unknown'])[0] if location.get('region') else 'Unknown'
        by_location[region].append(interview)
    
    if len(by_location) < 2:
        return None
    
    # Pick two contrasting locations
    locations = list(by_location.keys())
    story_a = by_location[locations[0]][0]
    story_b = by_location[locations[-1]][0]
    
    # Have Claude analyze the pair
    prompt = f"""Analyze this pair of StoryCorps stories about '{theme}':

STORY A ({story_a.get('location', {}).get('region', ['Unknown'])[0]}):
Title: {story_a.get('title', 'Untitled')}
Description: {story_a.get('description', '')}

STORY B ({story_b.get('location', {}).get('region', ['Unknown'])[0]}):
Title: {story_b.get('title', 'Untitled')}
Description: {story_b.get('description', '')}

Provide:
1. SURFACE_DIFFERENCES: 3 obvious contrasts
2. DEEP_CONNECTIONS: 3 profound similarities
3. CONNECTION_SCORE: [0.0-1.0]
4. WHY_IT_MATTERS: 1-2 sentences on why this connection is powerful"""
    
    analysis = call_claude(prompt, api_key)
    
    return {
        "theme": theme,
        "story_a": {
            "id": story_a.get('id'),
            "title": story_a.get('title'),
            "location": story_a.get('location', {}).get('region', ['Unknown'])[0],
            "description": story_a.get('description', '')[:300]
        },
        "story_b": {
            "id": story_b.get('id'),
            "title": story_b.get('title'),
            "location": story_b.get('location', {}).get('region', ['Unknown'])[0],
            "description": story_b.get('description', '')[:300]
        },
        "analysis": analysis,
        "generated_at": datetime.now().isoformat()
    }

def main():
    """Generate all patterns for static site"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY required")
        return
        
    print("🎭 Generating Mosaic Patterns for Static Site")
    print("=" * 60)
    
    # Create output directory
    os.makedirs("../frontend/public/data", exist_ok=True)
    
    # Define themes to analyze
    themes = ["family", "work", "love", "loss", "hope", "struggle", "identity", "community"]
    
    patterns = []
    pairs = []
    
    for theme in themes:
        print(f"\n📊 Processing theme: {theme}")
        
        # Fetch interviews
        interviews = fetch_interviews_by_theme(theme, limit=30)
        
        if interviews:
            # Generate pattern
            print(f"  Generating unity pattern...")
            pattern = generate_pattern(theme, interviews, api_key)
            if pattern:
                patterns.append(pattern)
                print(f"  ✓ Unity score: {pattern['unity_score']:.2f}")
            
            # Find story pair
            print(f"  Finding story pair...")
            pair = find_story_pair(theme, interviews, api_key)
            if pair:
                pairs.append(pair)
                print(f"  ✓ Found pair")
    
    # Save data
    print(f"\n💾 Saving data...")
    
    # Save patterns
    with open("../frontend/public/data/patterns.json", "w") as f:
        json.dump({
            "patterns": patterns,
            "generated_at": datetime.now().isoformat(),
            "total_themes": len(patterns)
        }, f, indent=2)
    
    # Save story pairs
    with open("../frontend/public/data/story_pairs.json", "w") as f:
        json.dump({
            "pairs": pairs,
            "generated_at": datetime.now().isoformat(),
            "total_pairs": len(pairs)
        }, f, indent=2)
    
    # Save summary for homepage
    summary = {
        "total_patterns": len(patterns),
        "total_pairs": len(pairs),
        "themes": [p["theme"] for p in patterns],
        "average_unity_score": sum(p["unity_score"] for p in patterns) / len(patterns) if patterns else 0,
        "highest_unity": max(patterns, key=lambda p: p["unity_score"]) if patterns else None,
        "generated_at": datetime.now().isoformat()
    }
    
    with open("../frontend/public/data/summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Generated {len(patterns)} patterns and {len(pairs)} story pairs")
    print(f"📁 Data saved to frontend/public/data/")
    print(f"\nTotal API cost: ~${len(themes) * 2 * 0.01:.2f} (estimate)")
    print("\nNext: Build React frontend to visualize this data!")

if __name__ == "__main__":
    main()