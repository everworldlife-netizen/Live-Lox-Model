# Live Lox - DigitalOcean Deployment Guide

Complete guide to deploy Live Lox on a DigitalOcean $6/month Droplet.

---

## Prerequisites

Before you begin, you need:

1. **DigitalOcean Account** - Sign up at https://www.digitalocean.com
2. **Domain Name** (optional but recommended) - For SSL certificate
3. **SSH Key** - For secure server access

---

## Step 1: Create a DigitalOcean Droplet

### 1.1 Sign Up and Create Droplet

1. Go to https://www.digitalocean.com and sign up
2. Click "Create" → "Droplets"
3. Choose configuration:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic ($6/month)
     - 1 GB RAM / 1 vCPU
     - 25 GB SSD
     - 1 TB transfer
   - **Datacenter:** Choose closest to your users
   - **Authentication:** SSH Key (recommended) or Password
   - **Hostname:** livelox-prod

4. Click "Create Droplet"
5. Wait 1-2 minutes for droplet to be created
6. Note the IP address (e.g., 123.45.67.89)

### 1.2 Connect to Your Droplet

```bash
ssh root@YOUR_DROPLET_IP
```

---

## Step 2: Run Server Setup Script

Once connected to your droplet, run the automated setup:

```bash
# Download the repository
cd /tmp
git clone https://github.com/everworldlife-netizen/Live-Lox-Model.git
cd Live-Lox-Model/deployment/scripts

# Run server setup (installs PostgreSQL, Redis, Python, etc.)
sudo bash setup_server.sh
```

**This script will:**
- ✅ Update system packages
- ✅ Install PostgreSQL 15
- ✅ Install Redis
- ✅ Install Python 3.11
- ✅ Install Nginx
- ✅ Install Java (for nbainjuries package)
- ✅ Configure firewall
- ✅ Create 'livelox' user
- ✅ Create PostgreSQL database

**Time:** ~5-10 minutes

---

## Step 3: Generate Secure Passwords

```bash
cd /tmp/Live-Lox-Model/deployment/scripts
bash generate_secrets.sh
```

**Save the output!** You'll need these passwords in the next step.

Example output:
```
Database Password: xK9mP2nQ7vL4wR8tY3hJ6fG1sD5aZ0cV
Secret Key: AbCdEfGhIjKlMnOpQrStUvWxYz123456
```

Update PostgreSQL password:
```bash
sudo -u postgres psql -c "ALTER USER livelox WITH PASSWORD 'YOUR_DB_PASSWORD_FROM_ABOVE';"
```

---

## Step 4: Deploy Application

```bash
# Switch to livelox user
sudo su - livelox

# Clone repository to /opt/livelox
cd /opt/livelox
git clone https://github.com/everworldlife-netizen/Live-Lox-Model.git
cd Live-Lox-Model/deployment/scripts

# Run deployment script
bash deploy_app.sh
```

**This script will:**
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Create .env configuration file
- ✅ Set up database tables

**Time:** ~3-5 minutes

---

## Step 5: Configure Environment Variables

```bash
# Edit the .env file
nano /opt/livelox/.env
```

**Update these values:**

```bash
# Use the passwords from Step 3
DATABASE_URL=postgresql://livelox:YOUR_DB_PASSWORD@localhost:5432/livelox
DB_PASSWORD=YOUR_DB_PASSWORD
SECRET_KEY=YOUR_SECRET_KEY

# Add your domain (if you have one)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

---

## Step 6: Set Up Services

```bash
# Exit from livelox user back to root
exit

# Run services setup
cd /tmp/Live-Lox-Model/deployment/scripts
sudo bash setup_services.sh
```

**This script will:**
- ✅ Create systemd services for FastAPI and news worker
- ✅ Enable auto-start on boot
- ✅ Start the services

**Check if services are running:**
```bash
sudo systemctl status livelox-api
sudo systemctl status livelox-news-worker
```

You should see "active (running)" in green.

---

## Step 7: Set Up Nginx and SSL

### 7.1 Configure Domain (if you have one)

**Before running this step:**
1. Go to your domain registrar (GoDaddy, Namecheap, etc.)
2. Add an A record:
   - **Type:** A
   - **Name:** @ (or api, or whatever subdomain)
   - **Value:** YOUR_DROPLET_IP
   - **TTL:** 3600
3. Wait 5-30 minutes for DNS propagation

**Check if DNS is ready:**
```bash
nslookup yourdomain.com
```

### 7.2 Run Nginx Setup

```bash
cd /tmp/Live-Lox-Model/deployment/scripts
sudo bash setup_nginx.sh
```

**Follow the prompts:**
1. Enter your domain name (e.g., api.livelox.com)
2. Confirm if DNS is ready
3. Script will automatically get SSL certificate from Let's Encrypt

**If you don't have a domain:**
- You can still access the API via http://YOUR_DROPLET_IP
- SSL won't be available without a domain

---

## Step 8: Verify Deployment

### 8.1 Check API is Running

```bash
# From your droplet
curl http://localhost:8000/health

