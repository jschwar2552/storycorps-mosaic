import React, { useState, useEffect } from 'react';
import './StoryConnection-new.css';

function StoryConnection({ story1, story2, connection }) {
  const [isRevealed, setIsRevealed] = useState(false);

  // Reset reveal state when connection changes
  useEffect(() => {
    setIsRevealed(false);
  }, [story1, story2]);

  return (
    <div className={`story-connection ${isRevealed ? 'revealed' : ''}`}>
      <div className="surface-layer">
        <div className="story-card left">
          <div className="story-header">
            <h3>{story1.name}</h3>
            <span className="location">{story1.location}</span>
          </div>
          <div className="demographics">
            {story1.demographics.map((demo, i) => (
              <div key={i} className="demo-item">{demo}</div>
            ))}
          </div>
          {story1.imageUrl && (
            <img src={story1.imageUrl} alt={story1.name} />
          )}
          <div className="life-details">
            {story1.lifeDetails.map((detail, i) => (
              <p key={i}>{detail}</p>
            ))}
          </div>
        </div>

        <div className="connection-space">
          <div className="connecting-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>

        <div className="story-card right">
          <div className="story-header">
            <h3>{story2.name}</h3>
            <span className="location">{story2.location}</span>
          </div>
          <div className="demographics">
            {story2.demographics.map((demo, i) => (
              <div key={i} className="demo-item">{demo}</div>
            ))}
          </div>
          {story2.imageUrl && (
            <img src={story2.imageUrl} alt={story2.name} />
          )}
          <div className="life-details">
            {story2.lifeDetails.map((detail, i) => (
              <p key={i}>{detail}</p>
            ))}
          </div>
        </div>
      </div>

      <div className={`connection-layer ${isRevealed ? 'visible' : ''}`}>
        <div className="connection-reveal">
          <h2>{connection.sharedExperience}</h2>
          <div className="shared-details">
            {connection.details.map((detail, i) => (
              <p key={i} className="detail-item">{detail}</p>
            ))}
          </div>
          {connection.quote && (
            <div className="connection-quote">
              "{connection.quote}"
            </div>
          )}
          <div className="connection-impact">
            {connection.impact}
          </div>
        </div>
      </div>

      <button 
        className="reveal-button"
        onClick={() => setIsRevealed(!isRevealed)}
      >
        {isRevealed ? 'Show Differences' : 'Reveal Connection'}
      </button>

      <div className="story-links">
        <a 
          href={story1.storyUrl} 
          target="_blank" 
          rel="noopener noreferrer"
          className="story-link"
        >
          Listen to {story1.name}'s Story →
        </a>
        <a 
          href={story2.storyUrl} 
          target="_blank" 
          rel="noopener noreferrer"
          className="story-link"
        >
          Listen to {story2.name}'s Story →
        </a>
      </div>
    </div>
  );
}

export default StoryConnection;