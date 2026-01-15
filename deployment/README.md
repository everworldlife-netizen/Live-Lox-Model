# Live Lox - Deployment Files

This directory contains all files needed to deploy Live Lox on a DigitalOcean $6/month Droplet.

## 📁 Directory Structure

```
deployment/
├── scripts/           # Automated setup scripts
│   ├── setup_server.sh        # Initial server setup
│   ├── deploy_app.sh          # Application deployment
│   ├── setup_services.sh      # Systemd services setup
│   ├── setup_nginx.sh         # Nginx and SSL setup
│   └── generate_secrets.sh    # Generate secure passwords
├── systemd/           # Systemd service files
│   ├── livelox-api.service
│   └── livelox-news-worker.service
├── nginx/             # Nginx configuration
│   └── livelox.conf
├── config/            # Configuration templates
│   └── .env.example
├── DEPLOYMENT_GUIDE.md    # Complete deployment guide
└── README.md          # This file
```

## 🚀 Quick Start

### Complete Deployment (5 steps)

```bash
# 1. Create DigitalOcean Droplet (Ubuntu 22.04, $6/month)
# 2. SSH into droplet
ssh root@YOUR_DROPLET_IP

# 3. Clone repo and run server setup
git clone https://github.com/everworldlife-netizen/Live-Lox-Model.git
cd Live-Lox-Model/deployment/scripts
sudo bash setup_server.sh

# 4. Generate passwords and deploy app
bash generate_secrets.sh  # Save the output!
sudo -u livelox bash deploy_app.sh

# 5. Set up services and nginx
sudo bash setup_services.sh
sudo bash setup_nginx.sh
```

**Total time:** ~15-20 minutes

## 📖 Documentation

For detailed step-by-step instructions, see [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

## 🛠️ Scripts Overview

### setup_server.sh
Sets up the server with all required software:
- PostgreSQL 15
- Redis
- Python 3.11
- Nginx
- Java (for nbainjuries)
- Firewall configuration

**Run once** during initial setup.

### deploy_app.sh
Deploys the application:
- Clones/updates repository
- Creates Python virtual environment
- Installs dependencies
- Creates database tables
- Generates .env file

**Run** during initial setup and when updating the app.

### setup_services.sh
Configures systemd services:
- FastAPI backend service
- News ingestion worker service
- Auto-start on boot
- Auto-restart on failure

**Run once** after deploying the app.

### setup_nginx.sh
Sets up Nginx reverse proxy:
- Configures Nginx
- Obtains SSL certificate (Let's Encrypt)
- Sets up HTTPS redirect
- Configures auto-renewal

**Run once** after services are running.

### generate_secrets.sh
Generates secure random passwords:
- Database password
- Secret key
- Redis password (optional)

**Run once** and save the output securely.

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `/opt/livelox/.env` and update:

```bash
DATABASE_URL=postgresql://livelox:YOUR_PASSWORD@localhost:5432/livelox
SECRET_KEY=YOUR_SECRET_KEY
CORS_ORIGINS=https://yourdomain.com
```

### Systemd Services

Services are located in `/etc/systemd/system/`:
- `livelox-api.service` - FastAPI backend
- `livelox-news-worker.service` - News ingestion worker

### Nginx Configuration

Nginx config is located at `/etc/nginx/sites-available/livelox`

## 📊 Monitoring

### View Logs

```bash
# API logs
sudo journalctl -u livelox-api -f

# News worker logs
sudo journalctl -u livelox-news-worker -f

# Nginx logs
sudo tail -f /var/log/nginx/livelox-error.log
```

### Check Status

```bash
# Services
sudo systemctl status livelox-api
sudo systemctl status livelox-news-worker

# Nginx
sudo systemctl status nginx

# Database
sudo systemctl status postgresql
```

## 🔄 Updating the Application

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

## 💰 Cost

**Total: $6/month**
- DigitalOcean Droplet: $6/month
- Everything else: FREE (PostgreSQL, Redis, Nginx, SSL)

## 🆘 Troubleshooting

### Service won't start
```bash
sudo systemctl status livelox-api
sudo journalctl -u livelox-api -n 50
```

### Database connection error
```bash
sudo systemctl status postgresql
sudo -u postgres psql -d livelox -c "SELECT 1;"
```

### Nginx 502 error
```bash
sudo systemctl status livelox-api
sudo nginx -t
sudo tail -f /var/log/nginx/livelox-error.log
```

## 📚 Additional Resources

- [Full Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [News Ingestion Service](../apps/api/app/services/news_ingestion/README.md)
- [GitHub Repository](https://github.com/everworldlife-netizen/Live-Lox-Model)

## 🎯 What's Deployed

After successful deployment, you'll have:

✅ FastAPI backend running on port 8000  
✅ PostgreSQL database with player_assumptions table  
✅ Redis caching server  
✅ News ingestion worker polling RSS feeds every 5 minutes  
✅ Nginx reverse proxy with SSL certificate  
✅ Systemd services with auto-restart  
✅ Firewall configured (ports 22, 80, 443)  

**Your API will be accessible at:**
- https://yourdomain.com (if you configured a domain)
- http://YOUR_DROPLET_IP (without domain)

---

**Ready to deploy? Start with [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)!**
