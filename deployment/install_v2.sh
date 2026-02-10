#!/bin/bash
#=============================================================================
# Control Center X Ultra - Enterprise Discord Ticket System
# Verbessertes Installations-Script für Debian 12
# Version 2.0 - Mit besserer Fehlerbehandlung und Diagnose
#=============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging
LOG_FILE="/tmp/ccx-ultra-install.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

echo -e "${CYAN}"
echo "========================================"
echo "  Control Center X Ultra - Installer    "
echo "  Enterprise Discord Ticket System      "
echo "  Version 2.0 - Verbessert              "
echo "========================================"
echo -e "${NC}"
echo ""
echo -e "${BLUE}Log wird gespeichert in: ${LOG_FILE}${NC}"
echo ""

# --- Konfiguration (Passen Sie hier Ihre Werte an) ---
DOMAIN="${DOMAIN:-ticket.armesa.de}"
INSTALL_DIR="${INSTALL_DIR:-/opt/ccx-ultra}"
BOT_DIR="$INSTALL_DIR/bot"
WEB_DIR="$INSTALL_DIR/web"
VENV_DIR="$INSTALL_DIR/venv"
WEB_PORT="${WEB_PORT:-8001}"
DB_NAME="${DB_NAME:-ccx_ultra}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@armesa.de}"

# Discord IDs (werden später konfiguriert)
DISCORD_GUILD_ID="${DISCORD_GUILD_ID:-YOUR_GUILD_ID}"
TICKET_CHANNEL_ID="${TICKET_CHANNEL_ID:-YOUR_CHANNEL_ID}"
TRANSCRIPT_LOG_CHANNEL_ID="${TRANSCRIPT_LOG_CHANNEL_ID:-YOUR_LOG_CHANNEL_ID}"
TICKET_CATEGORY_ID="${TICKET_CATEGORY_ID:-YOUR_CATEGORY_ID}"
SUPPORT_ROLE_IDS="${SUPPORT_ROLE_IDS:-ROLE_ID1,ROLE_ID2,ROLE_ID3}"

# --- Funktionen ---
log_step() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[WARNUNG] $1${NC}"
}

log_error() {
    echo -e "${RED}[FEHLER] $1${NC}"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 gefunden"
        return 0
    else
        echo -e "${RED}✗${NC} $1 nicht gefunden"
        return 1
    fi
}

# --- Voraussetzungen prüfen ---
log_step "Prüfe Systemvoraussetzungen..."

# Root Check
if [ "$EUID" -ne 0 ]; then
    log_error "Bitte als root ausführen: sudo bash install_v2.sh"
    exit 1
fi

# OS Check
if [ ! -f /etc/debian_version ]; then
    log_warning "Dieses Script ist für Debian 12 optimiert"
    read -p "Trotzdem fortfahren? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# RAM Check
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM" -lt 1800 ]; then
    log_warning "Weniger als 2GB RAM erkannt ($TOTAL_RAM MB). Empfohlen: 2GB+"
fi

# Disk Space Check
AVAILABLE_DISK=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_DISK" -lt 10 ]; then
    log_warning "Weniger als 10GB freier Speicher ($AVAILABLE_DISK GB). Empfohlen: 20GB+"
fi

echo ""
echo -e "${BLUE}System-Info:${NC}"
echo "  RAM: ${TOTAL_RAM}MB"
echo "  Disk: ${AVAILABLE_DISK}GB verfügbar"
echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo ""

# --- Installation starten ---
log_step "[1/13] Aktualisiere System-Pakete..."
apt update -qq
apt upgrade -y -qq

log_step "[2/13] Installiere Basis-Dependencies..."
apt install -y -qq \
    python3 python3-pip python3-venv python3-dev \
    build-essential gcc pkg-config \
    nginx certbot python3-certbot-nginx \
    supervisor \
    curl wget git \
    ufw \
    gnupg2 \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    net-tools \
    dnsutils \
    htop

log_step "[3/13] Installiere MongoDB 7.0..."
if ! check_command mongod; then
    # MongoDB GPG Key
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
        gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg
    
    # MongoDB Repository
    echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | \
        tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    
    apt update -qq
    apt install -y mongodb-org
fi

# MongoDB starten
systemctl start mongod
systemctl enable mongod

