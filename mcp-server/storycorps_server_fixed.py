#!/usr/bin/env python3
"""
StoryCorps MCP Server - Fixed for Claude Desktop
Proper MCP protocol implementation with initialization handshake
"""

import json
import sys
import sqlite3
from pathlib import Path
import urllib.request
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.storycorps_mcp.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger('storycorps_mcp')

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
        method = request.get('method', '')
        params = request.get('params', {})
        
        # Handle initialization
        if method == 'initialize':
            return {
                "protocolVersion": "0.1.0",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "storycorps",
                    "version": "1.0.0"
                }
            }
        
        # Handle tool listing
        if method == 'tools/list':
            return {
                "tools": [
                    {
                        "name": "search_stories",
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
                    {
                        "name": "get_story",
                        "description": "Get details for a specific story",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "story_id": {"type": "string", "description": "Story ID"}
                            },
                            "required": ["story_id"]
                        }
                    },
                    {
                        "name": "save_collection",
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
                    {
                        "name": "list_collections",
                        "description": "List all saved collections",
                        "inputSchema": {"type": "object", "properties": {}}
                    }
                ]
            }
        
        # Handle tool calls
        if method.startswith('tools/call'):
            tool_name = params.get('name')
            tool_params = params.get('arguments', {})
            
            handlers = {
                'search_stories': lambda: self.search_stories(
                    tool_params.get('theme', ''),
                    tool_params.get('location')
                ),
                'get_story': lambda: self.get_story(tool_params.get('story_id')),
                'save_collection': lambda: self.save_collection(
                    tool_params.get('name'),
                    tool_params.get('story_ids', [])
                ),
                'list_collections': lambda: self.list_collections()
            }
            
            handler = handlers.get(tool_name)
            if handler:
                try:
                    result = handler()
                    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
                except Exception as e:
                    return {"error": {"code": -32603, "message": str(e)}}
            else:
                return {"error": {"code": -32601, "message": f'Unknown tool: {tool_name}'}}
        
        return {"error": {"code": -32601, "message": f'Unknown method: {method}'}}
    
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
                logger.error(f"API error: {e}")
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
    """Main server loop following MCP protocol"""
    server = StoryCorpsServer()
    logger.info("StoryCorps MCP Server starting...")
    
    # Process requests
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            request = json.loads(line.strip())
            logger.debug(f"Received request: {request}")
            
            result = server.handle_request(request)
            
            response = {
                "jsonrpc": "2.0",
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
            logger.error(f"Error: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()