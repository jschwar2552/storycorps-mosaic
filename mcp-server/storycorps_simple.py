#!/usr/bin/env python3
"""
StoryCorps MCP Server - Minimal implementation for Claude Desktop
"""

import json
import sys
import sqlite3
from pathlib import Path
import urllib.request
from datetime import datetime

# Database path
DB_PATH = Path.home() / ".storycorps_cache.db"

def init_db():
    """Initialize SQLite database"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                story_id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                keywords TEXT,
                location TEXT,
                url TEXT,
                cached_at TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                name TEXT PRIMARY KEY,
                story_ids TEXT,
                created_at TIMESTAMP
            )
        ''')

def search_stories(theme, location=None):
    """Search for stories by theme"""
    if not theme:
        return {"error": "Theme is required"}
    
    # Try cache first
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        
        query = "SELECT * FROM stories WHERE keywords LIKE ? OR description LIKE ?"
        params = [f'%{theme}%', f'%{theme}%']
        
        if location:
            query += " AND location LIKE ?"
            params.append(f'%{location}%')
        
        cached = conn.execute(query + " LIMIT 20", params).fetchall()
        
        if cached:
            stories = []
            for row in cached:
                story = dict(row)
                story['keywords'] = json.loads(story['keywords'])
                stories.append(story)
            return {
                'stories': stories,
                'count': len(stories),
                'source': 'cache',
                'message': f"Found {len(stories)} cached stories about '{theme}'"
            }
    
    # Fetch from API
    stories = []
    base_url = 'https://archive.storycorps.org/wp-json/storycorps/v1/interviews'
    
    for page in range(1, 4):
        try:
            url = f"{base_url}?per_page=10&page={page}"
            req = urllib.request.Request(url, headers={'User-Agent': 'StoryCorps-MCP/1.0'})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                
                for story in data:
                    keywords = story.get('keywords', [])
                    description = (story.get('description') or '').lower()
                    keywords_text = ' '.join(keywords).lower()
                    
                    if theme.lower() in keywords_text or theme.lower() in description:
                        story_location = story.get('location', {}).get('region', ['Unknown'])[0]
                        
                        if location and location.lower() not in story_location.lower():
                            continue
                        
                        formatted = {
                            'story_id': str(story.get('id')),
                            'title': story.get('title'),
                            'description': story.get('description'),
                            'keywords': keywords,
                            'location': story_location,
                            'url': story.get('url')
                        }
                        
                        stories.append(formatted)
                        
                        # Cache the story
                        with sqlite3.connect(DB_PATH) as conn:
                            conn.execute('''
                                INSERT OR REPLACE INTO stories VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                formatted['story_id'],
                                formatted['title'],
                                formatted['description'],
                                json.dumps(formatted['keywords']),
                                formatted['location'],
                                formatted['url'],
                                datetime.now().isoformat()
                            ))
                        
                        if len(stories) >= 10:
                            return {
                                'stories': stories,
                                'count': len(stories),
                                'source': 'api',
                                'message': f"Found {len(stories)} stories about '{theme}' from StoryCorps"
                            }
                            
        except Exception:
            break
    
    return {
        'stories': stories,
        'count': len(stories),
        'source': 'api',
        'message': f"Found {len(stories)} stories about '{theme}' from StoryCorps"
    }

def main():
    """Main server loop"""
    init_db()
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line.strip())
            method = request.get('method')
            params = request.get('params', {})
            request_id = request.get('id', 0)  # Default to 0 if no ID
            
            result = None
            
            if method == 'initialize':
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "storycorps",
                        "version": "1.0.0"
                    }
                }
            
            elif method == 'tools/list':
                result = {
                    "tools": [
                        {
                            "name": "search_stories",
                            "description": "Search StoryCorps stories by theme and optional location",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "theme": {
                                        "type": "string",
                                        "description": "Theme to search for (e.g., family, resilience, immigration)"
                                    },
                                    "location": {
                                        "type": "string",
                                        "description": "Optional location filter (e.g., New York, rural, South)"
                                    }
                                },
                                "required": ["theme"]
                            }
                        }
                    ]
                }
            
            elif method == 'tools/call':
                tool_name = params.get('name')
                tool_args = params.get('arguments', {})
                
                if tool_name == 'search_stories':
                    result_data = search_stories(
                        tool_args.get('theme'),
                        tool_args.get('location')
                    )
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result_data, indent=2)
                            }
                        ]
                    }
            
            # Send response
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except Exception:
            # Send minimal error response
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": 0,
                "error": {
                    "code": -32603,
                    "message": "Internal error"
                }
            }))
            sys.stdout.flush()

if __name__ == "__main__":
    main()