# MongoDB Status prüfen
if systemctl is-active --quiet mongod; then
    echo -e "${GREEN}✓ MongoDB läuft${NC}"
else
    log_error "MongoDB konnte nicht gestartet werden!"
    systemctl status mongod
    exit 1
fi

log_step "[4/13] Installiere Redis..."
apt install -y redis-server
systemctl start redis-server
systemctl enable redis-server

if systemctl is-active --quiet redis-server; then
    echo -e "${GREEN}✓ Redis läuft${NC}"
else
    log_warning "Redis läuft nicht - wird für Rate Limiting benötigt"
fi

log_step "[5/13] Erstelle Verzeichnisstruktur..."
mkdir -p "$BOT_DIR" "$WEB_DIR" "$INSTALL_DIR/logs" "$INSTALL_DIR/transcripts" "$INSTALL_DIR/backups"
chmod 755 "$INSTALL_DIR"
echo -e "${GREEN}✓ Verzeichnisse erstellt in $INSTALL_DIR${NC}"

log_step "[6/13] Erstelle Python Virtual Environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

log_step "[7/13] Installiere Python Dependencies..."
pip install --upgrade pip -q
pip install -q \
    fastapi==0.115.12 \
    uvicorn[standard]==0.34.3 \
    motor==3.7.1 \
    pymongo==4.11.2 \
    bcrypt==4.3.0 \
    pyjwt==2.11.0 \
    python-jose[cryptography]==3.3.0 \
    python-dotenv==1.0.1 \
    discord.py==2.4.0 \
    aiohttp==3.11.11 \
    python-multipart==0.0.20 \
    sse-starlette==2.2.1 \
    starlette==0.45.2

echo -e "${GREEN}✓ Python Dependencies installiert${NC}"

log_step "[8/13] Erstelle Konfigurationsdateien..."

# Web Panel .env
if [ ! -f "$WEB_DIR/.env" ]; then
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > "$WEB_DIR/.env" << ENVEOF
# MongoDB Konfiguration
MONGO_URL=mongodb://localhost:27017
DB_NAME=$DB_NAME

# JWT Secret für Authentication
JWT_SECRET=$JWT_SECRET

# CORS Origins (Ihre Domain)
CORS_ORIGINS=https://$DOMAIN,http://localhost:3000

# Discord Bot Token (WICHTIG: Ändern Sie dies!)
DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# Discord Server/Channel IDs (WICHTIG: Ändern Sie dies!)
DISCORD_GUILD_ID=$DISCORD_GUILD_ID
TICKET_CHANNEL_ID=$TICKET_CHANNEL_ID
TRANSCRIPT_LOG_CHANNEL_ID=$TRANSCRIPT_LOG_CHANNEL_ID
TICKET_CATEGORY_ID=$TICKET_CATEGORY_ID

# Support Rollen IDs (komma-separiert)
SUPPORT_ROLE_IDS=$SUPPORT_ROLE_IDS
ENVEOF
    echo -e "${YELLOW}✓ Web Panel .env erstellt - WICHTIG: Bearbeiten Sie $WEB_DIR/.env${NC}"
else
    echo -e "${BLUE}ℹ .env existiert bereits, überspringe${NC}"
fi

# Bot config.env
if [ ! -f "$BOT_DIR/config.env" ]; then
    cat > "$BOT_DIR/config.env" << ENVEOF
# Discord Bot Token (WICHTIG: Ändern Sie dies!)
DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# Discord Server/Channel IDs (WICHTIG: Ändern Sie dies!)
DISCORD_GUILD_ID=$DISCORD_GUILD_ID
TICKET_CHANNEL_ID=$TICKET_CHANNEL_ID
TRANSCRIPT_LOG_CHANNEL_ID=$TRANSCRIPT_LOG_CHANNEL_ID
TICKET_CATEGORY_ID=$TICKET_CATEGORY_ID

# Support Rollen IDs (komma-separiert)
SUPPORT_ROLE_IDS=$SUPPORT_ROLE_IDS

# API Endpoint (normalerweise nicht ändern)
API_URL=http://localhost:$WEB_PORT/api

# Ticket System Einstellungen
MAX_TICKETS_PER_USER=3
SLA_FIRST_RESPONSE_MINUTES=30
AUTO_CLOSE_INACTIVE_HOURS=48
ENVEOF
    echo -e "${YELLOW}✓ Bot config.env erstellt - WICHTIG: Bearbeiten Sie $BOT_DIR/config.env${NC}"
