#!/bin/bash
#=============================================================================
# Control Center X Ultra - Enterprise Discord Ticket System
# Automated Installation Script for Debian 12
#=============================================================================
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Control Center X Ultra - Installer    ${NC}"
echo -e "${BLUE}  Enterprise Discord Ticket System      ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# --- Configuration ---
DOMAIN="ticket.armesa.de"
INSTALL_DIR="/opt/ccx-ultra"
BOT_DIR="$INSTALL_DIR/bot"
WEB_DIR="$INSTALL_DIR/web"
VENV_DIR="$INSTALL_DIR/venv"
WEB_PORT=8001
DB_NAME="ccx_ultra"
ADMIN_EMAIL="admin@armesa.de"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo bash install.sh)${NC}"
    exit 1
fi

echo -e "${GREEN}[1/12] Updating system packages...${NC}"
apt update && apt upgrade -y

echo -e "${GREEN}[2/12] Installing base dependencies...${NC}"
apt install -y \
    python3 python3-pip python3-venv python3-dev \
    build-essential gcc \
    nginx certbot python3-certbot-nginx \
    supervisor \
    curl wget git \
    ufw \
    gnupg2

echo -e "${GREEN}[3/12] Installing MongoDB...${NC}"
# MongoDB 7.0 for Debian 12
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
apt update
apt install -y mongodb-org
systemctl start mongod
systemctl enable mongod
echo -e "${GREEN}  MongoDB started and enabled${NC}"

echo -e "${GREEN}[4/12] Installing Redis...${NC}"
apt install -y redis-server
systemctl start redis-server
systemctl enable redis-server
echo -e "${GREEN}  Redis started and enabled${NC}"

echo -e "${GREEN}[5/12] Creating directory structure...${NC}"
mkdir -p $BOT_DIR $WEB_DIR $INSTALL_DIR/logs $INSTALL_DIR/transcripts

echo -e "${GREEN}[6/12] Setting up Python virtual environment...${NC}"
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install \
    fastapi uvicorn \
    motor pymongo \
    bcrypt pyjwt python-jose[cryptography] \
    python-dotenv \
    discord.py aiohttp \
    python-multipart \
    sse-starlette

echo -e "${GREEN}[7/12] Creating configuration files...${NC}"

# Web Panel .env
if [ ! -f "$WEB_DIR/.env" ]; then
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > $WEB_DIR/.env << ENVEOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=$DB_NAME
JWT_SECRET=$JWT_SECRET
CORS_ORIGINS=https://$DOMAIN
DISCORD_BOT_TOKEN=CHANGE_ME
DISCORD_GUILD_ID=1407623359365120090
TICKET_CHANNEL_ID=1469120567532847225
TRANSCRIPT_LOG_CHANNEL_ID=1470212303260483817
TICKET_CATEGORY_ID=1469120434115969064
SUPPORT_ROLE_IDS=368510579511656449,372850494445453314,1006197315566051388
ENVEOF
    echo -e "${YELLOW}  IMPORTANT: Edit $WEB_DIR/.env and set DISCORD_BOT_TOKEN${NC}"
fi

# Bot config.env
if [ ! -f "$BOT_DIR/config.env" ]; then
    cat > $BOT_DIR/config.env << ENVEOF
DISCORD_BOT_TOKEN=CHANGE_ME
DISCORD_GUILD_ID=1407623359365120090
TICKET_CHANNEL_ID=1469120567532847225
TRANSCRIPT_LOG_CHANNEL_ID=1470212303260483817
TICKET_CATEGORY_ID=1469120434115969064
SUPPORT_ROLE_IDS=368510579511656449,372850494445453314,1006197315566051388
API_URL=http://localhost:$WEB_PORT/api
MAX_TICKETS_PER_USER=3
SLA_FIRST_RESPONSE_MINUTES=30
AUTO_CLOSE_INACTIVE_HOURS=48
ENVEOF
    echo -e "${YELLOW}  IMPORTANT: Edit $BOT_DIR/config.env and set DISCORD_BOT_TOKEN${NC}"
fi

echo -e "${GREEN}[8/12] Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/$DOMAIN << NGINXEOF
# Rate limiting zone
limit_req_zone \$binary_remote_addr zone=ccx_limit:10m rate=10r/s;

