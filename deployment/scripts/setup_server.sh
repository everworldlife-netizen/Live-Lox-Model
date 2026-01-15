#!/bin/bash
set -e

# Live Lox - DigitalOcean Server Setup Script
# This script sets up a complete production environment on Ubuntu 22.04
# Run as root: sudo bash setup_server.sh

echo "=========================================="
echo "Live Lox Server Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Please run as root (use: sudo bash setup_server.sh)"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt-get update -y
apt-get upgrade -y

# Install essential packages
echo "📦 Installing essential packages..."
apt-get install -y \
    build-essential \
    curl \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    software-properties-common \
    gnupg \
    lsb-release \
    ca-certificates \
    apt-transport-https \
    ufw \
    fail2ban \
    unzip \
    wget

# Install PostgreSQL 15
echo "🐘 Installing PostgreSQL 15..."
sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt-get update -y
apt-get install -y postgresql-15 postgresql-contrib-15

# Install Redis
echo "📮 Installing Redis..."
apt-get install -y redis-server

# Configure Redis
echo "📮 Configuring Redis..."
sed -i 's/supervised no/supervised systemd/' /etc/redis/redis.conf
systemctl restart redis-server
systemctl enable redis-server

# Install Python 3.11
echo "🐍 Installing Python 3.11..."
add-apt-repository ppa:deadsnakes/ppa -y
apt-get update -y
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip

# Install Java (required for nbainjuries package)
echo "☕ Installing Java..."
apt-get install -y default-jre default-jdk

# Set up firewall
echo "🔥 Configuring firewall..."
ufw --force enable
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw status

# Configure fail2ban
echo "🛡️ Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Create application user
echo "👤 Creating application user..."
if ! id -u livelox > /dev/null 2>&1; then
    useradd -m -s /bin/bash livelox
    echo "User 'livelox' created"
else
    echo "User 'livelox' already exists"
fi

# Create application directory
echo "📁 Creating application directory..."
mkdir -p /opt/livelox
chown livelox:livelox /opt/livelox

# Set up PostgreSQL database
echo "🐘 Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE USER livelox WITH PASSWORD 'CHANGE_THIS_PASSWORD';" || echo "User already exists"
sudo -u postgres psql -c "CREATE DATABASE livelox OWNER livelox;" || echo "Database already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE livelox TO livelox;"

# Configure PostgreSQL for local connections
echo "🐘 Configuring PostgreSQL..."
PG_HBA="/etc/postgresql/15/main/pg_hba.conf"
if ! grep -q "livelox" $PG_HBA; then
    echo "host    livelox         livelox         127.0.0.1/32            md5" >> $PG_HBA
    systemctl restart postgresql
fi

# Install pip packages globally
echo "🐍 Installing Python packages..."
pip3 install --upgrade pip
pip3 install virtualenv

echo ""
echo "=========================================="
echo "✅ Server setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Change PostgreSQL password in /opt/livelox/.env"
echo "2. Clone your repository to /opt/livelox"
echo "3. Run deployment/scripts/deploy_app.sh"
echo ""
echo "PostgreSQL Info:"
echo "  - Database: livelox"
echo "  - User: livelox"
echo "  - Password: CHANGE_THIS_PASSWORD (⚠️  CHANGE THIS!)"
echo "  - Host: localhost"
echo "  - Port: 5432"
echo ""
echo "Redis Info:"
echo "  - Host: localhost"
echo "  - Port: 6379"
echo ""
