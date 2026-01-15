#!/bin/bash
set -e

# Live Lox - Application Deployment Script
# Run as livelox user: bash deploy_app.sh

echo "=========================================="
echo "Live Lox Application Deployment"
echo "=========================================="
echo ""

APP_DIR="/opt/livelox"
REPO_URL="https://github.com/everworldlife-netizen/Live-Lox-Model.git"

# Check if running as livelox user
if [ "$USER" != "livelox" ]; then
    echo "⚠️  This script should be run as 'livelox' user"
    echo "Switching to livelox user..."
    sudo -u livelox bash "$0"
    exit $?
fi

cd $APP_DIR

# Clone or update repository
if [ ! -d "$APP_DIR/Live-Lox-Model" ]; then
    echo "📥 Cloning repository..."
    git clone $REPO_URL
    cd Live-Lox-Model
else
    echo "📥 Updating repository..."
    cd Live-Lox-Model
    git pull origin main
fi

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install application dependencies
echo "📦 Installing application dependencies..."
cd apps/api
pip install -r requirements.txt
pip install -r requirements_news_ingestion.txt

# Install additional production dependencies
pip install uvicorn[standard] gunicorn psycopg2-binary

# Create .env file if it doesn't exist
if [ ! -f "$APP_DIR/.env" ]; then
    echo "📝 Creating .env file..."
    cat > $APP_DIR/.env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://livelox:CHANGE_THIS_PASSWORD@localhost:5432/livelox

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Application Configuration
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000

# News Ingestion Configuration
NEWS_INGESTION_ENABLED=true
NEWS_INGESTION_INTERVAL=300  # 5 minutes

# Security (generate new secret key!)
SECRET_KEY=CHANGE_THIS_TO_RANDOM_STRING

# CORS Origins (add your frontend domain)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
EOF
    echo "⚠️  Created .env file - PLEASE UPDATE THE PASSWORDS AND SECRET KEY!"
fi

# Run database migrations (if you have any)
echo "🗄️  Running database migrations..."
# Uncomment when you have migrations
# python manage.py migrate

# Create database tables for news ingestion
echo "🗄️  Creating database tables..."
psql $DATABASE_URL << 'EOSQL'
CREATE TABLE IF NOT EXISTS player_assumptions (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL,
    game_id VARCHAR(50),
    assumption_type VARCHAR(50) NOT NULL,
    minutes_multiplier FLOAT,
    minutes_cap INTEGER,
    confidence_level VARCHAR(20),
    reason TEXT,
    source VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_player_assumptions_player_id ON player_assumptions(player_id);
CREATE INDEX IF NOT EXISTS idx_player_assumptions_game_id ON player_assumptions(game_id);
CREATE INDEX IF NOT EXISTS idx_player_assumptions_timestamp ON player_assumptions(timestamp);
EOSQL

echo ""
echo "=========================================="
echo "✅ Application deployment complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit $APP_DIR/.env and update passwords"
echo "2. Run: sudo bash deployment/scripts/setup_services.sh"
echo "3. Run: sudo bash deployment/scripts/setup_nginx.sh"
echo ""