else
    echo -e "${BLUE}ℹ config.env existiert bereits, überspringe${NC}"
fi

log_step "[9/13] Konfiguriere Nginx..."

# Nginx Config erstellen
cat > "/etc/nginx/sites-available/$DOMAIN" << 'NGINXEOF'
# Rate limiting zone
limit_req_zone $binary_remote_addr zone=ccx_limit:10m rate=10r/s;

server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_proxied any;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;

    # API reverse proxy
    location /api/ {
        limit_req zone=ccx_limit burst=20 nodelay;

        proxy_pass http://127.0.0.1:WEB_PORT_PLACEHOLDER/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE support
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
    }

    # Frontend static files
    location / {
        root WEBDIR_PLACEHOLDER/static;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 30d;
            add_header Cache-Control "public, no-transform";
        }
    }
}
NGINXEOF

# Platzhalter ersetzen
sed -i "s|DOMAIN_PLACEHOLDER|$DOMAIN|g" "/etc/nginx/sites-available/$DOMAIN"
sed -i "s|WEB_PORT_PLACEHOLDER|$WEB_PORT|g" "/etc/nginx/sites-available/$DOMAIN"
sed -i "s|WEBDIR_PLACEHOLDER|$WEB_DIR|g" "/etc/nginx/sites-available/$DOMAIN"

# Symlink erstellen
ln -sf "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-enabled/"
rm -f /etc/nginx/sites-enabled/default

# Nginx testen
if nginx -t 2>&1 | grep -q "successful"; then
    echo -e "${GREEN}✓ Nginx Konfiguration OK${NC}"
    systemctl reload nginx
else
    log_error "Nginx Konfiguration fehlerhaft!"
    nginx -t
    exit 1
fi

log_step "[10/13] HTTPS mit Certbot einrichten..."
echo -e "${YELLOW}Hinweis: DNS muss auf diesen Server zeigen!${NC}"
echo -e "${YELLOW}Überprüfen Sie: dig $DOMAIN${NC}"
echo ""

# Check DNS first
SERVER_IP=$(curl -s ifconfig.me)
DNS_IP=$(dig +short "$DOMAIN" | head -n1)

if [ "$SERVER_IP" = "$DNS_IP" ]; then
    echo -e "${GREEN}✓ DNS zeigt korrekt auf diesen Server${NC}"
    
    # Certbot ausführen
    if certbot --nginx -d "$DOMAIN" --email "$ADMIN_EMAIL" --agree-tos --non-interactive --redirect; then
        echo -e "${GREEN}✓ SSL Zertifikat installiert${NC}"
    else
        log_warning "Certbot fehlgeschlagen - können Sie später manuell ausführen:"
        echo "  certbot --nginx -d $DOMAIN"
    fi
else
    log_warning "DNS stimmt nicht überein!"
    echo "  Server IP: $SERVER_IP"
    echo "  DNS IP: $DNS_IP"
    echo ""
    echo "Bitte DNS konfigurieren und später Certbot manuell ausführen:"
    echo "  certbot --nginx -d $DOMAIN"
fi

# Certbot Renewal testen
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    certbot renew --dry-run 2>/dev/null && echo -e "${GREEN}✓ Certbot Auto-Renewal OK${NC}"
fi

log_step "[11/13] Erstelle Supervisor Services..."

# Web Panel Service
cat > /etc/supervisor/conf.d/ccx-webpanel.conf << SUPEOF
[program:ccx-webpanel]
command=$VENV_DIR/bin/uvicorn server:app --host 0.0.0.0 --port $WEB_PORT --workers 2
directory=$WEB_DIR
user=root
autostart=true
autorestart=true
startsecs=5
startretries=5
stopwaitsecs=10
stderr_logfile=$INSTALL_DIR/logs/webpanel.err.log
stdout_logfile=$INSTALL_DIR/logs/webpanel.out.log
stderr_logfile_maxbytes=20MB
stdout_logfile_maxbytes=20MB
stderr_logfile_backups=5
stdout_logfile_backups=5
environment=PATH="$VENV_DIR/bin"
SUPEOF

