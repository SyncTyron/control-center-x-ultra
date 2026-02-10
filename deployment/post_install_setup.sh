#!/bin/bash
#=============================================================================
# Control Center X Ultra - Post-Installation Setup
# Führt alle Schritte nach der Basis-Installation durch
#=============================================================================

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "========================================"
echo "  CCX Ultra - Post-Installation Setup   "
echo "========================================"
echo -e "${NC}"

# Konfiguration
INSTALL_DIR="/opt/ccx-ultra"
WEB_DIR="$INSTALL_DIR/web"
BOT_DIR="$INSTALL_DIR/bot"
VENV_DIR="$INSTALL_DIR/venv"
DOMAIN="ticket.armesa.de"

# Prüfe ob Basis-Installation vorhanden
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}FEHLER: $INSTALL_DIR nicht gefunden!${NC}"
    echo "Bitte führen Sie zuerst install_v2.sh aus!"
    exit 1
fi

# Prüfe aktuelles Verzeichnis
if [ ! -f "../../backend/server.py" ]; then
    echo -e "${RED}FEHLER: Bitte aus dem deployment/ Verzeichnis ausführen!${NC}"
    echo "Erwartete Struktur:"
    echo "  ticketbot-webpanel-main/"
    echo "  ├── backend/server.py"
    echo "  ├── bot/bot.py"
    echo "  ├── frontend/"
    echo "  └── deployment/ ← Sie sind hier"
    exit 1
fi

echo -e "${GREEN}[1/6] Kopiere Backend Dateien...${NC}"
cp ../../backend/server.py "$WEB_DIR/"
if [ -f "../../backend/requirements.txt" ]; then
    cp ../../backend/requirements.txt "$WEB_DIR/"
fi
echo -e "${GREEN}✓ Backend Dateien kopiert${NC}"

echo -e "${GREEN}[2/6] Kopiere Bot Dateien...${NC}"
cp ../../bot/bot.py "$BOT_DIR/"
if [ -f "../../bot/requirements.txt" ]; then
    cp ../../bot/requirements.txt "$BOT_DIR/"
fi
echo -e "${GREEN}✓ Bot Dateien kopiert${NC}"

echo -e "${GREEN}[3/6] Installiere Python Dependencies...${NC}"
source "$VENV_DIR/bin/activate"
if [ -f "$WEB_DIR/requirements.txt" ]; then
    pip install -q -r "$WEB_DIR/requirements.txt"
fi
echo -e "${GREEN}✓ Dependencies installiert${NC}"

echo -e "${GREEN}[4/6] Baue Frontend...${NC}"

# Node.js prüfen/installieren
if ! command -v node &> /dev/null; then
    echo "Node.js nicht gefunden, installiere..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
fi

# Yarn prüfen/installieren
if ! command -v yarn &> /dev/null; then
    echo "Yarn nicht gefunden, installiere..."
    npm install -g yarn
fi

# Frontend bauen
cd ../../frontend

echo "Installiere Frontend Dependencies..."
yarn install

echo "Erstelle Frontend .env..."
cat > .env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
EOF

echo "Baue Frontend (das kann einige Minuten dauern)..."
yarn build

echo "Kopiere Build zum Web-Server..."
mkdir -p "$WEB_DIR/static"
cp -r build/* "$WEB_DIR/static/"

echo -e "${GREEN}✓ Frontend gebaut und kopiert${NC}"

echo -e "${GREEN}[5/6] Konfiguriere Services...${NC}"

# Backend requirements prüfen
cd "$WEB_DIR"
source "$VENV_DIR/bin/activate"

echo "Teste Backend Import..."
python3 -c "import fastapi, motor, bcrypt, jwt" 2>/dev/null && echo -e "${GREEN}✓ Backend Dependencies OK${NC}" || {
    echo -e "${YELLOW}Installiere fehlende Dependencies...${NC}"
    pip install -q fastapi uvicorn motor pymongo bcrypt pyjwt python-jose python-dotenv
}

# Services neu laden
supervisorctl reread
supervisorctl update

echo -e "${GREEN}[6/6] Starte Services...${NC}"

# Nur Backend starten (Bot braucht noch Konfiguration)
supervisorctl start ccx-webpanel

sleep 3

# Status prüfen
if supervisorctl status ccx-webpanel | grep -q "RUNNING"; then
    echo -e "${GREEN}✓ Backend läuft${NC}"
else
    echo -e "${RED}✗ Backend läuft NICHT${NC}"
    echo "Prüfe Logs:"
    tail -n 20 "$INSTALL_DIR/logs/webpanel.err.log"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Abgeschlossen!                  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo -e "${CYAN}📋 NÄCHSTE SCHRITTE:${NC}"
echo ""
echo -e "${YELLOW}1. Backend Konfiguration:${NC}"
echo "   nano $WEB_DIR/.env"
echo "   → DISCORD_BOT_TOKEN setzen"
echo "   → Discord IDs anpassen"
echo ""

echo -e "${YELLOW}2. Bot Konfiguration:${NC}"
echo "   nano $BOT_DIR/config.env"
echo "   → DISCORD_BOT_TOKEN setzen"
echo "   → Discord IDs anpassen"
echo ""

echo -e "${YELLOW}3. Services neu starten:${NC}"
echo "   supervisorctl restart ccx-webpanel"
echo "   supervisorctl start ccx-bot"
echo ""

echo -e "${YELLOW}4. System testen:${NC}"
echo "   $INSTALL_DIR/healthcheck.sh"
echo "   curl http://localhost:8001/api/health"
echo "   https://$DOMAIN/login"
echo ""

echo -e "${GREEN}Standard Login:${NC}"
echo "  Username: admin"
echo "  Password: admin123"
echo ""

echo -e "${CYAN}🔍 TROUBLESHOOTING:${NC}"
echo "  Backend Logs: tail -f $INSTALL_DIR/logs/webpanel.err.log"
echo "  Bot Logs: tail -f $INSTALL_DIR/logs/bot.err.log"
echo "  Health Check: $INSTALL_DIR/healthcheck.sh"
echo ""

# Finaler Health Check
echo -e "${CYAN}Führe Health Check aus...${NC}"
echo ""
$INSTALL_DIR/healthcheck.sh

echo ""
echo -e "${GREEN}✓ Post-Installation Setup abgeschlossen!${NC}"
