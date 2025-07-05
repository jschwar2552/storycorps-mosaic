# Mosaic: Finding Human Unity Through Stories

A data visualization project that discovers and displays common themes across diverse human experiences using the StoryCorps archive.

## Live Demo
[View Dashboard](#) (Coming soon)

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