/**
 * Vercel Serverless Function for Mosaic Conversational UI
 * Handles chat-like queries about human connections
 */

export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Get user query
  const { message, context = {} } = req.body;

  if (!message) {
    return res.status(400).json({ error: 'Message required' });
  }

  // Check for API key
  const anthropicKey = process.env.ANTHROPIC_API_KEY;
  if (!anthropicKey) {
    return res.status(500).json({ error: 'API key not configured' });
  }

  try {
    // Parse user intent
    const intent = await parseUserIntent(message, anthropicKey);
    
    // Fetch relevant stories
    const stories = await fetchRelevantStories(intent);
    
    // Analyze with Claude
    const analysis = await analyzeConnections(stories, intent, anthropicKey);
    
    // Format conversational response
    const response = formatResponse(analysis, stories);
    
    // Cache result for performance
    await cacheResult(message, response);
    
    return res.status(200).json({
      response,
      intent,
      storyCount: stories.length,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Chat error:', error);
    return res.status(500).json({ 
      error: 'Failed to process query',
      message: error.message 
    });
  }
}

async function parseUserIntent(message, apiKey) {
  // Use Claude to understand what the user is looking for
  const prompt = `User message: "${message}"
  
Extract the user's intent for finding human connections:
1. THEME: What theme are they interested in? (e.g., struggle, hope, family)
2. EMOTION: What emotion are they expressing? (e.g., lonely, curious, inspired)
3. CONTEXT: Any specific demographic or situation mentioned?
4. SEARCH_TERMS: Keywords to search for in stories

Format as JSON.`;

  const response = await callClaude(prompt, apiKey);
  
  try {
    return JSON.parse(response);
  } catch {
    // Fallback parsing
    return {
      theme: extractTheme(message),
      emotion: "curious",
      context: null,
      search_terms: message.toLowerCase().split(' ').filter(w => w.length > 3)
    };
  }
}

async function fetchRelevantStories(intent) {
  const baseUrl = 'https://archive.storycorps.org/wp-json/storycorps/v1/interviews';
  const stories = [];
  
  // Search for stories matching intent
  for (let page = 1; page <= 5; page++) {
    try {
      const response = await fetch(`${baseUrl}?per_page=10&page=${page}`, {
        headers: { 'User-Agent': 'Mosaic/1.0' }
      });
      
      const data = await response.json();
      
      // Filter by intent
      for (const story of data) {
        const keywords = story.keywords?.map(k => k.toLowerCase()) || [];
        const description = story.description?.toLowerCase() || '';
        
        // Check if story matches intent
        const matches = intent.search_terms.some(term => 
          keywords.some(k => k.includes(term)) || 
          description.includes(term)
        );
        
        if (matches) {
          stories.push(story);
        }
      }
      
      // Stop if we have enough
      if (stories.length >= 20) break;
      
    } catch (error) {
      console.error('Fetch error:', error);
    }
  }
  
  return stories;
}

async function analyzeConnections(stories, intent, apiKey) {
  if (stories.length === 0) {
    return {
      unity_score: 0,
      message: "I couldn't find stories matching your query. Try different words?",
      suggestions: ["family challenges", "finding hope", "immigrant journey"]
    };
  }
  
  // Group by demographics
  const byLocation = {};
  stories.forEach(story => {
    const region = story.location?.region?.[0] || 'Unknown';
    if (!byLocation[region]) byLocation[region] = [];
    byLocation[region].push(story);
  });
  
  // Create analysis prompt
  const prompt = `The user expressed: "${intent.theme}" with emotion: "${intent.emotion}"

Analyze these ${stories.length} StoryCorps stories to find human connections:

${Object.entries(byLocation).slice(0, 5).map(([region, regionStories]) => `
${region} (${regionStories.length} stories):
${regionStories.slice(0, 3).map(s => `- ${s.title}: ${s.description?.slice(0, 100)}...`).join('\n')}
`).join('\n')}

Provide:
1. UNITY_SCORE: [0.0-1.0]
2. KEY_INSIGHT: One profound sentence about what connects these people
3. COMMON_THREADS: 3 specific shared experiences
4. SURPRISING_CONNECTION: Something unexpected that unites them
5. STORY_PAIR: IDs of two stories that powerfully show this connection
6. FOLLOW_UP: A question to explore deeper

Be warm, insightful, and conversational.`;

  return await callClaude(prompt, apiKey);
}

function formatResponse(analysis, stories) {
  // Parse Claude's analysis
  const lines = analysis.split('\n');
  let unityScore = 0.7;
  let keyInsight = '';
  let commonThreads = [];
  let followUp = '';
  
  // Extract components (simplified parsing)
  lines.forEach(line => {
    if (line.includes('UNITY_SCORE:')) {
      unityScore = parseFloat(line.split(':')[1]) || 0.7;
    } else if (line.includes('KEY_INSIGHT:')) {
      keyInsight = line.split(':').slice(1).join(':').trim();
    } else if (line.includes('FOLLOW_UP:')) {
      followUp = line.split(':').slice(1).join(':').trim();
    }
  });
  
  // Build conversational response
  const response = {
    message: keyInsight || `I found ${stories.length} stories that connect around this theme.`,
    unityScore,
    storyCount: stories.length,
    locations: [...new Set(stories.map(s => s.location?.region?.[0] || 'Unknown'))],
    preview: stories.slice(0, 3).map(s => ({
      id: s.id,
      title: s.title,
      location: s.location?.region?.[0] || 'Unknown',
      snippet: s.description?.slice(0, 150) + '...'
    })),
    followUp: followUp || "What aspect of this would you like to explore deeper?",
    fullAnalysis: analysis
  };
  
  return response;
}

async function callClaude(prompt, apiKey) {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json'
    },
    body: JSON.stringify({
      model: 'claude-3-haiku-20240307',
      max_tokens: 500,
      messages: [{ role: 'user', content: prompt }]
    })
  });
  
  const data = await response.json();
  return data.content[0].text;
}

function extractTheme(message) {
  const themes = ['family', 'work', 'love', 'loss', 'hope', 'struggle', 'identity'];
  const msgLower = message.toLowerCase();
  
  for (const theme of themes) {
    if (msgLower.includes(theme)) return theme;
  }
  
  return 'connection';
}

async function cacheResult(query, result) {
  // In production, use Redis or similar
  // For now, just log
  console.log(`Cached query: ${query.slice(0, 50)}...`);
}