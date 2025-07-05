# Setting Up StoryCorps MCP Server

## Quick Setup

1. **Add to Claude Code MCP configuration**:
```bash
claude mcp add storycorps python3 /Users/jason/storycorps-mosaic/mcp-server/server.py
```

2. **Restart Claude Code** to load the new server

3. **Test it's working**:
   - In Claude, type: "Search for stories about family"
   - You should see results from StoryCorps

## Available Commands

Once configured, you can ask Claude things like:

### Basic Search
- "Search for stories about resilience"
- "Find stories about immigrants in New York"
- "Show me stories about loss from rural areas"

### Working with Results
- "Save these as 'Family Resilience' collection"
- "Show me my saved collections"
- "Tell me more about the third story"

### Exploration
- "What themes connect these stories?"
- "Find more stories like this one"
- "Compare the NYC story with the rural one"

## How It Works

1. **First search** for a theme fetches from API and caches locally
2. **Subsequent searches** use cache (instant, no API calls)
3. **Collections** let you save interesting story groups
4. **Links included** - every story has its StoryCorps URL

## Tips

- The cache builds progressively as you explore
- Stories stay cached for reuse
- Each story includes a direct link to StoryCorps
- Collections persist between sessions

## Troubleshooting

If the server isn't working:

1. Check it's added to MCP:
```bash
claude mcp list
```

2. Test manually:
```bash
python3 /Users/jason/storycorps-mosaic/mcp-server/test_server.py
```

3. Restart Claude Code completely

## Database Location

Your story cache is stored at: `~/.storycorps_cache.db`

This file will grow as you explore more themes and stories.