# Bot Service
cat > /etc/supervisor/conf.d/ccx-bot.conf << SUPEOF
[program:ccx-bot]
command=$VENV_DIR/bin/python bot.py
directory=$BOT_DIR
user=root
autostart=false
autorestart=true
startsecs=5
startretries=5
stopwaitsecs=10
stderr_logfile=$INSTALL_DIR/logs/bot.err.log
stdout_logfile=$INSTALL_DIR/logs/bot.out.log
stderr_logfile_maxbytes=20MB
stdout_logfile_maxbytes=20MB
stderr_logfile_backups=5
stdout_logfile_backups=5
environment=PATH="$VENV_DIR/bin"
SUPEOF

# Supervisor neu laden
supervisorctl reread
supervisorctl update

echo -e "${GREEN}✓ Supervisor Services konfiguriert${NC}"
echo -e "${YELLOW}ℹ Bot auf 'autostart=false' - starten Sie ihn nach Konfiguration mit: supervisorctl start ccx-bot${NC}"

log_step "[12/13] Konfiguriere Firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp comment 'SSH'
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'
    echo "y" | ufw enable
    echo -e "${GREEN}✓ Firewall konfiguriert (SSH, HTTP, HTTPS)${NC}"
else
    log_warning "UFW nicht installiert, Firewall übersprungen"
fi

log_step "[13/13] Erstelle Backup Script..."

cat > "$INSTALL_DIR/backup.sh" << 'BACKUPEOF'
#!/bin/bash
# CCX Ultra Backup Script
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/ccx-ultra/backups/$DATE"

echo "Erstelle Backup in $BACKUP_DIR..."

mkdir -p "$BACKUP_DIR"

# MongoDB Backup
mongodump --db ccx_ultra --out "$BACKUP_DIR/mongodb" --quiet

# Config Backups
cp /opt/ccx-ultra/web/.env "$BACKUP_DIR/web.env" 2>/dev/null
cp /opt/ccx-ultra/bot/config.env "$BACKUP_DIR/bot.config.env" 2>/dev/null

# Supervisor Configs
cp /etc/supervisor/conf.d/ccx-*.conf "$BACKUP_DIR/" 2>/dev/null

# Nginx Config
cp /etc/nginx/sites-available/ticket.* "$BACKUP_DIR/" 2>/dev/null

echo "Backup abgeschlossen: $BACKUP_DIR"

