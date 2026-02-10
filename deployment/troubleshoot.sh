#!/bin/bash
#=============================================================================
# Control Center X Ultra - Troubleshooting & Diagnose Tool
#=============================================================================

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="/opt/ccx-ultra"
WEB_DIR="$INSTALL_DIR/web"
BOT_DIR="$INSTALL_DIR/bot"
DOMAIN="ticket.armesa.de"

echo -e "${CYAN}"
echo "========================================"
echo "  CCX Ultra - Troubleshooting Tool      "
echo "========================================"
echo -e "${NC}"
echo ""

# --- Funktion: Check mit Status ---
check_status() {
    local name="$1"
    local command="$2"
    
    printf "%-40s" "$name"
    if eval "$command" &>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FEHLER${NC}"
        return 1
    fi
}

# --- 1. System Checks ---
echo -e "${BLUE}═══ SYSTEM CHECKS ═══${NC}"
check_status "Root Zugriff" "[ \$EUID -eq 0 ]"
check_status "Installation Verzeichnis" "[ -d $INSTALL_DIR ]"
check_status "Virtual Environment" "[ -d $INSTALL_DIR/venv ]"
check_status "Backend Dateien" "[ -f $WEB_DIR/server.py ]"
check_status "Bot Dateien" "[ -f $BOT_DIR/bot.py ]"
echo ""

# --- 2. Services ---
echo -e "${BLUE}═══ SERVICES STATUS ═══${NC}"
check_status "MongoDB läuft" "systemctl is-active --quiet mongod"
check_status "Redis läuft" "systemctl is-active --quiet redis-server"
check_status "Nginx läuft" "systemctl is-active --quiet nginx"
check_status "Supervisor läuft" "systemctl is-active --quiet supervisor"

echo ""
echo "Supervisor Services:"
supervisorctl status
echo ""

# --- 3. Ports & Netzwerk ---
echo -e "${BLUE}═══ NETZWERK & PORTS ═══${NC}"
check_status "Port 8001 (Backend)" "netstat -tlnp | grep -q ':8001'"
check_status "Port 27017 (MongoDB)" "netstat -tlnp | grep -q ':27017'"
check_status "Port 80 (HTTP)" "netstat -tlnp | grep -q ':80'"
check_status "Port 443 (HTTPS)" "netstat -tlnp | grep -q ':443'"

echo ""
echo "Aktive Connections:"
netstat -tlnp | grep -E "(8001|27017|80|443)"
echo ""

# --- 4. DNS & SSL ---
echo -e "${BLUE}═══ DNS & SSL ═══${NC}"
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "Unbekannt")
DNS_IP=$(dig +short "$DOMAIN" 2>/dev/null | head -n1 || echo "Unbekannt")

echo "Server IP: $SERVER_IP"
echo "DNS IP: $DNS_IP"

if [ "$SERVER_IP" = "$DNS_IP" ]; then
    echo -e "${GREEN}✓ DNS zeigt korrekt auf diesen Server${NC}"
else
    echo -e "${RED}✗ DNS stimmt NICHT überein!${NC}"
fi

if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo -e "${GREEN}✓ SSL Zertifikat vorhanden${NC}"
    echo "Zertifikat läuft ab:"
    openssl x509 -in "/etc/letsencrypt/live/$DOMAIN/cert.pem" -noout -enddate 2>/dev/null || echo "Fehler beim Lesen"
else
    echo -e "${YELLOW}⚠ Kein SSL Zertifikat gefunden${NC}"
fi
echo ""

# --- 5. Backend API Test ---
echo -e "${BLUE}═══ BACKEND API TEST ═══${NC}"
echo "Teste http://localhost:8001/api/health"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8001/api/health 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Backend antwortet (200 OK)${NC}"
    echo "Response: $BODY"
else
    echo -e "${RED}✗ Backend antwortet NICHT korrekt${NC}"
    echo "HTTP Code: $HTTP_CODE"
    echo "Response: $BODY"
fi
echo ""

# --- 6. Konfiguration prüfen ---
echo -e "${BLUE}═══ KONFIGURATION ═══${NC}"

