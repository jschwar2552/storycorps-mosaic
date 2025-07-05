# 🎭 StoryCorps Mosaic: Discovering Human Unity Through Stories

An AI-powered conversational interface that discovers deep human connections across different backgrounds using StoryCorps stories and Claude. By analyzing thousands of personal narratives, Mosaic reveals the profound threads that connect us all, creating a tapestry of shared human experience.

## Experience Mosaic

Ask questions like:
- "How do single parents find strength?"
- "Show me stories about immigrants finding home"
- "What connects people during loss?"

Mosaic will discover patterns of unity across different demographics in real-time.

## Overview
Mosaic analyzes thousands of personal stories to find surprising connections between people of different backgrounds, revealing the themes that unite us across geography, age, culture, and beliefs.

## Features
- 🌍 Cross-demographic theme analysis
- 📊 Interactive data visualizations
- 🔍 Pattern discovery across 500,000+ stories
- 🤝 Unity metrics showing common ground

## Architecture

Mosaic uses a modern, scalable architecture designed for performance and reliability:

- **Frontend**: React application hosted on GitHub Pages for fast, global access
- **Backend API**: Vercel serverless functions for scalable, on-demand processing
- **AI Integration**: Claude API for intelligent pattern discovery and analysis
- **Data Pipeline**: Python-based analysis engine for story processing

## Project Structure
```
storycorps-mosaic/
├── frontend/          # React application (GitHub Pages)
│   ├── src/          # React components and application logic
│   └── public/       # Static assets and index.html
├── backend/          # Python analysis engine
│   ├── src/          # Core pattern discovery algorithms
│   └── tests/        # Test suite
├── api/              # Vercel serverless functions
│   └── chat.js       # AI-powered chat endpoint
├── data/             # Sample data for development
└── docs/             # Documentation
```

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Git
- API Keys:
  - Anthropic API key for Claude
  - StoryCorps API access (optional for full functionality)

### Installation
```bash
# Clone repository
git clone https://github.com/jschwar2552/storycorps-mosaic.git
cd storycorps-mosaic

# Install backend dependencies
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install

# Install root dependencies (for Vercel)
cd ..
npm install
```

### Configuration

1. **Backend configuration** (`backend/.env`):
   ```
   ANTHROPIC_API_KEY=your_anthropic_key
   STORYCORPS_API_KEY=your_storycorps_key
   ```

2. **Vercel configuration** (`.env`):
   ```
   ANTHROPIC_API_KEY=your_anthropic_key
   ```

### Development
```bash
# Run frontend development server
cd frontend
npm start
# Available at http://localhost:3000

# Test backend locally
cd backend
python -m src.pattern_discovery

# Run tests
cd backend
python -m pytest
```

## Deployment

### Frontend Deployment (GitHub Pages)

The frontend automatically deploys to GitHub Pages via GitHub Actions when you push to the `main` branch:

1. Push changes to main branch
2. GitHub Actions builds the React app
3. Deploys to `gh-pages` branch
4. Available at: `https://jschwar2552.github.io/storycorps-mosaic/`

### Backend API Deployment (Vercel)

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy to Vercel**:
   ```bash
   vercel --prod
   ```

3. **Configure environment variables** in Vercel dashboard:
   - `ANTHROPIC_API_KEY`
   - Any other required API keys

The API will be available at: `https://storycorps-mosaic.vercel.app/api`

## API Documentation

### Chat API

**Endpoint:** `POST /api/chat`

Discover patterns and connections across StoryCorps stories using AI.

**Request:**
```json
{
  "message": "How do single parents find strength?"
}
```

**Response:**
```json
{
  "response": "Analysis of patterns across stories...",
  "patterns": [
    {
      "theme": "resilience",
      "stories": [...],
      "connections": [...]
    }
  ]
}
```

## Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- StoryCorps for providing access to their incredible archive of human stories
- The open-source community for the amazing tools that make this possible
- All the storytellers who have shared their experiences

---

**Live Demo:** [https://jschwar2552.github.io/storycorps-mosaic/](https://jschwar2552.github.io/storycorps-mosaic/)

**API Endpoint:** [https://storycorps-mosaic.vercel.app/api](https://storycorps-mosaic.vercel.app/api)# Test workflow trigger
