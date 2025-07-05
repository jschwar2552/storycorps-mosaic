import React, { useState } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      text: "Hi! I'm Mosaic. I help discover human connections across different backgrounds. Ask me anything about the human experience - I'll find surprising connections between people who seem nothing alike.",
      suggestions: [
        "Tell me about family struggles",
        "How do people find hope?", 
        "Show me immigrant stories",
        "What connects parents across cultures?",
        "How do people deal with loss?",
        "Stories about finding purpose",
        "How do different generations see America?",
        "What does home mean to people?",
        "Show me stories about resilience"
      ]
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    // Add user message
    setMessages(prev => [...prev, { type: 'user', text }]);
    setInput('');
    setLoading(true);

    try {
      // Call our API
      const apiUrl = process.env.REACT_APP_API_URL || 'https://storycorps-mosaic.vercel.app';
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      // Add bot response with enhanced analysis
      setMessages(prev => [...prev, {
        type: 'bot',
        text: data.response.message,
        unityScore: data.response.unityScore,
        stories: data.response.preview,
        analysis: data.response.analysis,
        followUp: data.response.followUp,
        locations: data.response.locations,
        suggestions: generateFollowUpSuggestions(text)
      }]);

    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'bot',
        text: `Sorry, I encountered an error: ${error.message}`,
        error: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleSuggestion = (suggestion) => {
    sendMessage(suggestion);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎭 Mosaic</h1>
        <p>Discovering human unity through stories</p>
      </header>

      <div className="chat-container">
        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.type}`}>
              {msg.type === 'bot' && <span className="bot-icon">🤖</span>}
              
              <div className="message-content">
                <p>{msg.text}</p>
                
                {msg.unityScore && (
                  <div className="unity-score">
                    <span>Unity Score: </span>
                    <div className="score-bar">
                      <div 
                        className="score-fill" 
                        style={{width: `${msg.unityScore * 100}%`}}
                      />
                    </div>
                    <span>{(msg.unityScore * 100).toFixed(0)}%</span>
                  </div>
                )}
                
                {msg.locations && (
                  <div className="locations">
                    <span>Stories from: </span>
                    {msg.locations.join(', ')}
                  </div>
                )}
                
                {msg.analysis && (
                  <div className="analysis-section">
                    <div className="contrast-connection">
                      <div className="differences">
                        <h4>🌍 Surface Differences</h4>
                        <ul>
                          {msg.analysis.surfaceDifferences.map((diff, i) => (
                            <li key={i}>{diff}</li>
                          ))}
                        </ul>
                      </div>
                      
                      <div className="connections">
                        <h4>💝 Deep Connections</h4>
                        <ul>
                          {msg.analysis.deepConnections.map((conn, i) => (
                            <li key={i}>{conn}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                    
                    {msg.analysis.surprisingUnity && (
                      <div className="surprising-unity">
                        <h4>✨ The Surprising Unity</h4>
                        <p>{msg.analysis.surprisingUnity}</p>
                      </div>
                    )}
                    
                    {msg.analysis.concreteExamples.length > 0 && (
                      <div className="concrete-examples">
                        <h4>💬 Voices Across Divides</h4>
                        {msg.analysis.concreteExamples.map((example, i) => (
                          <p key={i} className="example">{example}</p>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                
                {msg.stories && (
                  <div className="story-previews">
                    {msg.stories.map((story, i) => (
                      <div 
                        key={i} 
                        className="story-preview clickable"
                        onClick={() => window.open(story.url, '_blank')}
                        title="Click to read full story on StoryCorps"
                      >
                        <h4>{story.title}</h4>
                        <div className="story-meta">
                          <span className="location">{story.location}</span>
                          {story.keywords && story.keywords.length > 0 && (
                            <div className="keywords">
                              {story.keywords.map((keyword, idx) => (
                                <span key={idx} className="keyword">{keyword}</span>
                              ))}
                            </div>
                          )}
                        </div>
                        <p>{story.snippet}</p>
                        <div className="story-actions">
                          <span className="read-more">Click to read full story →</span>
                          {story.audioUrl && (
                            <span className="audio-indicator">🎧 Audio available</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {msg.suggestions && (
                  <div className="suggestions">
                    {msg.suggestions.map((sug, i) => (
                      <button 
                        key={i} 
                        onClick={() => handleSuggestion(sug)}
                        className="suggestion-btn"
                      >
                        {sug}
                      </button>
                    ))}
                  </div>
                )}
                
                {msg.followUp && idx === messages.length - 1 && (
                  <p className="follow-up">{msg.followUp}</p>
                )}
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="message bot">
              <span className="bot-icon">🤖</span>
              <div className="loading">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about the human experience..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

// Generate contextual follow-up suggestions
function generateFollowUpSuggestions(query) {
  const theme = query.toLowerCase();
  const basePrompts = [
    "Dig deeper into this theme",
    "Show me more contrasts",
    "Find surprising connections"
  ];
  
  // Add theme-specific prompts
  if (theme.includes('family') || theme.includes('parent')) {
    return [...basePrompts, "How do chosen families form?", "What bonds non-blood families?", "Show me single parent stories"];
  } else if (theme.includes('hope') || theme.includes('resilience')) {
    return [...basePrompts, "Where do people find strength?", "Stories of rebuilding", "Unexpected sources of hope"];
  } else if (theme.includes('immigrant') || theme.includes('america')) {
    return [...basePrompts, "What does home mean?", "First vs second generation", "Dreams across borders"];
  } else if (theme.includes('loss') || theme.includes('grief')) {
    return [...basePrompts, "How people honor memory", "Finding joy after loss", "Rituals of remembrance"];
  } else if (theme.includes('love') || theme.includes('relationship')) {
    return [...basePrompts, "Love across generations", "Unconventional love stories", "How love survives hardship"];
  } else if (theme.includes('work') || theme.includes('purpose')) {
    return [...basePrompts, "Finding meaning in work", "Career vs calling", "Work across generations"];
  } else {
    return [
      "Show me another angle",
      "Find deeper connections", 
      "Explore related themes",
      "Compare different regions",
      "Show generational differences"
    ];
  }
}

export default App;