if [ -f "$WEB_DIR/.env" ]; then
    echo -e "${GREEN}✓ Backend .env vorhanden${NC}"
    
    # Token prüfen
    if grep -q "DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN_HERE" "$WEB_DIR/.env" 2>/dev/null; then
        echo -e "${RED}  ✗ DISCORD_BOT_TOKEN nicht konfiguriert!${NC}"
    else
        echo -e "${GREEN}  ✓ DISCORD_BOT_TOKEN gesetzt${NC}"
    fi
    
    # JWT Secret prüfen
    if grep -q "JWT_SECRET=" "$WEB_DIR/.env" 2>/dev/null; then
        echo -e "${GREEN}  ✓ JWT_SECRET vorhanden${NC}"
    else
        echo -e "${RED}  ✗ JWT_SECRET fehlt!${NC}"
    fi
else
    echo -e "${RED}✗ Backend .env FEHLT!${NC}"
fi

if [ -f "$BOT_DIR/config.env" ]; then
    echo -e "${GREEN}✓ Bot config.env vorhanden${NC}"
    
    if grep -q "DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN_HERE" "$BOT_DIR/config.env" 2>/dev/null; then
        echo -e "${RED}  ✗ Bot DISCORD_BOT_TOKEN nicht konfiguriert!${NC}"
    else
        echo -e "${GREEN}  ✓ Bot DISCORD_BOT_TOKEN gesetzt${NC}"
    fi
else
    echo -e "${RED}✗ Bot config.env FEHLT!${NC}"
fi
echo ""

# --- 7. Nginx Config ---
echo -e "${BLUE}═══ NGINX KONFIGURATION ═══${NC}"
if nginx -t 2>&1 | grep -q "successful"; then
    echo -e "${GREEN}✓ Nginx Konfiguration OK${NC}"
else
    echo -e "${RED}✗ Nginx Konfiguration FEHLER${NC}"
    nginx -t
fi

if [ -f "/etc/nginx/sites-enabled/$DOMAIN" ]; then
    echo -e "${GREEN}✓ Site Config aktiv${NC}"
else
    echo -e "${RED}✗ Site Config NICHT aktiv${NC}"
fi
echo ""

# --- 8. Logs ---
echo -e "${BLUE}═══ AKTUELLE FEHLER IN LOGS ═══${NC}"

if [ -f "$INSTALL_DIR/logs/webpanel.err.log" ]; then
    echo -e "${YELLOW}Backend Errors (letzte 10 Zeilen):${NC}"
    tail -n 10 "$INSTALL_DIR/logs/webpanel.err.log" | grep -i "error\|exception\|failed" || echo "Keine aktuellen Fehler"
else
    echo "Keine Backend Logs gefunden"
fi
echo ""

if [ -f "$INSTALL_DIR/logs/bot.err.log" ]; then
    echo -e "${YELLOW}Bot Errors (letzte 10 Zeilen):${NC}"
    tail -n 10 "$INSTALL_DIR/logs/bot.err.log" | grep -i "error\|exception\|failed" || echo "Keine aktuellen Fehler"
else
    echo "Keine Bot Logs gefunden"
fi
echo ""

# --- 9. Ressourcen ---
echo -e "${BLUE}═══ SYSTEM RESSOURCEN ═══${NC}"
echo "Disk Space:"
df -h | grep -E "(Filesystem|/dev/)" | head -3
echo ""
echo "Memory:"
free -h | grep -E "(total|Mem)"
echo ""
echo "CPU Load:"
uptime
echo ""

# --- 10. Häufige Probleme & Lösungen ---
echo -e "${BLUE}═══ HÄUFIGE PROBLEME & LÖSUNGEN ═══${NC}"
echo ""

# Problem 1: Backend läuft nicht
if ! systemctl is-active --quiet supervisor || ! supervisorctl status ccx-webpanel | grep -q "RUNNING"; then
    echo -e "${YELLOW}❌ PROBLEM: Backend läuft nicht${NC}"
    echo -e "${GREEN}LÖSUNG:${NC}"
    echo "  1. Logs prüfen:"
    echo "     tail -f $INSTALL_DIR/logs/webpanel.err.log"
    echo ""
    echo "  2. Manuell testen:"
    echo "     cd $WEB_DIR"
    echo "     source $INSTALL_DIR/venv/bin/activate"
    echo "     uvicorn server:app --host 0.0.0.0 --port 8001"
    echo ""
    echo "  3. Dependencies installieren (falls Fehler):"
    echo "     pip install -r $WEB_DIR/requirements.txt"
    echo ""
    echo "  4. Service neu starten:"
    echo "     supervisorctl restart ccx-webpanel"
    echo ""
