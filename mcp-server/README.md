# StoryCorps MCP Server

A Model Context Protocol server for exploring human connections through StoryCorps stories.

## Features

- **Smart Caching**: Cache stories locally to avoid API limits
- **Rich Search**: Find stories by theme, location, keywords
- **Unity Analysis**: Discover connections between different people
- **Story Comparison**: Deep dive into specific story pairs
- **Collections**: Save and organize your discoveries
- **Similar Stories**: Find related stories automatically

## Installation

1. Install the MCP package:
```bash
pip install mcp
```

2. Make the server executable:
```bash
chmod +x storycorps_mcp.py
```

3. Add to Claude Code:
```bash
claude mcp add storycorps /Users/jason/storycorps-mosaic/mcp-server/storycorps_mcp.py
```

## Usage

Once configured, you can use these commands in Claude:

### Search for Stories
```
Search for stories about "resilience"
Find immigrant stories from New York
Show me stories about family from rural areas
```

### Analyze Patterns
```
Analyze unity between stories [1234, 5678, 9012]
What connects these stories about loss?
Show me the differences and connections
```

### Compare Stories
```
Compare story 1234 with story 5678
What's different about these two perspectives?
```

### Find Similar Stories
```
Find stories similar to 1234
Show me more like this story about hope
```

### Save Collections
```
Save these stories as "Resilience Across Cultures"
Create a collection called "Urban vs Rural Family"
List my saved collections
```

### Check Cache
```
Show cache status
How many stories are cached?
What themes have I explored?
```

## How It Works

1. **Cache-First**: Checks local SQLite cache before hitting API
2. **Progressive Building**: Cache grows as you explore
3. **30-Day Freshness**: Stories stay cached for 30 days
4. **Pattern Memory**: Saves your unity analyses
5. **Direct Links**: Every story includes its StoryCorps URL

## Database Schema

- `stories`: Cached story data with keywords, location, URL
- `pattern_cache`: Saved unity analyses
- `collections`: Your curated story groups
- `search_cache`: Query results cache

## Tips

- Start broad ("family") then narrow ("single parent families")
- Use location filters to compare regions
- Save interesting patterns as collections
- Check cache status to see your exploration history
- Stories include direct links to StoryCorps for full experience

## Advantages Over Website

- **Conversational**: Ask follow-ups, clarify, explore
- **No API Limits**: Smart caching prevents rate limiting
- **Deeper Analysis**: Claude can do richer pattern finding
- **Personal Dataset**: Build your own research cache
- **Flexible Queries**: Complex comparisons and searches

Enjoy exploring human connections!