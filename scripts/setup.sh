#!/bin/bash

# SeedVR2 RunPod GUI Setup Script

set -e

echo "🚀 Setting up SeedVR2 RunPod GUI..."

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required but not installed. Aborting." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before running the application"
fi

# Backend setup
echo "🔧 Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate || . venv/Scripts/activate  # Windows compatibility
pip install -r requirements.txt

# Create necessary directories
mkdir -p uploads static logs

# Frontend setup
echo "🎨 Setting up frontend..."
cd ../frontend
npm install

# Build frontend
echo "🏗️  Building frontend..."
npm run build

# Docker setup (optional)
read -p "Do you want to build Docker images? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🐳 Building Docker images..."
    cd ..
    docker-compose build
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run 'docker-compose up' to start all services"
echo "3. Or run services individually:"
echo "   - Backend: cd backend && uvicorn api.main:app --reload"
echo "   - Frontend: cd frontend && npm start"
echo ""
echo "📚 See docs/deployment.md for production deployment instructions"