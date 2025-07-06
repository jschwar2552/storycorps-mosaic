#!/usr/bin/env python3
"""
StoryCorps MCP Server - Fixed version addressing common gotchas
"""

import json
import sqlite3
import sys
import os
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.parse
import logging

# Set up logging to debug issues
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.claude' / 'storycorps_mcp.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger('storycorps_mcp')

# Initialize database
DB_PATH = Path.home() / ".storycorps_cache.db"

def init_database():
    """Initialize SQLite database"""
    try:
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
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def main():
    """Main MCP server loop with proper error handling"""
    logger.info("StoryCorps MCP Server starting...")
    
    try:
        init_database()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
    
    # MCP Protocol: Send capabilities
    capabilities = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "capabilities": {
                "tools": {
                    "search_stories": {
                        "description": "Search for StoryCorps stories by theme",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "theme": {"type": "string"},
                                "location": {"type": "string", "optional": True}
                            },
                            "required": ["theme"]
                        }
                    },
                    "get_story": {
                        "description": "Get details for a specific story",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "story_id": {"type": "string"}
                            },
                            "required": ["story_id"]
                        }
                    },
                    "save_collection": {
                        "description": "Save a collection of stories",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "story_ids": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["name", "story_ids"]
                        }
                    },
                    "list_collections": {
                        "description": "List all saved collections",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                }
            },
            "serverInfo": {
                "name": "storycorps",
                "version": "1.0.0"
            }
        }
    }
    
    print(json.dumps(capabilities))
    sys.stdout.flush()
    
    # Main request loop
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                logger.info("EOF received, shutting down")
                break
            
            line = line.strip()
            if not line:
                continue
                
            logger.debug(f"Received request: {line[:100]}...")
            
            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error",
                        "data": str(e)
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
                continue
            
            method = request.get('method')
            params = request.get('params', {})
            request_id = request.get('id')
            
            logger.debug(f"Processing method: {method}")
            
            # Handle methods
            result = None
            error = None
            
            try:
                if method == 'tools/search_stories':
                    result = search_stories(params.get('theme'), params.get('location'))
                elif method == 'tools/get_story':
                    result = get_story(params.get('story_id'))
                elif method == 'tools/save_collection':
                    result = save_collection(params.get('name'), params.get('story_ids'))
                elif method == 'tools/list_collections':
                    result = list_collections()
                else:
                    error = {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
            except Exception as e:
                logger.error(f"Error processing {method}: {e}", exc_info=True)
                error = {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            
            # Send response
            response = {
                "jsonrpc": "2.0",
                "id": request_id
            }
            
            if error:
                response["error"] = error
            else:
                response["result"] = result
                
            logger.debug(f"Sending response for {method}")
            print(json.dumps(response))
            sys.stdout.flush()
            
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            # Try to send error response
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
    
    logger.info("StoryCorps MCP Server shutting down")

def search_stories(theme, location=None):
    """Search for stories by theme"""
    logger.info(f"Searching for theme: {theme}, location: {location}")
    
    if not theme:
        raise ValueError("Theme is required")
    
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
        logger.info(f"Found {len(stories)} stories in cache")
        return {
            'source': 'cache',
            'stories': stories,
            'count': len(stories),
            'message': f"Found {len(stories)} cached stories about '{theme}'"
        }
    
    # Fetch from API
    logger.info("Cache miss, fetching from API")
    stories = fetch_from_api(theme)
    conn.close()
    
    return {
        'source': 'api',
        'stories': stories,
        'count': len(stories),
        'message': f"Found {len(stories)} stories about '{theme}' from StoryCorps"
    }

def fetch_from_api(theme):
    """Fetch stories from StoryCorps API"""
    base_url = 'https://archive.storycorps.org/wp-json/storycorps/v1/interviews'
    stories = []
    
    for page in range(1, 4):
        try:
            url = f"{base_url}?per_page=10&page={page}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mosaic-MCP/1.0'})
            
            logger.debug(f"Fetching page {page} from API")
            
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
            logger.error(f"API fetch error: {e}")
            break
    
    logger.info(f"Fetched {len(stories)} stories from API")
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
        logger.debug(f"Cached story: {story['title']}")
    except Exception as e:
        logger.error(f"Cache error: {e}")
    finally:
        conn.close()

def get_story(story_id):
    """Get details for a specific story"""
    if not story_id:
        raise ValueError("Story ID is required")
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    result = c.execute('SELECT * FROM stories WHERE story_id = ?', (story_id,)).fetchone()
    conn.close()
    
    if result:
        story = dict(result)
        story['keywords'] = json.loads(story['keywords'])
        return story
    else:
        return {'error': f'Story {story_id} not found in cache'}

def save_collection(name, story_ids):
    """Save a collection of stories"""
    if not name or not story_ids:
        raise ValueError("Name and story_ids are required")
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT OR REPLACE INTO collections (name, story_ids, created_at)
        VALUES (?, ?, ?)
    ''', (name, json.dumps(story_ids), datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Saved collection '{name}' with {len(story_ids)} stories")
    return {'message': f"Saved collection '{name}' with {len(story_ids)} stories"}

def list_collections():
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

if __name__ == "__main__":
    # Handle process termination gracefully
    import signal
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)