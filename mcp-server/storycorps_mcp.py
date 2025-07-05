#!/usr/bin/env python3
"""
StoryCorps MCP Server - Explore human connections through stories
"""

import json
import sqlite3
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import urllib.request
import urllib.parse

# MCP imports
from mcp import MCPServer, Tool, ToolResult

class StoryCorpsMCP:
    def __init__(self):
        self.db_path = Path.home() / ".storycorps_cache.db"
        self.cache_duration = timedelta(days=30)  # Stories stay fresh for 30 days
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Stories table
        c.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY,
                story_id TEXT UNIQUE,
                title TEXT,
                description TEXT,
                keywords TEXT,  -- JSON array
                location_region TEXT,
                location_country TEXT,
                url TEXT,
                audio_url TEXT,
                participants TEXT,  -- JSON array
                cached_at TIMESTAMP,
                raw_data TEXT  -- Full JSON response
            )
        ''')
        
        # Search cache table
        c.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                query_hash TEXT PRIMARY KEY,
                query TEXT,
                story_ids TEXT,  -- JSON array
                cached_at TIMESTAMP
            )
        ''')
        
        # Pattern analysis cache
        c.execute('''
            CREATE TABLE IF NOT EXISTS pattern_cache (
                analysis_id TEXT PRIMARY KEY,
                theme TEXT,
                story_ids TEXT,  -- JSON array
                unity_score REAL,
                surface_differences TEXT,  -- JSON
                deep_connections TEXT,  -- JSON
                surprising_unity TEXT,
                concrete_examples TEXT,  -- JSON
                analysis_text TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        # Collections for saved explorations
        c.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                name TEXT PRIMARY KEY,
                description TEXT,
                story_ids TEXT,  -- JSON array
                created_at TIMESTAMP,
                notes TEXT
            )
        ''')
        
        # Create indexes
        c.execute('CREATE INDEX IF NOT EXISTS idx_keywords ON stories(keywords)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_location ON stories(location_region)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_cached_at ON stories(cached_at)')
        
        conn.commit()
        conn.close()
    
    def _get_cache_status(self) -> Dict[str, int]:
        """Get current cache statistics"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        stats = {
            'total_stories': c.execute('SELECT COUNT(*) FROM stories').fetchone()[0],
            'unique_locations': c.execute('SELECT COUNT(DISTINCT location_region) FROM stories WHERE location_region IS NOT NULL').fetchone()[0],
            'saved_patterns': c.execute('SELECT COUNT(*) FROM pattern_cache').fetchone()[0],
            'collections': c.execute('SELECT COUNT(*) FROM collections').fetchone()[0]
        }
        
        conn.close()
        return stats
    
    def _search_cache_first(self, theme: str, location: Optional[str] = None) -> Optional[List[Dict]]:
        """Check if we have cached stories for this search"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Build query
        query_parts = [f"keywords LIKE '%{theme}%' OR description LIKE '%{theme}%'"]
        if location:
            query_parts.append(f"location_region LIKE '%{location}%'")
        
        where_clause = ' AND '.join(query_parts)
        
        # Check if we have fresh cached results
        results = c.execute(f'''
            SELECT * FROM stories 
            WHERE {where_clause}
            AND cached_at > datetime('now', '-30 days')
            LIMIT 20
        ''').fetchall()
        
        conn.close()
        
        if results:
            return [dict(row) for row in results]
        return None
    
    def _fetch_from_api(self, theme: str, max_pages: int = 5) -> List[Dict]:
        """Fetch stories from StoryCorps API"""
        base_url = 'https://archive.storycorps.org/wp-json/storycorps/v1/interviews'
        stories = []
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{base_url}?per_page=10&page={page}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mosaic/1.0'})
                
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read())
                    
                    # Filter by theme
                    for story in data:
                        keywords = [k.lower() for k in (story.get('keywords') or [])]
                        description = (story.get('description') or '').lower()
                        
                        if theme.lower() in ' '.join(keywords) or theme.lower() in description:
                            stories.append(story)
                            # Cache the story
                            self._cache_story(story)
                    
                    if len(stories) >= 20:
                        break
                        
            except Exception as e:
                print(f"API fetch error: {e}")
                break
        
        return stories
    
    def _cache_story(self, story: Dict):
        """Cache a story in the database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT OR REPLACE INTO stories 
                (story_id, title, description, keywords, location_region, 
                 location_country, url, audio_url, participants, cached_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                story.get('id'),
                story.get('title'),
                story.get('description'),
                json.dumps(story.get('keywords', [])),
                story.get('location', {}).get('region', [None])[0],
                story.get('location', {}).get('country'),
                story.get('url'),
                story.get('audio_url'),
                json.dumps(story.get('participants', [])),
                datetime.now(),
                json.dumps(story)
            ))
            conn.commit()
        except Exception as e:
            print(f"Cache error: {e}")
        finally:
            conn.close()
    
    async def search_stories(self, theme: str, location: Optional[str] = None, 
                           use_cache: bool = True) -> ToolResult:
        """Search for stories by theme and optional location"""
        # Try cache first
        if use_cache:
            cached = self._search_cache_first(theme, location)
            if cached:
                return ToolResult(
                    success=True,
                    data={
                        'stories': cached,
                        'count': len(cached),
                        'source': 'cache',
                        'message': f"Found {len(cached)} cached stories about '{theme}'"
                    }
                )
        
        # Fetch from API
        stories = self._fetch_from_api(theme)
        
        if location and stories:
            # Filter by location
            stories = [s for s in stories 
                      if location.lower() in (s.get('location', {}).get('region', [''])[0] or '').lower()]
        
        return ToolResult(
            success=True,
            data={
                'stories': stories,
                'count': len(stories),
                'source': 'api',
                'message': f"Found {len(stories)} stories about '{theme}'" + 
                          (f" in {location}" if location else "")
            }
        )
    
    async def analyze_unity(self, story_ids: List[int], theme: str) -> ToolResult:
        """Analyze unity patterns across stories"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get stories
        placeholders = ','.join('?' * len(story_ids))
        stories = c.execute(f'''
            SELECT * FROM stories 
            WHERE story_id IN ({placeholders})
        ''', story_ids).fetchall()
        
        conn.close()
        
        if not stories:
            return ToolResult(success=False, error="Stories not found in cache")
        
        # Build analysis
        analysis = {
            'theme': theme,
            'story_count': len(stories),
            'locations': list(set(s['location_region'] for s in stories if s['location_region'])),
            'surface_differences': [
                f"{len(set(s['location_region'] for s in stories if s['location_region']))} different regions",
                f"Stories spanning {stories[-1]['cached_at'][:10]} to {stories[0]['cached_at'][:10]}",
                "Diverse backgrounds and life circumstances"
            ],
            'deep_connections': [
                f"All explore themes of {theme}",
                "Shared human experiences across geography",
                "Common emotional threads despite different contexts"
            ],
            'unity_score': 0.75,  # Simplified - would use Claude in production
            'preview_stories': [
                {
                    'id': s['story_id'],
                    'title': s['title'],
                    'location': s['location_region'],
                    'url': s['url'],
                    'snippet': s['description'][:200] + '...' if s['description'] else ''
                }
                for s in stories[:3]
            ]
        }
        
        # Cache the analysis
        analysis_id = hashlib.md5(f"{theme}:{','.join(map(str, story_ids))}".encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO pattern_cache
            (analysis_id, theme, story_ids, unity_score, surface_differences,
             deep_connections, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis_id,
            theme,
            json.dumps(story_ids),
            analysis['unity_score'],
            json.dumps(analysis['surface_differences']),
            json.dumps(analysis['deep_connections']),
            datetime.now()
        ))
        conn.commit()
        conn.close()
        
        return ToolResult(success=True, data=analysis)
    
    async def get_story_details(self, story_id: int) -> ToolResult:
        """Get full details for a specific story"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        story = c.execute('SELECT * FROM stories WHERE story_id = ?', (story_id,)).fetchone()
        conn.close()
        
        if not story:
            return ToolResult(success=False, error="Story not found in cache")
        
        return ToolResult(
            success=True,
            data={
                'id': story['story_id'],
                'title': story['title'],
                'description': story['description'],
                'keywords': json.loads(story['keywords']),
                'location': {
                    'region': story['location_region'],
                    'country': story['location_country']
                },
                'url': story['url'],
                'audio_url': story['audio_url'],
                'participants': json.loads(story['participants'] or '[]'),
                'cached_at': story['cached_at']
            }
        )
    
    async def save_collection(self, name: str, story_ids: List[int], 
                            description: str = "", notes: str = "") -> ToolResult:
        """Save a collection of stories for future reference"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT OR REPLACE INTO collections
                (name, description, story_ids, created_at, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                name,
                description,
                json.dumps(story_ids),
                datetime.now(),
                notes
            ))
            conn.commit()
            conn.close()
            
            return ToolResult(
                success=True,
                data={'message': f"Collection '{name}' saved with {len(story_ids)} stories"}
            )
        except Exception as e:
            conn.close()
            return ToolResult(success=False, error=str(e))
    
    async def list_collections(self) -> ToolResult:
        """List all saved collections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        collections = c.execute('''
            SELECT name, description, story_ids, created_at 
            FROM collections 
            ORDER BY created_at DESC
        ''').fetchall()
        
        conn.close()
        
        result = []
        for coll in collections:
            story_ids = json.loads(coll['story_ids'])
            result.append({
                'name': coll['name'],
                'description': coll['description'],
                'story_count': len(story_ids),
                'created_at': coll['created_at']
            })
        
        return ToolResult(success=True, data={'collections': result})
    
    async def compare_stories(self, story_id1: int, story_id2: int) -> ToolResult:
        """Deep comparison of two specific stories"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        stories = c.execute('''
            SELECT * FROM stories 
            WHERE story_id IN (?, ?)
        ''', (story_id1, story_id2)).fetchall()
        
        conn.close()
        
        if len(stories) != 2:
            return ToolResult(success=False, error="Could not find both stories")
        
        s1, s2 = stories[0], stories[1]
        
        # Extract comparison
        comparison = {
            'story_1': {
                'title': s1['title'],
                'location': s1['location_region'],
                'keywords': json.loads(s1['keywords']),
                'url': s1['url']
            },
            'story_2': {
                'title': s2['title'], 
                'location': s2['location_region'],
                'keywords': json.loads(s2['keywords']),
                'url': s2['url']
            },
            'differences': {
                'locations': f"{s1['location_region']} vs {s2['location_region']}",
                'unique_keywords_1': list(set(json.loads(s1['keywords'])) - set(json.loads(s2['keywords']))),
                'unique_keywords_2': list(set(json.loads(s2['keywords'])) - set(json.loads(s1['keywords'])))
            },
            'similarities': {
                'shared_keywords': list(set(json.loads(s1['keywords'])) & set(json.loads(s2['keywords']))),
                'both_have_audio': bool(s1['audio_url'] and s2['audio_url'])
            }
        }
        
        return ToolResult(success=True, data=comparison)
    
    async def find_similar(self, story_id: int, limit: int = 5) -> ToolResult:
        """Find stories similar to a given story"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get the reference story
        ref_story = c.execute('SELECT * FROM stories WHERE story_id = ?', (story_id,)).fetchone()
        
        if not ref_story:
            conn.close()
            return ToolResult(success=False, error="Story not found")
        
        ref_keywords = set(json.loads(ref_story['keywords']))
        
        # Find stories with overlapping keywords
        all_stories = c.execute('''
            SELECT * FROM stories 
            WHERE story_id != ?
        ''', (story_id,)).fetchall()
        
        conn.close()
        
        # Score by keyword overlap
        scored_stories = []
        for story in all_stories:
            keywords = set(json.loads(story['keywords']))
            overlap = len(ref_keywords & keywords)
            if overlap > 0:
                scored_stories.append((overlap, story))
        
        # Sort by score and return top matches
        scored_stories.sort(key=lambda x: x[0], reverse=True)
        
        similar = []
        for score, story in scored_stories[:limit]:
            similar.append({
                'id': story['story_id'],
                'title': story['title'],
                'location': story['location_region'],
                'shared_keywords': list(ref_keywords & set(json.loads(story['keywords']))),
                'similarity_score': score,
                'url': story['url']
            })
        
        return ToolResult(
            success=True,
            data={
                'reference_story': ref_story['title'],
                'similar_stories': similar
            }
        )
    
    async def cache_status(self) -> ToolResult:
        """Get current cache statistics"""
        stats = self._get_cache_status()
        
        # Add recent searches
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        recent = c.execute('''
            SELECT DISTINCT theme, COUNT(*) as count
            FROM pattern_cache
            GROUP BY theme
            ORDER BY MAX(created_at) DESC
            LIMIT 10
        ''').fetchall()
        
        conn.close()
        
        stats['recent_themes'] = [{'theme': r[0], 'analyses': r[1]} for r in recent]
        
        return ToolResult(success=True, data=stats)


# Create the MCP server
server = MCPServer("storycorps-explorer", "1.0.0")
mcp = StoryCorpsMCP()

# Register tools
server.add_tool(Tool(
    name="search_stories",
    description="Search for StoryCorps stories by theme and optional location. Uses cache when available.",
    parameters={
        "theme": {"type": "string", "description": "Theme or topic to search for"},
        "location": {"type": "string", "description": "Optional location filter", "required": False},
        "use_cache": {"type": "boolean", "description": "Use cached results if available", "default": True}
    },
    handler=mcp.search_stories
))

server.add_tool(Tool(
    name="analyze_unity",
    description="Analyze unity patterns across multiple stories",
    parameters={
        "story_ids": {"type": "array", "description": "List of story IDs to analyze"},
        "theme": {"type": "string", "description": "Theme being explored"}
    },
    handler=mcp.analyze_unity
))

server.add_tool(Tool(
    name="get_story_details",
    description="Get full details for a specific story including URL",
    parameters={
        "story_id": {"type": "integer", "description": "Story ID"}
    },
    handler=mcp.get_story_details
))

server.add_tool(Tool(
    name="compare_stories",
    description="Deep comparison of two specific stories",
    parameters={
        "story_id1": {"type": "integer", "description": "First story ID"},
        "story_id2": {"type": "integer", "description": "Second story ID"}
    },
    handler=mcp.compare_stories
))

server.add_tool(Tool(
    name="find_similar",
    description="Find stories similar to a given story",
    parameters={
        "story_id": {"type": "integer", "description": "Reference story ID"},
        "limit": {"type": "integer", "description": "Maximum similar stories to return", "default": 5}
    },
    handler=mcp.find_similar
))

server.add_tool(Tool(
    name="save_collection",
    description="Save a collection of stories for future reference",
    parameters={
        "name": {"type": "string", "description": "Collection name"},
        "story_ids": {"type": "array", "description": "Story IDs to include"},
        "description": {"type": "string", "description": "Collection description", "required": False},
        "notes": {"type": "string", "description": "Additional notes", "required": False}
    },
    handler=mcp.save_collection
))

server.add_tool(Tool(
    name="list_collections", 
    description="List all saved story collections",
    parameters={},
    handler=mcp.list_collections
))

server.add_tool(Tool(
    name="cache_status",
    description="Get cache statistics and recent searches",
    parameters={},
    handler=mcp.cache_status
))

if __name__ == "__main__":
    import sys
    server.run(sys.stdin, sys.stdout)