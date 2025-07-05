# CORS Issue Analysis & Solutions

## Problem Summary
The Mosaic app was experiencing "Failed to fetch" errors when the GitHub Pages frontend tried to call the Vercel API. After thorough testing, I identified two main issues:

1. **Missing OPTIONS handler**: The API was returning 405 for preflight requests
2. **Frontend configuration**: Missing homepage field and hardcoded API URL

## Issues Found

### 1. API Not Handling OPTIONS Requests
- Browsers send OPTIONS requests for CORS preflight checks
- The API was returning 405 (Method Not Allowed) for OPTIONS
- Even though CORS headers were present, the 405 status caused failures

### 2. Frontend Configuration Issues
- Missing `homepage` field in package.json for GitHub Pages
- Hardcoded API URL instead of using environment variables
- No production environment configuration

## Solutions Implemented

### 1. Fixed API Handler
Added OPTIONS request handling in `/api/chat.js`:
```javascript
if (req.method === 'OPTIONS') {
  return res.status(200).end();
}
```

### 2. Updated Frontend Configuration
- Added `homepage` field to `frontend/package.json`
- Created `.env.production` with API URL
- Updated App.js to use environment variable:
```javascript
const apiUrl = process.env.REACT_APP_API_URL || 'https://storycorps-mosaic.vercel.app';
```

### 3. Created Deployment Script
Added `deploy.sh` for easy deployment of both services

## Testing Results

### API Direct Test ✅
```bash
curl -X POST https://storycorps-mosaic.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about family struggles"}'
```
- Returns 200 OK with proper data
- CORS headers present: `Access-Control-Allow-Origin: *`

### OPTIONS Preflight Test ✅
```bash
curl -X OPTIONS https://storycorps-mosaic.vercel.app/api/chat \
  -H "Origin: https://jschwar2552.github.io"
```
- Now returns 200 OK (previously 405)
- CORS headers properly set

## Alternative Approaches Considered

### A. Current Approach: Fix CORS (Recommended) ✅
**Pros:**
- Real-time data from StoryCorps API
- Claude AI analysis for each query
- Dynamic and personalized responses
- Scalable architecture

**Cons:**
- Requires API key management
- Potential API rate limits
- Network latency

### B. Preloaded/Static Data Approach
**Pros:**
- No CORS issues
- Faster response times
- Works offline
- No API costs

**Cons:**
- Static data becomes outdated
- Limited analysis capabilities
- Larger bundle size
- Less personalized responses

### C. Different Architecture Options

#### Option 1: Proxy Server
- Add a simple proxy server to handle CORS
- Could use Cloudflare Workers or similar

#### Option 2: Single Domain
- Host both frontend and API on Vercel
- Eliminates CORS entirely

#### Option 3: Static Site with Serverless Functions
- Use Netlify or Vercel for both frontend and functions
- Simpler deployment

## Recommendations

### Immediate Actions ✅
1. Deploy the API with OPTIONS fix: `vercel --prod`
2. Rebuild and deploy frontend: `cd frontend && npm run deploy`
3. Test the full flow from GitHub Pages

### Future Improvements
1. **Add Error Retry Logic**: Implement exponential backoff for failed requests
2. **Cache Responses**: Use localStorage to cache successful responses
3. **Offline Mode**: Preload some sample data for offline demos
4. **Rate Limiting UI**: Show remaining API calls to users
5. **Loading States**: Better loading indicators during API calls

### Monitoring
1. Add error tracking (e.g., Sentry)
2. Monitor API response times
3. Track CORS failures vs other errors
4. Set up alerts for API downtime

## Quick Deploy Commands

```bash
# Deploy everything
./deploy.sh

# Or manually:
# Deploy API
vercel --prod

# Deploy Frontend
cd frontend
npm run build
npm run deploy
```

## Testing the Fix

1. Visit: https://jschwar2552.github.io/storycorps-mosaic/
2. Type a query like "Tell me about family struggles"
3. Should see successful response with unity score and stories

## Debug Checklist
- [ ] API returns 200 for OPTIONS requests
- [ ] Frontend uses correct API URL
- [ ] CORS headers include Access-Control-Allow-Origin
- [ ] No console errors about CORS
- [ ] Network tab shows successful preflight
- [ ] Response data renders correctly