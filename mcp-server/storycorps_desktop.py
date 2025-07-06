#!/usr/bin/env python3
"""
StoryCorps MCP Server for Claude Desktop
Compatible with Claude Desktop's MCP implementation
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
    
    def search_stories(self, theme, location=None):
        """Search for stories by theme"""
        if not theme:
            raise ValueError("Theme is required")
        
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
        stories = self.fetch_from_api(theme, location)
        return {
            'stories': stories,
            'count': len(stories),
            'source': 'api',
            'message': f"Found {len(stories)} stories about '{theme}' from StoryCorps"
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
                            self.cache_story(formatted)
                            
                            if len(stories) >= 10:
                                return stories
                                
            except Exception as e:
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
            raise ValueError("Story ID required")
            
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
                raise ValueError(f'Story {story_id} not found')
    
    def save_collection(self, name, story_ids):
        """Save a story collection"""
        if not name:
            raise ValueError("Collection name required")
            
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
    """Main server loop for Claude Desktop MCP"""
    server = StoryCorpsServer()
    
    # Main request/response loop
    while True:
        try:
            # Read request from stdin
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line.strip())
            
            # Extract method and params
            method = request.get('method')
            params = request.get('params', {})
            request_id = request.get('id')
            
            # Handle different methods
            if method == 'initialize':
                # Respond to initialization
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
                # List available tools
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
                        },
                        {
                            "name": "get_story",
                            "description": "Get details for a specific story by ID",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "story_id": {
                                        "type": "string",
                                        "description": "Story ID to retrieve"
                                    }
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
                                    "name": {
                                        "type": "string",
                                        "description": "Name for the collection"
                                    },
                                    "story_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of story IDs to save"
                                    }
                                },
                                "required": ["name", "story_ids"]
                            }
                        },
                        {
                            "name": "list_collections",
                            "description": "List all saved story collections",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    ]
                }
            
            elif method == 'tools/call':
                # Handle tool calls
                tool_name = params.get('name')
                tool_args = params.get('arguments', {})
                
                try:
                    if tool_name == 'search_stories':
                        result_data = server.search_stories(
                            tool_args.get('theme'),
                            tool_args.get('location')
                        )
                    elif tool_name == 'get_story':
                        result_data = server.get_story(tool_args.get('story_id'))
                    elif tool_name == 'save_collection':
                        result_data = server.save_collection(
                            tool_args.get('name'),
                            tool_args.get('story_ids', [])
                        )
                    elif tool_name == 'list_collections':
                        result_data = server.list_collections()
                    else:
                        raise ValueError(f"Unknown tool: {tool_name}")
                    
                    # Format the result
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result_data, indent=2)
                            }
                        ]
                    }
                    
                except Exception as e:
                    # Return error in expected format
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: {str(e)}"
                            }
                        ],
                        "isError": True
                    }
            
            else:
                # Unknown method
                result = {"error": {"code": -32601, "message": f"Method not found: {method}"}}
            
            # Send response
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            # Invalid JSON
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
            
        except Exception as e:
            # Other errors
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()