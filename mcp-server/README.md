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

The server is already configured! It's been added to Claude Code:

```bash
claude mcp list
# Output: storycorps: python3 /Users/jason/storycorps-mosaic/mcp-server/storycorps_server.py
```

**Important**: You need to restart Claude Code completely (Cmd+Q, wait 5-10 seconds, reopen) for the MCP server to load.

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
3. **Persistent Storage**: Stories stay cached between sessions
4. **Direct Links**: Every story includes its StoryCorps URL
5. **Gotcha-Resistant**: Handles MCP session restarts gracefully

## Architecture

The server (`storycorps_server.py`) addresses common MCP gotchas:
- **Proper JSON-RPC protocol** for stability
- **SQLite persistence** survives session restarts
- **Signal handling** for clean shutdown
- **Zombie process prevention**
- **Logging** to `~/.claude/storycorps_mcp.log`

## Database

Located at `~/.storycorps_cache.db`:
- `stories`: Cached story data with keywords, location, URL
- `collections`: Your curated story groups

## Tips

- Start broad ("family") then narrow ("single parent families")
- Use location filters to compare regions
- Save interesting patterns as collections
- Stories include direct links to StoryCorps for full experience

## Troubleshooting

If the MCP server isn't responding:

1. **Check for zombie processes**:
```bash
ps aux | grep storycorps_server
pkill -f storycorps_server
```

2. **Restart Claude Code completely** (Cmd+Q, wait 5-10 seconds)

3. **Check logs**:
```bash
tail -f ~/.claude/storycorps_mcp.log
```

4. **Verify configuration**:
```bash
claude mcp list
```

5. **Test manually**:
```bash
python3 /Users/jason/storycorps-mosaic/mcp-server/test_server.py
```

## Advantages Over Website

- **Conversational**: Ask follow-ups, clarify, explore
- **No API Limits**: Smart caching prevents rate limiting
- **Deeper Analysis**: Claude can do richer pattern finding
- **Personal Dataset**: Build your own research cache
- **Flexible Queries**: Complex comparisons and searches

Enjoy exploring human connections!