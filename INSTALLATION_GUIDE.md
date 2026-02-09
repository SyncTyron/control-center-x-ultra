# Control Center X Ultra - Vollständige VPS Installationsanleitung

## 🎯 Was Sie bekommen
Ein vollständig funktionierendes Enterprise Discord Ticket System mit:
- Discord Bot (Python 3.11+)
- Web Control Panel (FastAPI Backend + React Frontend)  
- MongoDB Datenbank
- Live Dashboard mit Echtzeit-Updates
- HTTPS mit automatischem SSL
- Automatische Backups

---

## ⚠️ WICHTIGE VORAUSSETZUNGEN

### 1. VPS Anforderungen
- **OS**: Debian 12 (Bookworm)
- **RAM**: Minimum 2GB (4GB empfohlen)
- **CPU**: 2 Cores empfohlen
- **Disk**: 20GB freier Speicher
- **Root Zugriff**: Erforderlich

### 2. Domain Setup
- Domain muss auf Ihren VPS zeigen (A Record)
- Beispiel: `ticket.armesa.de` → Ihre VPS IP
- DNS Propagierung abwarten (bis zu 24h)

### 3. Discord Bot Setup
Gehen Sie zu https://discord.com/developers/applications

1. **Neue Application erstellen**
2. **Bot Tab → Add Bot**
3. **Bot Token kopieren** (wird später benötigt)
4. **Privileged Gateway Intents aktivieren:**
   - ✅ PRESENCE INTENT
   - ✅ SERVER MEMBERS INTENT
   - ✅ MESSAGE CONTENT INTENT

5. **OAuth2 → URL Generator:**
   - Scopes: `bot`, `applications.commands`
   - Permissions: `Administrator` (oder spezifisch: Manage Channels, Send Messages, etc.)
   
6. **Bot zum Server einladen**

7. **Discord IDs sammeln:**
   - Server ID (Guild ID)
   - Support Rollen IDs
   - Channel IDs für Tickets und Logs
   
   *Tipp: Developer Mode in Discord aktivieren → Rechtsklick → Copy ID*

---

## 📦 INSTALLATION

### Schritt 1: Dateien auf VPS hochladen

```bash
# Mit SSH verbinden
ssh root@YOUR_VPS_IP

# Arbeitsverzeichnis erstellen
mkdir -p /root/ccx-install
cd /root/ccx-install

# Dateien hochladen (von Ihrem lokalen PC)
# Option A: Mit SCP
scp -r ./ticketbot-webpanel-main root@YOUR_VPS_IP:/root/ccx-install/

# Option B: Mit Git (falls Repository vorhanden)
git clone YOUR_REPO_URL
cd ticketbot-webpanel-main
```

### Schritt 2: Installation ausführen

```bash
cd /root/ccx-install/ticketbot-webpanel-main/deployment
chmod +x install.sh
bash install.sh
```

**⏱ Dauer: 10-15 Minuten**

### Schritt 3: Dateien kopieren

```bash
# Backend
cp /root/ccx-install/ticketbot-webpanel-main/backend/server.py /opt/ccx-ultra/web/

# Bot
cp /root/ccx-install/ticketbot-webpanel-main/bot/bot.py /opt/ccx-ultra/bot/

# Backend Requirements
cp /root/ccx-install/ticketbot-webpanel-main/backend/requirements.txt /opt/ccx-ultra/web/
```

### Schritt 4: Python Dependencies installieren

```bash
source /opt/ccx-ultra/venv/bin/activate
pip install -r /opt/ccx-ultra/web/requirements.txt
```

### Schritt 5: Konfiguration anpassen

#### Backend .env bearbeiten
```bash
nano /opt/ccx-ultra/web/.env
```

**Ändern Sie:**
```env
DISCORD_BOT_TOKEN=IHR_BOT_TOKEN_HIER
DISCORD_GUILD_ID=1407623359365120090
SUPPORT_ROLE_IDS=368510579511656449,372850494445453314,1006197315566051388
```

#### Bot config.env bearbeiten
```bash
nano /opt/ccx-ultra/bot/config.env
```

**Ändern Sie:**
```env
DISCORD_BOT_TOKEN=IHR_BOT_TOKEN_HIER
DISCORD_GUILD_ID=1407623359365120090
TICKET_CHANNEL_ID=1469120567532847225
TRANSCRIPT_LOG_CHANNEL_ID=1470212303260483817
TICKET_CATEGORY_ID=1469120434115969064
SUPPORT_ROLE_IDS=368510579511656449,372850494445453314,1006197315566051388
```

