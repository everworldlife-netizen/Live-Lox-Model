#!/bin/bash
set -e

# Live Lox - Systemd Services Setup Script
# Run as root: sudo bash setup_services.sh

echo "=========================================="
echo "Live Lox Services Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Please run as root (use: sudo bash setup_services.sh)"
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEMD_DIR="$SCRIPT_DIR/../systemd"

# Create log directory
echo "📁 Creating log directory..."
mkdir -p /var/log/livelox
chown livelox:livelox /var/log/livelox

# Copy systemd service files
echo "📋 Installing systemd service files..."
cp $SYSTEMD_DIR/livelox-api.service /etc/systemd/system/
cp $SYSTEMD_DIR/livelox-news-worker.service /etc/systemd/system/

# Reload systemd
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# Enable services
echo "✅ Enabling services..."
systemctl enable livelox-api.service
systemctl enable livelox-news-worker.service

# Start services
echo "🚀 Starting services..."
systemctl start livelox-api.service
systemctl start livelox-news-worker.service

# Check status
echo ""
echo "=========================================="
echo "Service Status"
echo "=========================================="
echo ""
echo "FastAPI Service:"
systemctl status livelox-api.service --no-pager || true
echo ""
echo "News Worker Service:"
systemctl status livelox-news-worker.service --no-pager || true

echo ""
echo "=========================================="
echo "✅ Services setup complete!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  - Check API status:    sudo systemctl status livelox-api"
echo "  - Check worker status: sudo systemctl status livelox-news-worker"
echo "  - View API logs:       sudo journalctl -u livelox-api -f"
echo "  - View worker logs:    sudo journalctl -u livelox-news-worker -f"
echo "  - Restart API:         sudo systemctl restart livelox-api"
echo "  - Restart worker:      sudo systemctl restart livelox-news-worker"
echo ""
