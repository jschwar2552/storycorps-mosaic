#!/usr/bin/env python3
"""Test the StoryCorps MCP server functionality"""

import json
from server import search_stories, save_collection, get_collections, init_database

def test_server():
    print("🧪 Testing StoryCorps MCP Server...\n")
    
    # Initialize database
    init_database()
    print("✅ Database initialized")
    
    # Test search
    print("\n📚 Testing search for 'family' stories...")
    result = search_stories('family')
    print(f"Found {result['count']} stories from {result['source']}")
    if result['stories']:
        story = result['stories'][0]
        print(f"\nFirst story:")
        print(f"  Title: {story['title']}")
        print(f"  Location: {story['location']}")
        print(f"  URL: {story['url']}")
        keywords = json.loads(story['keywords'])
        print(f"  Keywords: {', '.join(keywords[:5])}")
    
    # Test collection saving
    if result['stories']:
        story_ids = [s['story_id'] for s in result['stories'][:3]]
        print(f"\n💾 Saving collection with {len(story_ids)} stories...")
        save_result = save_collection("Test Family Stories", story_ids)
        print(save_result['message'])
    
    # Test listing collections
    print("\n📋 Listing collections...")
    collections = get_collections()
    for coll in collections['collections']:
        print(f"  - {coll['name']}: {coll['story_count']} stories")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_server()