### Schritt 6: Frontend bauen

```bash
cd /root/ccx-install/ticketbot-webpanel-main/frontend

# Node.js & Yarn installieren (falls noch nicht vorhanden)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
npm install -g yarn

# Dependencies installieren
yarn install

# Frontend .env erstellen
cat > .env << 'EOF'
REACT_APP_BACKEND_URL=https://ticket.armesa.de
EOF

# Build erstellen
yarn build

# Build zu Web-Root kopieren
mkdir -p /opt/ccx-ultra/web/static
cp -r build/* /opt/ccx-ultra/web/static/
```

### Schritt 7: Services starten

```bash
# Supervisor neu laden
supervisorctl reread
supervisorctl update

# Alle Services starten
supervisorctl start all

# Status prüfen
supervisorctl status
```

**Erwartete Ausgabe:**
```
ccx-bot                          RUNNING   pid 12345, uptime 0:00:05
ccx-webpanel                     RUNNING   pid 12346, uptime 0:00:05
```

### Schritt 8: Testen

```bash
# Backend Health Check
curl http://localhost:8001/api/health

# Sollte zurückgeben:
# {"status":"ok","service":"Control Center X Ultra"}

# In Browser öffnen:
# https://ticket.armesa.de/login
```

**Standard Login:**
- Username: `admin`
- Password: `admin123`

---

## 🔍 PROBLEMLÖSUNG

### Problem: "404 Not Found" beim Login

**Ursache:** Backend läuft nicht oder Nginx leitet nicht korrekt weiter

**Lösung:**
```bash
# 1. Backend Status prüfen
supervisorctl status ccx-webpanel

# 2. Logs prüfen
tail -n 50 /opt/ccx-ultra/logs/webpanel.err.log

# 3. Backend neu starten
supervisorctl restart ccx-webpanel

# 4. Nginx Konfiguration prüfen
nginx -t

# 5. Port prüfen
netstat -tlnp | grep 8001
```

### Problem: Services starten nicht

```bash
# Detaillierte Logs anschauen
tail -f /opt/ccx-ultra/logs/*.log

# Häufige Fehler:
# - Fehlender Discord Bot Token → .env prüfen
# - MongoDB läuft nicht → systemctl status mongod
# - Port bereits belegt → netstat -tlnp | grep 8001
```

### Problem: Nginx 502 Bad Gateway

```bash
# Backend läuft?
supervisorctl status ccx-webpanel

# Backend manuell testen
cd /opt/ccx-ultra/web
source /opt/ccx-ultra/venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001

# Wenn Fehler → Dependencies fehlen:
pip install -r requirements.txt
```

### Problem: Bot verbindet nicht

```bash
# Bot Logs prüfen
tail -f /opt/ccx-ultra/logs/bot.err.log

# Häufige Fehler:
# - Ungültiger Token
# - Intents nicht aktiviert (Discord Developer Portal)
# - Falsche Guild ID
```

### Problem: Frontend zeigt weiße Seite

```bash
# Browser Console öffnen (F12)
# Fehler prüfen

# Häufige Ursachen:
# 1. REACT_APP_BACKEND_URL falsch
# 2. Build nicht korrekt kopiert
# 3. Nginx serviert nicht die richtige Datei

# Fix: Frontend neu bauen
cd /root/ccx-install/ticketbot-webpanel-main/frontend
rm -rf build node_modules
yarn install
yarn build
cp -r build/* /opt/ccx-ultra/web/static/
```

---

## 🔧 NÜTZLICHE BEFEHLE

### Services verwalten
```bash
# Status aller Services
supervisorctl status

# Service neu starten
supervisorctl restart ccx-webpanel
supervisorctl restart ccx-bot

# Alle neu starten
supervisorctl restart all

# Logs live ansehen
tail -f /opt/ccx-ultra/logs/webpanel.out.log
tail -f /opt/ccx-ultra/logs/bot.err.log
```

### Datenbank
```bash
# MongoDB Shell öffnen
mongosh

use ccx_ultra

# Admin User anzeigen
db.panel_users.find()

# Tickets anzeigen
db.tickets.find().limit(5)

# Admin Passwort zurücksetzen
# In Python:
python3 << 'EOF'
import bcrypt
password = "neuesPasswort123"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"Neuer Hash: {hashed}")
EOF

# Dann in MongoDB:
db.panel_users.updateOne(
  {username: "admin"},
  {$set: {password_hash: "NEUER_HASH_HIER"}}
)
```

