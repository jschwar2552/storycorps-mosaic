#!/bin/bash
# Setup script for testing Mosaic locally

echo "🎭 Setting up Mosaic test environment..."
echo "======================================="

# Create virtual environment
echo "1. Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "2. Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "3. Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please add your ANTHROPIC_API_KEY to .env"
else
    echo "3. .env file already exists ✓"
fi

# Create necessary directories
echo "4. Creating directories..."
mkdir -p data/patterns
mkdir -p data/cache
mkdir -p logs

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Add your ANTHROPIC_API_KEY to .env"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python test_pattern_discovery.py"
echo ""