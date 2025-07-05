# Testing Mosaic Pattern Discovery

## Quick Start

1. **Set up environment**:
   ```bash
   cd backend
   chmod +x setup_test_env.sh
   ./setup_test_env.sh
   ```

2. **Add your Claude API key**:
   ```bash
   # Edit .env file
   ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
   ```

3. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

4. **Run the test**:
   ```bash
   python test_with_claude.py
   ```

## What the Test Does

1. **Analyzes keywords** from 30 StoryCorps interviews
2. **Discovers unity patterns** for a theme (e.g., "family")
3. **Finds story pairs** that show deep connections
4. **Uses Claude** to analyze why stories connect across differences

## Expected Output

```
🎭 Mosaic Pattern Discovery - Testing with Claude
============================================================

📊 Step 1: Analyzing keyword distribution...
Top themes found:
  - family: 15 occurrences
  - work: 8 occurrences
  - love: 6 occurrences

🎯 Selected theme for analysis: 'family'

🔍 Step 2: Discovering unity pattern for 'family'...

✨ Unity Pattern Discovered!
Theme: family
Unity Score: 0.85 (0=divided, 1=universal)
Demographics analyzed: urban_newyork, rural_iowa, mixed_texas
Sample size: 42 interviews

📝 Claude's Insights:
The theme of family transcends all demographic boundaries...

💫 Step 3: Finding powerful story pair for 'family'...

🤝 Story Pair Found!
📖 Story A: Rural Farmer's Story
   Location: Iowa
📖 Story B: Urban Immigrant's Tale  
   Location: New York

🌍 Surface Differences:
   - Rural Iowa farmer vs Urban New York immigrant
   - Native-born vs foreign-born

❤️ Deep Connections:
   - Both experienced profound loss
   - Family as source of strength

✨ Unity Score: 0.92
```

## Cost Estimate

- Each test run costs approximately $0.10-0.20 in Claude API usage
- Uses Claude 3 Haiku for efficiency
- Caches results to avoid duplicate API calls

## Troubleshooting

1. **No ANTHROPIC_API_KEY**: Get one at https://console.anthropic.com/
2. **Import errors**: Make sure you activated the virtual environment
3. **Rate limits**: Wait a few minutes between test runs

## Next Steps

After successful testing:
1. Run `pytest tests/` to run unit tests
2. Try different themes to build pattern library
3. Move on to building the REST API