fi

# Problem 2: 404 Not Found
RESPONSE_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/health 2>/dev/null)
if [ "$RESPONSE_CODE" != "200" ]; then
    echo -e "${YELLOW}❌ PROBLEM: API gibt 404/Fehler zurück${NC}"
    echo -e "${GREEN}LÖSUNG:${NC}"
    echo "  1. Backend Port prüfen:"
    echo "     netstat -tlnp | grep 8001"
    echo ""
    echo "  2. Nginx Proxy prüfen:"
    echo "     grep 'proxy_pass' /etc/nginx/sites-enabled/$DOMAIN"
    echo "     # Sollte sein: proxy_pass http://127.0.0.1:8001/api/;"
    echo ""
    echo "  3. Nginx neu laden:"
    echo "     nginx -t && systemctl reload nginx"
    echo ""
fi

# Problem 3: Bot verbindet nicht
if supervisorctl status ccx-bot 2>/dev/null | grep -q "FATAL\|EXITED"; then
    echo -e "${YELLOW}❌ PROBLEM: Bot startet nicht${NC}"
    echo -e "${GREEN}LÖSUNG:${NC}"
    echo "  1. Bot Logs prüfen:"
    echo "     tail -f $INSTALL_DIR/logs/bot.err.log"
    echo ""
    echo "  2. Discord Token prüfen:"
    echo "     grep DISCORD_BOT_TOKEN $BOT_DIR/config.env"
    echo ""
    echo "  3. Discord Intents aktiviert?"
    echo "     → https://discord.com/developers/applications"
    echo "     → Bot → Privileged Gateway Intents"
    echo "     → Alle 3 aktivieren (Presence, Members, Message Content)"
    echo ""
    echo "  4. Bot manuell testen:"
    echo "     cd $BOT_DIR"
    echo "     source $INSTALL_DIR/venv/bin/activate"
    echo "     python bot.py"
    echo ""
fi

# Problem 4: Frontend weiße Seite
if [ ! -f "$WEB_DIR/static/index.html" ]; then
    echo -e "${YELLOW}❌ PROBLEM: Frontend nicht gebaut${NC}"
    echo -e "${GREEN}LÖSUNG:${NC}"
    echo "  1. Frontend bauen:"
    echo "     cd /pfad/zu/frontend"
    echo "     yarn install"
    echo "     echo 'REACT_APP_BACKEND_URL=https://$DOMAIN' > .env"
    echo "     yarn build"
    echo ""
    echo "  2. Build kopieren:"
    echo "     cp -r build/* $WEB_DIR/static/"
    echo ""
    echo "  3. Nginx neu laden:"
    echo "     systemctl reload nginx"
    echo ""
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${CYAN}Troubleshooting abgeschlossen!${NC}"
echo ""
echo -e "${YELLOW}Weitere Hilfe:${NC}"
echo "  • Installation Guide: ./INSTALLATION_GUIDE.md"
echo "  • Health Check: $INSTALL_DIR/healthcheck.sh"
echo "  • Logs: ls -lh $INSTALL_DIR/logs/"
echo ""

# Zusammenfassung
echo -e "${CYAN}═══ ZUSAMMENFASSUNG ═══${NC}"
ISSUES=0

! systemctl is-active --quiet mongod && echo -e "${RED}✗ MongoDB läuft nicht${NC}" && ((ISSUES++))
! systemctl is-active --quiet nginx && echo -e "${RED}✗ Nginx läuft nicht${NC}" && ((ISSUES++))
! supervisorctl status ccx-webpanel 2>/dev/null | grep -q "RUNNING" && echo -e "${RED}✗ Backend läuft nicht${NC}" && ((ISSUES++))
[ ! -f "$WEB_DIR/static/index.html" ] && echo -e "${RED}✗ Frontend nicht gebaut${NC}" && ((ISSUES++))

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ Keine kritischen Probleme gefunden!${NC}"
    echo ""
    echo "Testen Sie den Login:"
    echo "  https://$DOMAIN/login"
    echo "  Username: admin"
    echo "  Password: admin123"
else
    echo -e "${YELLOW}⚠ $ISSUES Problem(e) gefunden (siehe oben)${NC}"
fi
echo ""
