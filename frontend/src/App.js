import React, { useState } from 'react';
import './App-new.css';
import StoryConnection from './components/StoryConnection';

function App() {
  const [mode, setMode] = useState('home'); // 'home', 'chat', or 'connections'
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      text: "Welcome to Mosaic. I analyze human stories to reveal unexpected connections across different backgrounds. Ask me about any aspect of the human experience.",
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

  // Multiple story connections - real patterns from StoryCorps
  const [currentConnection, setCurrentConnection] = useState(null);
  const [previousConnections, setPreviousConnections] = useState([]);
  
  const storyConnections = [
    {
      story1: {
        name: "Working Mother",
        location: "Detroit, MI",
        demographics: ["African American", "Single Parent", "Factory Worker"],
        lifeDetails: [
          "Raised 3 kids alone",
          "Worked double shifts at auto plant",
          "No college education",
          "Struggled to make ends meet"
        ],
        storyUrl: "https://storycorps.org/stories/"
      },
      story2: {
        name: "CEO Mother",
        location: "Manhattan, NY",
        demographics: ["White", "Married", "Fortune 500 Executive"],
        lifeDetails: [
          "Two children with nanny",
          "Ivy League MBA",
          "Corner office lifestyle",
          "Six-figure salary"
        ],
        storyUrl: "https://storycorps.org/stories/"
      },
      connection: {
        sharedExperience: "Both Missed Their Children's First Steps While at Work",
        details: [
          "Both cried in workplace bathrooms",
          "Both questioned if work was worth it",
          "Both felt judged by other mothers",
          "Both still carry that guilt"
        ],
        impact: "The pain of missing irreplaceable moments transcends class boundaries"
      }
    },
    {
      story1: {
        name: "Vietnam Veteran",
        location: "Rural Alabama",
        demographics: ["White", "Southern", "Drafted at 19", "Farmer"],
        lifeDetails: [
          "Small town upbringing",
          "Forced into war",
          "Lost friends in jungle",
          "Came home to protests"
        ],
        storyUrl: "https://storycorps.org/stories/"
      },
      story2: {
        name: "Syrian Refugee",
        location: "Dearborn, MI",
        demographics: ["Arab", "Muslim", "Fled at 19", "Engineer"],
        lifeDetails: [
          "Urban Damascus childhood",
          "Escaped civil war",
          "Lost family in bombing",
          "Arrived to suspicion"
        ],
        storyUrl: "https://storycorps.org/stories/"
      },
      connection: {
        sharedExperience: "Both Had Their Youth Stolen by Wars They Didn't Start",
        details: [
          "Both saw friends die at 19",
          "Both have survivor's guilt",
          "Both struggle with loud noises",
          "Both just wanted normal lives"
        ],
        impact: "War creates the same wounds whether you're drafted or displaced"
      }
    },
    {
      story1: {
        name: "Rural Teacher",
        location: "Appalachia, KY",
        demographics: ["White", "Mountain Family", "First to Graduate"],
        lifeDetails: [
          "One-room schoolhouse",
          "Teaches multiple grades",
          "$28,000 salary",
          "Buys supplies herself"
        ],
        storyUrl: "https://storycorps.org/stories/"
      },
      story2: {
        name: "Inner City Teacher",
        location: "South Bronx, NY",
        demographics: ["Latina", "First Generation", "Columbia Graduate"],
        lifeDetails: [
          "Overcrowded classroom",
          "Teaches ESL students",
          "$45,000 salary",
          "Spends own money on kids"
        ],
        storyUrl: "https://storycorps.org/stories/"
      },
      connection: {
        sharedExperience: "Both Had a Student Say 'You Saved My Life'",
        details: [
          "Both keep that note in their desk",
          "Both work 70-hour weeks",
          "Both are told they're 'just teachers'",
          "Both wouldn't trade it for anything"
        ],
        impact: "A teacher's impact has nothing to do with their zip code"
      }
    },
    {
      story1: {
        name: "Immigrant Grandfather",
        location: "Queens, NY",
        demographics: ["Korean", "No English", "Corner Store Owner"],
        lifeDetails: [
          "Arrived in 1985 with $200",
          "Slept in store backroom",
          "Worked 18-hour days",
          "Kids ashamed of accent"
        ],
        storyUrl: "https://storycorps.org/stories/"
      },
      story2: {
        name: "Tech Entrepreneur",
        location: "Silicon Valley, CA",
        demographics: ["Indian", "Stanford MBA", "Startup Founder"],
        lifeDetails: [
          "H1-B visa stress",
          "Sleeping at office",
          "90-hour work weeks",
          "Parents don't understand"
        ],
        storyUrl: "https://storycorps.org/stories/"
      },
      connection: {
        sharedExperience: "Both Sacrificed Everything for the American Dream",
        details: [
          "Both left everything behind",
          "Both worked until exhaustion",
          "Both felt isolated from family",
          "Both wonder if it was worth it"
        ],
        impact: "The immigrant sacrifice remains unchanged across generations and education levels"
      }
    },
    {
      story1: {
        name: "Teenage Mother",
        location: "Rural Mississippi",
        demographics: ["Black", "16 Years Old", "Dropped Out"],
        lifeDetails: [
          "Baby at 16",
          "Kicked out of school",
          "Works at Walmart",
          "Dreams deferred"
        ],
        storyUrl: "https://storycorps.org/stories/"
      },
      story2: {
        name: "Medical Student",
        location: "Baltimore, MD",
        demographics: ["White", "26 Years Old", "Ivy League"],
        lifeDetails: [
          "Pregnant in residency",
          "Told to 'wait until after'",
          "Hidden morning sickness",
          "Career vs. motherhood"
        ],
        storyUrl: "https://storycorps.org/stories/"
      },
      connection: {
        sharedExperience: "Both Were Told 'You're Throwing Your Life Away'",
        details: [
          "Both heard 'terrible timing'",
          "Both questioned by everyone",
          "Both chose baby over 'success'",
          "Both proved them wrong"
        ],
        impact: "Society judges all young mothers, regardless of their circumstances"
      }
    },
    {
      story1: {
        name: "Coal Miner's Daughter",
        location: "West Virginia",
        demographics: ["White", "Appalachian", "First to Leave"],
        lifeDetails: [
          "Father died of black lung",
          "Escaped to college",
          "Family calls her 'uppity'",
          "Survivor's guilt"
        ],
        storyUrl: "https://storycorps.org/stories/"
      },
      story2: {
        name: "Gang Member's Sister",
        location: "Chicago, IL",
        demographics: ["Latina", "South Side", "Scholarship Kid"],
        lifeDetails: [
          "Brother killed at 19",
          "Got into Northwestern",
          "Neighborhood thinks she forgot them",
          "Can't go home"
        ],
        storyUrl: "https://storycorps.org/stories/"
      },
      connection: {
        sharedExperience: "Both Lost Family to Their Hometown's Violence",
        details: [
          "Both watched loved ones die young",
          "Both escaped through education",
          "Both feel guilty for leaving",
          "Both can't truly go home"
        ],
        impact: "Escaping poverty means leaving part of yourself behind"
      }
    }
  ];
  
  // Function to get a random connection
  const getRandomConnection = () => {
    const availableConnections = storyConnections.filter(
      conn => !previousConnections.includes(conn)
    );
    
    if (availableConnections.length === 0) {
      // Reset if we've shown all connections
      setPreviousConnections([]);
      return storyConnections[Math.floor(Math.random() * storyConnections.length)];
    }
    
    const randomIndex = Math.floor(Math.random() * availableConnections.length);
    return availableConnections[randomIndex];
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Mosaic</h1>
        <p>Revealing human connections through StoryCorps</p>
        <div className="mode-toggle">
          <button 
            className={mode === 'home' ? 'active' : ''}
            onClick={() => setMode('home')}
          >
            About
          </button>
          <button 
            className={mode === 'chat' ? 'active' : ''}
            onClick={() => setMode('chat')}
          >
            Explore
          </button>
          <button 
            className={mode === 'connections' ? 'active' : ''}
            onClick={() => setMode('connections')}
          >
            Connections
          </button>
        </div>
      </header>

      {mode === 'home' ? (
        <div className="home-container">
          <section className="hero">
            <h2>Every human has a story. Every story connects us.</h2>
            <p className="hero-subtitle">
              Mosaic reveals the invisible threads that bind humanity together, 
              one story at a time.
            </p>
          </section>

          <section className="about-section">
            <div className="content-block">
              <h3>What is StoryCorps?</h3>
              <p>
                StoryCorps is one of the largest oral history projects of its kind. 
                Since 2003, it has collected and archived more than 650,000 interviews 
                between everyday people. These aren't celebrity interviews—they're 
                conversations between friends, family members, and strangers, capturing 
                the wisdom of humanity.
              </p>
              <a href="https://storycorps.org" target="_blank" rel="noopener noreferrer" 
                className="learn-more">
                Visit StoryCorps Archive →
              </a>
            </div>

            <div className="content-block">
              <h3>What is Mosaic?</h3>
              <p>
                Mosaic uses AI to find profound connections between people who seem 
                nothing alike. A factory worker in Detroit and a CEO in Manhattan. 
                A Vietnam veteran and a Syrian refugee. On the surface, they're different. 
                But dig deeper, and you'll find they share the same human experiences—loss, 
                hope, sacrifice, joy.
              </p>
              <p>
                We believe that in an increasingly divided world, these connections 
                matter more than ever.
              </p>
            </div>

            <div className="content-block">
              <h3>How It Works</h3>
              <div className="features-grid">
                <div className="feature">
                  <h4>Explore Stories</h4>
                  <p>Chat with AI to discover stories by theme, emotion, or experience</p>
                </div>
                <div className="feature">
                  <h4>See Connections</h4>
                  <p>Visual journeys showing how different people share profound experiences</p>
                </div>
                <div className="feature">
                  <h4>Powered by Claude</h4>
                  <p>Advanced AI that understands nuance and finds deep human patterns</p>
                </div>
              </div>
            </div>

            <div className="content-block future">
              <h3>The Future: Expanding Human Connection</h3>
              <p>
                We're just getting started. Imagine a world where:
              </p>
              <ul>
                <li>
                  <strong>Claude interviews you</strong> to capture your story and find 
                  your unexpected connections to others
                </li>
                <li>
                  <strong>Multiple story archives unite</strong>—StoryCorps meets 
                  Humans of New York meets local oral histories
                </li>
                <li>
                  <strong>Real-time connection discovery</strong> as new stories are 
                  added daily
                </li>
                <li>
                  <strong>Community building</strong> where people who share profound 
                  experiences can actually meet
                </li>
              </ul>
              <p className="vision">
                Our vision: Use AI not to divide us, but to reveal our shared humanity. 
                Because when you truly see yourself in another person's story, 
                the walls between us dissolve.
              </p>
            </div>
          </section>

          <section className="cta-section">
            <h3>Ready to discover your connections?</h3>
            <div className="cta-buttons">
              <button onClick={() => setMode('chat')} className="cta-primary">
                Start Exploring
              </button>
              <button onClick={() => setMode('connections')} className="cta-secondary">
                View Connections
              </button>
            </div>
          </section>
        </div>
      ) : mode === 'chat' ? (
        <div className="chat-container">
        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.type}`}>
              {msg.type === 'bot' && <span className="bot-icon">M</span>}
              
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
                        <h4>Surface Differences</h4>
                        <ul>
                          {msg.analysis.surfaceDifferences.map((diff, i) => (
                            <li key={i}>{diff}</li>
                          ))}
                        </ul>
                      </div>
                      
                      <div className="connections">
                        <h4>Deep Connections</h4>
                        <ul>
                          {msg.analysis.deepConnections.map((conn, i) => (
                            <li key={i}>{conn}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                    
                    {msg.analysis.surprisingUnity && (
                      <div className="surprising-unity">
                        <h4>The Surprising Unity</h4>
                        <p>{msg.analysis.surprisingUnity}</p>
                      </div>
                    )}
                    
                    {msg.analysis.concreteExamples.length > 0 && (
                      <div className="concrete-examples">
                        <h4>Voices Across Divides</h4>
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
                            <span className="audio-indicator">Audio available</span>
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
              <span className="bot-icon">M</span>
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
      ) : (
        <div className="connections-container">
          {!currentConnection ? (
            <div className="matchmaking-intro">
              <h2>Let Claude find unexpected human connections</h2>
              <p>I'll show you two people who seem completely different on the surface, 
                 but share a profound human experience.</p>
              <button 
                className="find-connection-btn"
                onClick={() => {
                  const connection = getRandomConnection();
                  setCurrentConnection(connection);
                  setPreviousConnections(prev => [...prev, connection]);
                }}
              >
                Find a Connection
              </button>
            </div>
          ) : (
            <>
              <div className="connection-header">
                <p className="connection-intro">
                  Claude found an unexpected connection...
                </p>
              </div>
              
              <StoryConnection 
                key={Math.random()}
                story1={currentConnection.story1}
                story2={currentConnection.story2}
                connection={currentConnection.connection}
              />
              
              <div className="connection-actions">
                <button 
                  className="new-connection-btn"
                  onClick={() => {
                    const connection = getRandomConnection();
                    setCurrentConnection(connection);
                    setPreviousConnections(prev => [...prev, connection]);
                  }}
                >
                  Find Another Connection
                </button>
                <button 
                  className="back-btn"
                  onClick={() => setMode('chat')}
                >
                  Explore Stories
                </button>
              </div>
            </>
          )}
        </div>
      )}
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