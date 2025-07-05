import React, { useState } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      text: "Hi! I'm Mosaic. I help discover human connections across different backgrounds. What are you curious about?",
      suggestions: ["Tell me about family struggles", "How do people find hope?", "Show me immigrant stories"]
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
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      // Add bot response
      setMessages(prev => [...prev, {
        type: 'bot',
        text: data.response.message,
        unityScore: data.response.unityScore,
        stories: data.response.preview,
        followUp: data.response.followUp,
        locations: data.response.locations
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
                
                {msg.stories && (
                  <div className="story-previews">
                    {msg.stories.map((story, i) => (
                      <div key={i} className="story-preview">
                        <h4>{story.title}</h4>
                        <span className="location">{story.location}</span>
                        <p>{story.snippet}</p>
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
            placeholder="Ask about human connections..."
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

export default App;