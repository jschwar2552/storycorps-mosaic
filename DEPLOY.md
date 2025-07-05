# Deploying Mosaic to Vercel

## Quick Deploy Guide

### 1. Install Vercel CLI
```bash
npm install -g vercel
```

### 2. Set up Environment Variable
In Vercel dashboard (vercel.com):
1. Go to your project settings
2. Click "Environment Variables"
3. Add: `ANTHROPIC_API_KEY` with your key value
4. ✅ Your API key is secure and never exposed!

### 3. Deploy
```bash
# From project root
vercel

# Follow prompts:
# - Link to existing project or create new
# - Use default settings
# - Deploy!
```

### 4. Test Your Deployment
Visit: `https://your-project.vercel.app`

Try queries like:
- "Tell me about families overcoming struggles"
- "How do immigrants find belonging?"
- "Show me stories about hope in hard times"

## How It Works

```
User Query → Vercel Function → StoryCorps API → Claude Analysis → Response
```

1. **Frontend** (React) sends chat messages to `/api/chat`
2. **Vercel Function** processes the query securely
3. **Claude** analyzes patterns in real-time
4. **Response** shows unity scores and story connections

## Security

- ✅ API key stored in Vercel environment variables
- ✅ Never exposed in frontend code
- ✅ All API calls happen server-side
- ✅ HTTPS everywhere

## Costs

- **Vercel**: Free tier includes 100GB bandwidth
- **Claude API**: ~$0.01-0.02 per query (Haiku model)
- **Estimated**: 5,000-10,000 free queries per month

## Local Development

```bash
# Set up env variable locally
export ANTHROPIC_API_KEY='your-key-here'

# Run development server
vercel dev

# Visit http://localhost:3000
```

## Monitoring

Check Vercel dashboard for:
- Function logs
- API usage
- Error tracking
- Performance metrics