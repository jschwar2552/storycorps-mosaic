#!/usr/bin/env python3
"""Simple test of keyword analysis without external dependencies"""
import urllib.request
import json
import ssl
from collections import defaultdict

ssl_context = ssl.create_default_context()

def analyze_keywords(limit=50):
    """Analyze keywords from StoryCorps API"""
    
    base_url = "https://archive.storycorps.org/wp-json/storycorps/v1/interviews"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Mosaic/1.0)'
    }
    
    print("Analyzing StoryCorps keywords...")
    print("=" * 60)
    
    keyword_counts = defaultdict(int)
    theme_counts = defaultdict(int)
    location_counts = defaultdict(int)
    interviews_analyzed = 0
    
    # Analyze pages
    for page in range(1, 6):  # 5 pages, 10 per page = 50 interviews
        url = f"{base_url}?per_page=10&page={page}"
        
        request = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(request, context=ssl_context) as response:
                data = json.loads(response.read().decode())
                
                for interview in data:
                    interviews_analyzed += 1
                    
                    # Count keywords
                    for keyword in interview.get('keywords', []):
                        keyword_counts[keyword.lower()] += 1
                        
                        # Map to themes
                        if any(word in keyword.lower() for word in ['family', 'parent', 'child', 'mother', 'father']):
                            theme_counts['family'] += 1
                        elif any(word in keyword.lower() for word in ['love', 'romance', 'marriage', 'relationship']):
                            theme_counts['love'] += 1
                        elif any(word in keyword.lower() for word in ['work', 'job', 'career', 'profession']):
                            theme_counts['work'] += 1
                        elif any(word in keyword.lower() for word in ['immigrant', 'immigration', 'journey']):
                            theme_counts['immigration'] += 1
                        elif any(word in keyword.lower() for word in ['memory', 'remember', 'past']):
                            theme_counts['memory'] += 1
                    
                    # Count locations
                    location = interview.get('location', {})
                    if location.get('region'):
                        region = location['region'][0] if isinstance(location['region'], list) else location['region']
                        location_counts[region] += 1
        
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
    
    print(f"\nAnalyzed {interviews_analyzed} interviews")
    
    # Show top keywords
    print("\nTop 20 Keywords:")
    sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    for keyword, count in sorted_keywords:
        print(f"  {keyword}: {count}")
    
    # Show themes
    print("\nTheme Distribution:")
    for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {theme}: {count} interviews")
    
    # Show locations
    print("\nTop 10 Locations:")
    sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for location, count in sorted_locations:
        print(f"  {location}: {count} interviews")
    
    # Find diverse theme example
    print("\n" + "=" * 60)
    print("Finding interviews about 'family' from different locations...")
    
    family_by_location = defaultdict(list)
    
    # Search for family stories
    for page in range(1, 11):  # Search more pages
        url = f"{base_url}?per_page=10&page={page}"
        request = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(request, context=ssl_context) as response:
                data = json.loads(response.read().decode())
                
                for interview in data:
                    keywords = [k.lower() for k in interview.get('keywords', [])]
                    if any('family' in k for k in keywords):
                        location = interview.get('location', {})
                        region = 'Unknown'
                        if location.get('region'):
                            region = location['region'][0] if isinstance(location['region'], list) else location['region']
                        
                        family_by_location[region].append({
                            'title': interview.get('title', 'Untitled'),
                            'description': interview.get('description', '')[:200] + '...'
                        })
        except:
            break
    
    print(f"\nFound family stories from {len(family_by_location)} different locations:")
    for location, stories in list(family_by_location.items())[:5]:
        print(f"\n{location} ({len(stories)} stories):")
        if stories:
            print(f"  Example: {stories[0]['title']}")
            print(f"  {stories[0]['description']}")
    
    return theme_counts, location_counts

if __name__ == "__main__":
    analyze_keywords()