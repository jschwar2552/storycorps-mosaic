#!/usr/bin/env python3
"""
StoryCorps MCP Server - Simplified version
"""

import json
import sqlite3
import hashlib
import sys
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.parse

# Initialize database
DB_PATH = Path.home() / ".storycorps_cache.db"

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id TEXT UNIQUE,
            title TEXT,
            description TEXT,
            keywords TEXT,
            location TEXT,
            url TEXT,
            cached_at TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS collections (
            name TEXT PRIMARY KEY,
            story_ids TEXT,
            created_at TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def search_stories(theme, location=None):
    """Search for stories by theme"""
    # Check cache first
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = "SELECT * FROM stories WHERE (keywords LIKE ? OR description LIKE ?)"
    params = [f'%{theme}%', f'%{theme}%']
    
    if location:
        query += " AND location LIKE ?"
        params.append(f'%{location}%')
    
    results = c.execute(query + " LIMIT 20", params).fetchall()
    
    if results:
        stories = [dict(row) for row in results]
        conn.close()
        return {
            'source': 'cache',
            'stories': stories,
            'count': len(stories)
        }
    
    # Fetch from API
    stories = fetch_from_api(theme)
    conn.close()
    
    return {
        'source': 'api',
        'stories': stories,
        'count': len(stories)
    }

def fetch_from_api(theme):
    """Fetch stories from StoryCorps API"""
    base_url = 'https://archive.storycorps.org/wp-json/storycorps/v1/interviews'
    stories = []
    
    for page in range(1, 4):
        try:
            url = f"{base_url}?per_page=10&page={page}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mosaic-MCP/1.0'})
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read())
                
                for story in data:
                    keywords = ' '.join(story.get('keywords', [])).lower()
                    description = (story.get('description') or '').lower()
                    
                    if theme.lower() in keywords or theme.lower() in description:
                        # Format and cache
                        formatted = {
                            'story_id': str(story.get('id')),
                            'title': story.get('title'),
                            'description': story.get('description'),
                            'keywords': json.dumps(story.get('keywords', [])),
                            'location': story.get('location', {}).get('region', ['Unknown'])[0],
                            'url': story.get('url'),
                            'cached_at': datetime.now().isoformat()
                        }
                        stories.append(formatted)
                        cache_story(formatted)
                        
                if len(stories) >= 10:
                    break
                    
        except Exception as e:
            print(f"API error: {e}", file=sys.stderr)
            break
    
    return stories

def cache_story(story):
    """Cache a story in the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT OR REPLACE INTO stories 
            (story_id, title, description, keywords, location, url, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            story['story_id'],
            story['title'],
            story['description'],
            story['keywords'],
            story['location'],
            story['url'],
            story['cached_at']
        ))
        conn.commit()
    except Exception as e:
        print(f"Cache error: {e}", file=sys.stderr)
    finally:
        conn.close()

def save_collection(name, story_ids):
    """Save a collection of stories"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT OR REPLACE INTO collections (name, story_ids, created_at)
        VALUES (?, ?, ?)
    ''', (name, json.dumps(story_ids), datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return {'message': f"Saved collection '{name}' with {len(story_ids)} stories"}

def get_collections():
    """List all collections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    results = c.execute('SELECT * FROM collections ORDER BY created_at DESC').fetchall()
    conn.close()
    
    collections = []
    for row in results:
        story_ids = json.loads(row['story_ids'])
        collections.append({
            'name': row['name'],
            'story_count': len(story_ids),
            'created_at': row['created_at']
        })
    
    return {'collections': collections}

def handle_request(request):
    """Handle MCP requests"""
    method = request.get('method')
    params = request.get('params', {})
    
    if method == 'search_stories':
        return search_stories(params.get('theme'), params.get('location'))
    elif method == 'save_collection':
        return save_collection(params.get('name'), params.get('story_ids'))
    elif method == 'list_collections':
        return get_collections()
    else:
        return {'error': f"Unknown method: {method}"}

def main():
    """Main MCP server loop"""
    init_database()
    
    # MCP communication via stdin/stdout
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            request = json.loads(line)
            response = handle_request(request)
            
            print(json.dumps({
                'id': request.get('id'),
                'result': response
            }))
            sys.stdout.flush()
            
        except Exception as e:
            print(json.dumps({
                'error': str(e)
            }), file=sys.stderr)
            sys.stderr.flush()

if __name__ == "__main__":
    main()