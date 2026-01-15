#!/bin/bash
set -e

# Live Lox - Nginx Setup Script
# Run as root: sudo bash setup_nginx.sh

echo "=========================================="
echo "Live Lox Nginx Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Please run as root (use: sudo bash setup_nginx.sh)"
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
NGINX_CONFIG="$SCRIPT_DIR/../nginx/livelox.conf"

# Prompt for domain name
echo "📝 Domain Configuration"
echo ""
read -p "Enter your domain name (e.g., api.livelox.com): " DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
    echo "ERROR: Domain name is required"
    exit 1
fi

# Create temporary config with domain name
TEMP_CONFIG="/tmp/livelox-nginx.conf"
sed "s/yourdomain.com/$DOMAIN_NAME/g" $NGINX_CONFIG > $TEMP_CONFIG

# Copy nginx configuration
echo "📋 Installing Nginx configuration..."
cp $TEMP_CONFIG /etc/nginx/sites-available/livelox
rm $TEMP_CONFIG

# Create symlink to enable site
if [ ! -L /etc/nginx/sites-enabled/livelox ]; then
    ln -s /etc/nginx/sites-available/livelox /etc/nginx/sites-enabled/
fi

# Remove default nginx site
if [ -L /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Create directory for Let's Encrypt challenges
mkdir -p /var/www/certbot

# Test nginx configuration
echo "🧪 Testing Nginx configuration..."
nginx -t

# Reload nginx
echo "🔄 Reloading Nginx..."
systemctl reload nginx

echo ""
echo "=========================================="
echo "SSL Certificate Setup"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: Make sure your domain $DOMAIN_NAME points to this server's IP address!"
echo ""
read -p "Is your domain already pointing to this server? (y/n): " DNS_READY

if [ "$DNS_READY" = "y" ] || [ "$DNS_READY" = "Y" ]; then
    echo ""
    echo "🔐 Obtaining SSL certificate..."
    certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME --redirect
    
    echo ""
    echo "✅ SSL certificate obtained successfully!"
    
    # Set up auto-renewal
    echo "🔄 Setting up automatic certificate renewal..."
    systemctl enable certbot.timer
    systemctl start certbot.timer
else
    echo ""
    echo "⚠️  Please configure your DNS first:"
    echo "   1. Go to your domain registrar"
    echo "   2. Add an A record pointing $DOMAIN_NAME to this server's IP"
    echo "   3. Wait for DNS propagation (can take up to 48 hours)"
    echo "   4. Run this command to get SSL certificate:"
    echo "      sudo certbot --nginx -d $DOMAIN_NAME"
fi

echo ""
echo "=========================================="
echo "✅ Nginx setup complete!"
echo "=========================================="
echo ""
echo "Your API is now available at:"
if [ "$DNS_READY" = "y" ] || [ "$DNS_READY" = "Y" ]; then
    echo "  https://$DOMAIN_NAME"
else
    echo "  http://$DOMAIN_NAME (HTTP only until SSL is configured)"
fi
echo ""
echo "Useful commands:"
echo "  - Test Nginx config:  sudo nginx -t"
echo "  - Reload Nginx:       sudo systemctl reload nginx"
echo "  - View Nginx logs:    sudo tail -f /var/log/nginx/livelox-error.log"
echo "  - Renew SSL cert:     sudo certbot renew"
echo ""
