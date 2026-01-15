#!/bin/bash

# Live Lox - Generate Secure Secrets
# This script generates random secure passwords and keys

echo "=========================================="
echo "Live Lox - Secure Secrets Generator"
echo "=========================================="
echo ""

# Generate database password
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
echo "Database Password:"
echo "  $DB_PASSWORD"
echo ""

# Generate secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "Secret Key:"
echo "  $SECRET_KEY"
echo ""

# Generate Redis password (optional)
REDIS_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
echo "Redis Password (optional):"
echo "  $REDIS_PASSWORD"
echo ""

echo "=========================================="
echo "⚠️  IMPORTANT: Save these securely!"
echo "=========================================="
echo ""
echo "Update these values in /opt/livelox/.env:"
echo ""
echo "DB_PASSWORD=$DB_PASSWORD"
echo "SECRET_KEY=$SECRET_KEY"
echo ""
echo "Also update PostgreSQL password:"
echo "  sudo -u postgres psql -c \"ALTER USER livelox WITH PASSWORD '$DB_PASSWORD';\""
echo ""