# From your computer (replace with your domain or IP)
curl https://yourdomain.com/health
```

**Expected response:**
```json
{"status": "healthy"}
```

### 8.2 Check News Worker is Running

```bash
sudo journalctl -u livelox-news-worker -f
```

You should see logs showing RSS feeds being polled.

### 8.3 Check Database

```bash
sudo -u postgres psql -d livelox -c "SELECT COUNT(*) FROM player_assumptions;"
```

---

## Step 9: Monitor and Maintain

### Useful Commands

**View Logs:**
```bash
# API logs
sudo journalctl -u livelox-api -f

# News worker logs
sudo journalctl -u livelox-news-worker -f

# Nginx logs
sudo tail -f /var/log/nginx/livelox-error.log
```

**Restart Services:**
```bash
sudo systemctl restart livelox-api
sudo systemctl restart livelox-news-worker
sudo systemctl reload nginx
```

**Update Application:**
```bash
sudo su - livelox
cd /opt/livelox/Live-Lox-Model
git pull origin main
source venv/bin/activate
cd apps/api
pip install -r requirements.txt
exit

sudo systemctl restart livelox-api
sudo systemctl restart livelox-news-worker
```

**Check Server Resources:**
```bash
# CPU and memory usage
htop

# Disk usage
df -h

# Database size
sudo -u postgres psql -d livelox -c "SELECT pg_size_pretty(pg_database_size('livelox'));"
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status livelox-api

# View detailed logs
sudo journalctl -u livelox-api -n 50

# Check if port 8000 is in use
sudo lsof -i :8000
```

### Database Connection Error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -d livelox -c "SELECT 1;"

# Check password in .env matches PostgreSQL
cat /opt/livelox/.env | grep DB_PASSWORD
```

### Nginx 502 Bad Gateway

```bash
# Check if API service is running
sudo systemctl status livelox-api

# Check Nginx configuration
sudo nginx -t

# View Nginx error logs
sudo tail -f /var/log/nginx/livelox-error.log
```

### SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew

# Check certificate status
sudo certbot certificates

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## Security Best Practices

### 1. Change Default SSH Port (Optional)

```bash
sudo nano /etc/ssh/sshd_config
# Change: Port 22 → Port 2222
sudo systemctl restart sshd
sudo ufw allow 2222/tcp
```

### 2. Set Up Automatic Security Updates

```bash
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### 3. Regular Backups

**Database Backup:**
```bash
# Create backup script
sudo nano /opt/livelox/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/livelox/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump livelox > $BACKUP_DIR/livelox_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "livelox_*.sql" -mtime +7 -delete
```

```bash
chmod +x /opt/livelox/backup.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add: 0 2 * * * /opt/livelox/backup.sh
```

---

## Cost Breakdown

| Item | Cost/Month |
|------|------------|
| DigitalOcean Droplet (1GB) | $6.00 |
| Domain Name (optional) | ~$12/year ($1/month) |
| **Total** | **$6-7/month** |

**What's Included:**
- ✅ FastAPI backend (always-on)
- ✅ PostgreSQL database
- ✅ Redis caching
- ✅ News ingestion worker
- ✅ Nginx reverse proxy
- ✅ Free SSL certificate
- ✅ 1 TB bandwidth

---

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. View logs: `sudo journalctl -u livelox-api -f`
3. Check GitHub issues: https://github.com/everworldlife-netizen/Live-Lox-Model/issues

---

## Next Steps

Now that your server is deployed:

1. **Connect your frontend** - Update CORS_ORIGINS in .env
2. **Set up monitoring** - Add Slack/email alerts
3. **Configure backups** - Set up automated database backups
4. **Scale if needed** - Upgrade to bigger droplet when traffic grows

---

**Congratulations! Your Live Lox application is now live! 🎉**
