/**
 * Vercel Serverless Function for Mosaic Conversational UI
 * Handles chat-like queries about human connections
 */

export default async function handler(req, res) {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
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
  // For now, skip Claude for intent parsing to save API calls and time
  // Just use direct keyword extraction
  const msgLower = message.toLowerCase();
  
  // Extract meaningful words (skip common words)
  const stopWords = ['the', 'about', 'tell', 'me', 'show', 'find', 'with', 'and', 'or', 'for', 'how', 'what', 'when', 'where', 'who'];
  const words = msgLower.split(' ').filter(w => w.length > 2 && !stopWords.includes(w));
  
  return {
    theme: extractTheme(message),
    emotion: "curious",
    context: null,
    search_terms: words.length > 0 ? words : ['family', 'life', 'story']
  };
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
        
        // Check if story matches intent - more flexible matching
        const matches = intent.search_terms.some(term => {
          // Split compound search terms into individual words
          const termWords = term.toLowerCase().split(' ');
          return termWords.some(word => 
            keywords.some(k => k.toLowerCase().includes(word)) || 
            description.toLowerCase().includes(word)
          );
        });
        
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
  
  // Create analysis prompt for finding unity across differences
  const prompt = `Find the hidden connections between these ${stories.length} StoryCorps interviews about "${intent.theme}":

${stories.slice(0, 5).map((s, idx) => `
Story ${idx + 1}: "${s.title}"
Location: ${s.location?.region?.[0] || 'Unknown'}
Keywords: ${s.keywords?.slice(0, 5).join(', ') || 'None'}
Description: ${s.description?.slice(0, 200)}...
`).join('\n---\n')}

ANALYZE THE CONTRAST AND CONNECTION:

1. SURFACE_DIFFERENCES: List 3-5 ways these storytellers are different (location, age, background, circumstances)
Example: "A rural farmer in Iowa vs an immigrant in NYC; generation that built America vs generation trying to enter it"

2. DEEP_CONNECTIONS: Find 3 specific things they ALL share despite differences
Example: "Both describe the kitchen table as the heart of family; both use the phrase 'making something from nothing'; both see sacrifice as love"

3. SURPRISING_UNITY: What unexpected thing connects them?
Example: "The Iowa farmer and NYC immigrant both describe America using the metaphor of a 'promise kept to their children'"

4. CONCRETE_EXAMPLES: Pull specific quotes or moments that prove the connection
Example: "Farmer: 'Every harvest, I think of my kids' future' | Immigrant: 'Every paycheck, I save for my children's dreams'"

5. UNITY_SCORE: [0.0-1.0] How strongly connected are these stories?

6. THE_HUMAN_TRUTH: In one profound sentence, what universal human experience emerges?

Format your response to highlight BOTH the differences AND the connections. Show how people who seem nothing alike are actually deeply connected.`;

  return await callClaude(prompt, apiKey);
}

function formatResponse(analysis, stories) {
  // Handle both string and object analysis
  let analysisText = analysis;
  if (typeof analysis === 'object' && analysis !== null) {
    analysisText = analysis.text || analysis.message || JSON.stringify(analysis);
  }
  
  // Parse Claude's structured analysis
  const lines = String(analysisText).split('\n');
  let unityScore = 0.7;
  let humanTruth = '';
  let surfaceDifferences = [];
  let deepConnections = [];
  let surprisingUnity = '';
  let concreteExamples = [];
  
  let currentSection = '';
  
  lines.forEach(line => {
    const trimmed = line.trim();
    
    // Identify sections
    if (trimmed.includes('SURFACE_DIFFERENCES:')) {
      currentSection = 'differences';
    } else if (trimmed.includes('DEEP_CONNECTIONS:')) {
      currentSection = 'connections';
    } else if (trimmed.includes('SURPRISING_UNITY:')) {
      currentSection = 'surprising';
    } else if (trimmed.includes('CONCRETE_EXAMPLES:')) {
      currentSection = 'examples';
    } else if (trimmed.includes('UNITY_SCORE:')) {
      const scoreMatch = line.match(/[\d.]+/);
      if (scoreMatch) unityScore = parseFloat(scoreMatch[0]);
      currentSection = '';
    } else if (trimmed.includes('THE_HUMAN_TRUTH:')) {
      humanTruth = line.split(':').slice(1).join(':').trim();
      currentSection = '';
    } else if (trimmed && !trimmed.startsWith('Example:')) {
      // Add content to appropriate section
      switch(currentSection) {
        case 'differences':
          if (trimmed.match(/^[-•*]/)) surfaceDifferences.push(trimmed.substring(1).trim());
          else if (trimmed && surfaceDifferences.length === 0) surfaceDifferences.push(trimmed);
          break;
        case 'connections':
          if (trimmed.match(/^[-•*]/)) deepConnections.push(trimmed.substring(1).trim());
          else if (trimmed && deepConnections.length === 0) deepConnections.push(trimmed);
          break;
        case 'surprising':
          if (!surprisingUnity) surprisingUnity = trimmed;
          break;
        case 'examples':
          if (trimmed.includes('|') || trimmed.includes(':')) {
            concreteExamples.push(trimmed);
          }
          break;
      }
    }
  });
  
  // Build enhanced response with contrasts and connections
  const response = {
    message: humanTruth || `These ${stories.length} stories reveal deep human connections across different backgrounds.`,
    unityScore,
    storyCount: stories.length,
    locations: [...new Set(stories.map(s => s.location?.region?.[0] || 'Unknown'))],
    
    // NEW: Structured analysis showing differences and connections
    analysis: {
      surfaceDifferences: surfaceDifferences.length > 0 ? surfaceDifferences : [
        `Stories from ${stories.length} different locations`,
        'Various backgrounds and life experiences',
        'Different generations and perspectives'
      ],
      deepConnections: deepConnections.length > 0 ? deepConnections : [
        'Shared human experiences',
        'Common values and hopes',
        'Universal themes of connection'
      ],
      surprisingUnity: surprisingUnity || 'Despite their differences, all share a common thread of human resilience',
      concreteExamples: concreteExamples.length > 0 ? concreteExamples : []
    },
    
    // Story previews with enhanced metadata
    preview: stories.slice(0, 3).map(s => ({
      id: s.id,
      title: s.title,
      location: s.location?.region?.[0] || 'Unknown',
      snippet: s.description?.slice(0, 150) + '...',
      url: s.url || `https://archive.storycorps.org/interviews/${s.id}`,
      audioUrl: s.audio_url,
      participants: s.participants || [],
      keywords: s.keywords?.slice(0, 3) || []
    })),
    
    followUp: "What other human connections would you like to explore?",
    fullAnalysis: analysisText
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
  
  // Handle errors from Claude API
  if (data.error) {
    throw new Error(`Claude API error: ${data.error.message || data.error}`);
  }
  
  // Extract text from response
  if (data.content && data.content[0] && data.content[0].text) {
    return data.content[0].text;
  }
  
  throw new Error('Unexpected Claude API response format');
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