# Alte Backups löschen (behalte nur die letzten 7)
ls -dt /opt/ccx-ultra/backups/*/ | tail -n +8 | xargs rm -rf 2>/dev/null

echo "Alte Backups bereinigt (behalte letzte 7)"
BACKUPEOF

chmod +x "$INSTALL_DIR/backup.sh"

# Backup Cronjob hinzufügen
(crontab -l 2>/dev/null | grep -v "ccx-ultra/backup.sh"; echo "0 3 * * * $INSTALL_DIR/backup.sh >> $INSTALL_DIR/logs/backup.log 2>&1") | crontab -

echo -e "${GREEN}✓ Täglicher Backup Cronjob erstellt (03:00 Uhr)${NC}"

# --- Health Check Script erstellen ---
cat > "$INSTALL_DIR/healthcheck.sh" << 'HEALTHEOF'
#!/bin/bash
echo "==================================="
echo "CCX Ultra System Health Check"
echo "==================================="
echo ""

echo "1. Services:"
supervisorctl status
echo ""

echo "2. Ports:"
netstat -tlnp | grep -E "(8001|27017|6379|80|443)" || echo "Keine Ports gefunden"
echo ""

echo "3. MongoDB:"
if systemctl is-active --quiet mongod; then
    echo "✓ MongoDB läuft"
else
    echo "✗ MongoDB läuft NICHT"
fi
echo ""

echo "4. Redis:"
if systemctl is-active --quiet redis-server; then
    echo "✓ Redis läuft"
else
    echo "✗ Redis läuft NICHT"
fi
echo ""

echo "5. Nginx:"
if systemctl is-active --quiet nginx; then
    echo "✓ Nginx läuft"
    nginx -t 2>&1 | grep -q "successful" && echo "✓ Nginx Konfiguration OK" || echo "✗ Nginx Konfiguration FEHLER"
else
    echo "✗ Nginx läuft NICHT"
fi
echo ""

echo "6. Backend API:"
RESPONSE=$(curl -s http://localhost:8001/api/health 2>/dev/null)
if echo "$RESPONSE" | grep -q "ok"; then
    echo "✓ Backend API antwortet: $RESPONSE"
else
    echo "✗ Backend API antwortet NICHT"
fi
echo ""

echo "7. Disk Space:"
df -h | grep -E "(Filesystem|/dev/)"
echo ""

echo "8. Memory:"
free -h
echo ""

echo "9. Letzte Backend Logs (10 Zeilen):"
tail -n 10 /opt/ccx-ultra/logs/webpanel.err.log 2>/dev/null || echo "Keine Logs"
echo ""

echo "==================================="
HEALTHEOF

chmod +x "$INSTALL_DIR/healthcheck.sh"

# --- Installation abgeschlossen ---
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation Abgeschlossen!          ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo -e "${CYAN}📋 INSTALLATION SUMMARY:${NC}"
echo "  Domain: $DOMAIN"
echo "  Install Dir: $INSTALL_DIR"
echo "  Backend Port: $WEB_PORT"
echo "  MongoDB: $(systemctl is-active mongod)"
echo "  Redis: $(systemctl is-active redis-server)"
echo "  Nginx: $(systemctl is-active nginx)"
echo ""

echo -e "${YELLOW}⚠️  WICHTIGE NÄCHSTE SCHRITTE:${NC}"
echo ""
echo -e "${CYAN}1. Backend & Bot Dateien kopieren:${NC}"
echo "   cp /pfad/zu/server.py $WEB_DIR/"
echo "   cp /pfad/zu/bot.py $BOT_DIR/"
echo ""

echo -e "${CYAN}2. Konfiguration anpassen:${NC}"
echo "   nano $WEB_DIR/.env"
echo "   nano $BOT_DIR/config.env"
echo "   ${YELLOW}→ DISCORD_BOT_TOKEN setzen${NC}"
echo "   ${YELLOW}→ Discord IDs anpassen${NC}"
echo ""

echo -e "${CYAN}3. Frontend bauen:${NC}"
echo "   cd /pfad/zu/frontend"
echo "   yarn install"
echo "   echo 'REACT_APP_BACKEND_URL=https://$DOMAIN' > .env"
echo "   yarn build"
echo "   cp -r build/* $WEB_DIR/static/"
echo ""

echo -e "${CYAN}4. Services starten:${NC}"
echo "   supervisorctl start ccx-webpanel"
echo "   supervisorctl start ccx-bot  # Nach Konfiguration"
echo ""

echo -e "${CYAN}5. System testen:${NC}"
echo "   $INSTALL_DIR/healthcheck.sh"
echo "   curl http://localhost:8001/api/health"
echo "   https://$DOMAIN/login"
echo ""

echo -e "${BLUE}📚 DOKUMENTATION:${NC}"
echo "  Installation Guide: ./INSTALLATION_GUIDE.md"
echo "  Health Check: $INSTALL_DIR/healthcheck.sh"
echo "  Backup: $INSTALL_DIR/backup.sh"
echo "  Logs: $INSTALL_DIR/logs/"
echo ""

echo -e "${BLUE}🔧 NÜTZLICHE BEFEHLE:${NC}"
echo "  supervisorctl status         # Service Status"
echo "  supervisorctl restart all    # Alle Services neu starten"
echo "  tail -f $INSTALL_DIR/logs/webpanel.err.log  # Backend Logs"
echo "  nginx -t && systemctl reload nginx          # Nginx neu laden"
echo ""

echo -e "${GREEN}Standard Login (nach Setup):${NC}"
echo "  Username: admin"
echo "  Password: admin123"
echo "  ${YELLOW}→ Bitte nach erstem Login ändern!${NC}"
echo ""

echo -e "${YELLOW}Bei Problemen:${NC}"
echo "  1. Health Check ausführen: $INSTALL_DIR/healthcheck.sh"
echo "  2. Logs prüfen: tail -f $INSTALL_DIR/logs/*.log"
echo "  3. Installation Guide lesen: ./INSTALLATION_GUIDE.md"
echo ""

echo -e "${GREEN}✓ Installation erfolgreich abgeschlossen!${NC}"
echo -e "${YELLOW}  Log gespeichert in: $LOG_FILE${NC}"
echo ""