server {
    listen 80;
    server_name $DOMAIN;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' wss: ws:;" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_proxied any;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;

    # API reverse proxy
    location /api/ {
        limit_req zone=ccx_limit burst=20 nodelay;

        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # SSE support
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
    }

    # Frontend (if you build the React app)
    location / {
        root $WEB_DIR/static;
        try_files \$uri \$uri/ /index.html;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
echo -e "${GREEN}  Nginx configured for $DOMAIN${NC}"

echo -e "${GREEN}[9/12] Setting up HTTPS with Certbot...${NC}"
echo -e "${YELLOW}  Running: certbot --nginx -d $DOMAIN --email $ADMIN_EMAIL --agree-tos --non-interactive${NC}"
certbot --nginx -d $DOMAIN --email $ADMIN_EMAIL --agree-tos --non-interactive || {
    echo -e "${YELLOW}  Certbot failed - DNS might not be pointing to this server yet.${NC}"
    echo -e "${YELLOW}  Run manually: certbot --nginx -d $DOMAIN${NC}"
}

# Verify certbot renewal
certbot renew --dry-run || echo -e "${YELLOW}  Certbot renewal test failed - check configuration${NC}"

echo -e "${GREEN}[10/12] Creating Supervisor services...${NC}"

# Web Panel service
cat > /etc/supervisor/conf.d/ccx-webpanel.conf << SUPEOF
[program:ccx-webpanel]
command=$VENV_DIR/bin/uvicorn server:app --host 0.0.0.0 --port $WEB_PORT --workers 2
directory=$WEB_DIR
user=root
autostart=true
autorestart=true
stderr_logfile=$INSTALL_DIR/logs/webpanel.err.log
stdout_logfile=$INSTALL_DIR/logs/webpanel.out.log
environment=PATH="$VENV_DIR/bin"
SUPEOF

# Bot service
cat > /etc/supervisor/conf.d/ccx-bot.conf << SUPEOF
[program:ccx-bot]
command=$VENV_DIR/bin/python bot.py
directory=$BOT_DIR
user=root
autostart=true
autorestart=true
stderr_logfile=$INSTALL_DIR/logs/bot.err.log
stdout_logfile=$INSTALL_DIR/logs/bot.out.log
environment=PATH="$VENV_DIR/bin"
SUPEOF

supervisorctl reread
supervisorctl update
echo -e "${GREEN}  Supervisor services configured${NC}"

echo -e "${GREEN}[11/12] Configuring Firewall...${NC}"
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable
echo -e "${GREEN}  Firewall enabled (22, 80, 443)${NC}"

echo -e "${GREEN}[12/12] Final Setup...${NC}"

# Create backup script
cat > $INSTALL_DIR/backup.sh << 'BACKUPEOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/ccx-ultra/backups/$DATE"
mkdir -p $BACKUP_DIR
mongodump --db ccx_ultra --out $BACKUP_DIR/mongodb
cp /opt/ccx-ultra/web/.env $BACKUP_DIR/
cp /opt/ccx-ultra/bot/config.env $BACKUP_DIR/
echo "Backup saved to $BACKUP_DIR"
# Keep only last 7 backups
ls -dt /opt/ccx-ultra/backups/*/ | tail -n +8 | xargs rm -rf
BACKUPEOF
chmod +x $INSTALL_DIR/backup.sh

# Add daily backup cron
echo "0 3 * * * /opt/ccx-ultra/backup.sh" | crontab -l 2>/dev/null | cat - | crontab -

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation Complete!                ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}NEXT STEPS:${NC}"
echo "1. Copy bot.py to $BOT_DIR/"
echo "2. Copy server.py to $WEB_DIR/"
echo "3. Edit $WEB_DIR/.env - Set DISCORD_BOT_TOKEN"
echo "4. Edit $BOT_DIR/config.env - Set DISCORD_BOT_TOKEN"
echo "5. Build React frontend and copy to $WEB_DIR/static/"
echo "6. Start services: supervisorctl start all"
echo ""
echo -e "${BLUE}USEFUL COMMANDS:${NC}"
echo "  supervisorctl status              # Check service status"
echo "  supervisorctl restart ccx-bot     # Restart bot"
echo "  supervisorctl restart ccx-webpanel # Restart web panel"
echo "  tail -f $INSTALL_DIR/logs/*.log   # View logs"
echo "  /opt/ccx-ultra/backup.sh          # Manual backup"
echo ""
echo -e "${BLUE}DISCORD DEVELOPER PORTAL SETUP:${NC}"
echo "  Required Privileged Intents:"
echo "    - PRESENCE INTENT (required for online status detection)"
echo "    - SERVER MEMBERS INTENT (required for member access)"
echo "    - MESSAGE CONTENT INTENT (required for transcript generation)"
echo ""
echo "  Bot Permissions (integer): 8 (Administrator) or specific:"
echo "    - Manage Channels"
echo "    - Read Messages/View Channels"
echo "    - Send Messages"
echo "    - Manage Messages"
echo "    - Embed Links"
echo "    - Attach Files"
echo "    - Read Message History"
echo "    - Add Reactions"
echo "    - Use Slash Commands"
echo ""
echo "  OAuth2 Scopes:"
echo "    - bot"
echo "    - applications.commands"
echo ""
echo "  Bot invite URL:"
echo "  https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&scope=bot%20applications.commands"
echo ""
echo -e "${YELLOW}NOTE: Make sure bot role is ABOVE the support roles in Server Settings > Roles${NC}"
