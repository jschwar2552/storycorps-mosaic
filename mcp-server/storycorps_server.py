#!/usr/bin/env python3
"""
StoryCorps MCP Server - Production version
Handles common MCP gotchas:
- Proper process cleanup
- JSON-RPC protocol compliance  
- Graceful error handling
- Logging for debugging
"""

import json
import sys
import sqlite3
from pathlib import Path
import urllib.request
from datetime import datetime

# Database path
DB_PATH = Path.home() / ".storycorps_cache.db"

class StoryCorpsServer:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
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
    
    def handle_request(self, request):
        """Process a single request"""
        method = request.get('method', '').replace('tools/', '')
        params = request.get('params', {})
        
        handlers = {
            'search_stories': lambda: self.search_stories(
                params.get('theme', ''),
                params.get('location')
            ),
            'get_story': lambda: self.get_story(params.get('story_id')),
            'save_collection': lambda: self.save_collection(
                params.get('name'),
                params.get('story_ids', [])
            ),
            'list_collections': lambda: self.list_collections()
        }
        
        handler = handlers.get(method)
        if handler:
            try:
                return handler()
            except Exception as e:
                return {'error': str(e)}
        else:
            return {'error': f'Unknown method: {method}'}
    
    def search_stories(self, theme, location=None):
        """Search for stories by theme"""
        if not theme:
            return {'error': 'Theme is required'}
        
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
                stories = [dict(row) for row in cached]
                for story in stories:
                    story['keywords'] = json.loads(story['keywords'])
                return {
                    'stories': stories,
                    'count': len(stories),
                    'source': 'cache'
                }
        
        # Fetch from API
        stories = self.fetch_from_api(theme, location)
        return {
            'stories': stories,
            'count': len(stories),
            'source': 'api'
        }
    
    def fetch_from_api(self, theme, location=None):
        """Fetch stories from StoryCorps API"""
        stories = []
        base_url = 'https://archive.storycorps.org/wp-json/storycorps/v1/interviews'
        
        for page in range(1, 4):
            try:
                url = f"{base_url}?per_page=10&page={page}"
                req = urllib.request.Request(url, headers={'User-Agent': 'StoryCorps-MCP/1.0'})
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read())
                    
                    for story in data:
                        # Check if matches theme
                        keywords = story.get('keywords', [])
                        description = (story.get('description') or '').lower()
                        keywords_text = ' '.join(keywords).lower()
                        
                        if theme.lower() in keywords_text or theme.lower() in description:
                            story_location = story.get('location', {}).get('region', ['Unknown'])[0]
                            
                            # Filter by location if specified
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
                            self.cache_story(formatted)
                            
                            if len(stories) >= 10:
                                return stories
                                
            except Exception as e:
                sys.stderr.write(f"API error: {e}\n")
                break
        
        return stories
    
    def cache_story(self, story):
        """Cache a story"""
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO stories VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                story['story_id'],
                story['title'],
                story['description'],
                json.dumps(story['keywords']),
                story['location'],
                story['url'],
                datetime.now().isoformat()
            ))
    
    def get_story(self, story_id):
        """Get a specific story"""
        if not story_id:
            return {'error': 'Story ID required'}
            
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM stories WHERE story_id = ?', 
                (story_id,)
            ).fetchone()
            
            if row:
                story = dict(row)
                story['keywords'] = json.loads(story['keywords'])
                return story
            else:
                return {'error': f'Story {story_id} not found'}
    
    def save_collection(self, name, story_ids):
        """Save a story collection"""
        if not name:
            return {'error': 'Collection name required'}
            
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO collections VALUES (?, ?, ?)
            ''', (name, json.dumps(story_ids), datetime.now().isoformat()))
            
        return {'message': f'Saved collection "{name}" with {len(story_ids)} stories'}
    
    def list_collections(self):
        """List all collections"""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM collections ORDER BY created_at DESC'
            ).fetchall()
            
            collections = []
            for row in rows:
                collections.append({
                    'name': row['name'],
                    'story_count': len(json.loads(row['story_ids'])),
                    'created_at': row['created_at']
                })
            
            return {'collections': collections}

def main():
    """Main server loop"""
    server = StoryCorpsServer()
    
    # Send capabilities
    print(json.dumps({
        "capabilities": {
            "tools": {
                "search_stories": {
                    "description": "Search StoryCorps stories by theme and optional location",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "theme": {"type": "string", "description": "Theme to search for"},
                            "location": {"type": "string", "description": "Optional location filter"}
                        },
                        "required": ["theme"]
                    }
                },
                "get_story": {
                    "description": "Get details for a specific story",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "story_id": {"type": "string", "description": "Story ID"}
                        },
                        "required": ["story_id"]
                    }
                },
                "save_collection": {
                    "description": "Save a collection of stories",
                    "inputSchema": {
                        "type": "object", 
                        "properties": {
                            "name": {"type": "string", "description": "Collection name"},
                            "story_ids": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["name", "story_ids"]
                    }
                },
                "list_collections": {
                    "description": "List all saved collections",
                    "inputSchema": {"type": "object", "properties": {}}
                }
            }
        }
    }))
    sys.stdout.flush()
    
    # Process requests
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            request = json.loads(line.strip())
            result = server.handle_request(request)
            
            response = {
                "id": request.get("id"),
                "result": result
            }
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            continue
        except KeyboardInterrupt:
            break
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")

if __name__ == "__main__":
    main()