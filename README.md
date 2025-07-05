# 🎭 Mosaic: Finding Human Unity Through Stories

An AI-powered conversational interface that discovers deep human connections across different backgrounds using StoryCorps stories and Claude.

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

## Project Structure
```
storycorps-mosaic/
├── backend/           # Python data collection & analysis
├── frontend/          # React dashboard (GitHub Pages)
├── data/             # Sample data for demo
├── docs/             # Documentation
└── scripts/          # Build and deployment scripts
```

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- StoryCorps API access (see [docs/api-access.md](docs/api-access.md))

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/storycorps-mosaic
cd storycorps-mosaic

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### Development
```bash
# Run backend API
cd backend
python -m uvicorn main:app --reload

# Run frontend dev server
cd frontend
npm start
```

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License
MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments
- StoryCorps for providing access to their incredible archive
- Contributors and testers from around the world