### Backup & Restore
```bash
# Manuelles Backup
/opt/ccx-ultra/backup.sh

# Backups anzeigen
ls -lh /opt/ccx-ultra/backups/

# Restore
mongorestore --db ccx_ultra /opt/ccx-ultra/backups/20250209_030000/mongodb/ccx_ultra/
```

### Nginx
```bash
# Konfiguration testen
nginx -t

# Nginx neu laden
systemctl reload nginx

# Nginx neu starten
systemctl restart nginx

# Logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

### Updates
```bash
# Code aktualisieren
cd /root/ccx-install/ticketbot-webpanel-main
git pull  # falls Git verwendet wird

# Backend aktualisieren
cp backend/server.py /opt/ccx-ultra/web/
supervisorctl restart ccx-webpanel

# Bot aktualisieren
cp bot/bot.py /opt/ccx-ultra/bot/
supervisorctl restart ccx-bot

# Frontend aktualisieren
cd frontend
yarn build
cp -r build/* /opt/ccx-ultra/web/static/
```

---

## 📊 MONITORING

### System Status prüfen
```bash
# Alle Services
supervisorctl status

# Ressourcen
htop
df -h
free -h

# Ports
netstat -tlnp | grep -E "(8001|27017|6379)"

# MongoDB
systemctl status mongod

# Nginx
systemctl status nginx
```

### Performance Optimierung
```bash
# MongoDB Indexe prüfen
mongosh ccx_ultra
db.tickets.getIndexes()

# Supervisor Worker erhöhen (für mehr Traffic)
nano /etc/supervisor/conf.d/ccx-webpanel.conf
# Ändern: --workers 4
supervisorctl restart ccx-webpanel
```

---

## 🔐 SICHERHEIT

### Firewall Status
```bash
ufw status verbose
```

### SSL Zertifikat erneuern
```bash
# Automatisch via Cron (bereits eingerichtet)
# Manuell testen:
certbot renew --dry-run

# Manuell erneuern:
certbot renew
systemctl reload nginx
```

### Passwörter ändern
```bash
# Im Web Panel: Settings → Change Password
# Oder via MongoDB (siehe oben)
```

---

## 📞 SUPPORT & DEBUGGING

### Vollständiger Health Check
```bash
#!/bin/bash
echo "=== CCX Ultra System Check ==="
echo ""
echo "1. Services:"
supervisorctl status
echo ""
echo "2. Ports:"
netstat -tlnp | grep -E "(8001|27017|6379|80|443)"
echo ""
echo "3. MongoDB:"
systemctl status mongod | grep Active
echo ""
echo "4. Nginx:"
nginx -t
systemctl status nginx | grep Active
echo ""
echo "5. Disk Space:"
df -h | grep -E "(Filesystem|/dev/)"
echo ""
echo "6. Recent Errors (last 10 lines):"
tail -n 10 /opt/ccx-ultra/logs/webpanel.err.log
```

### Debug Mode aktivieren
```bash
# Backend mit Debug Logs
cd /opt/ccx-ultra/web
source /opt/ccx-ultra/venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload --log-level debug
```

---

## ✅ POST-INSTALLATION CHECKLIST

- [ ] Domain zeigt auf VPS IP
- [ ] SSL Zertifikat installiert (https:// funktioniert)
- [ ] Services laufen (supervisorctl status)
- [ ] Backend antwortet (curl http://localhost:8001/api/health)
- [ ] Frontend erreichbar (https://ticket.armesa.de)
- [ ] Login funktioniert (admin/admin123)
- [ ] Discord Bot online im Server
- [ ] Ticket System testen (/ticket-panel Command)
- [ ] Firewall aktiv (ufw status)
- [ ] Automatische Backups aktiv (crontab -l)

---

## 🎉 FERTIG!

Ihr Control Center X Ultra System sollte nun vollständig funktionieren!

**Zugriff:**
- Web Panel: https://ticket.armesa.de
- Login: admin / admin123 (bitte ändern!)

**Nächste Schritte:**
1. Passwort ändern
2. Weitere Support User anlegen
3. Ticket Panel im Discord erstellen: `/ticket-panel`
4. System testen

**Bei Problemen:**
1. Logs prüfen: `/opt/ccx-ultra/logs/`
2. Health Check Script ausführen (siehe oben)
3. Services neu starten: `supervisorctl restart all`

---

*Control Center X Ultra v1.0 - Enterprise Discord Ticket System*
