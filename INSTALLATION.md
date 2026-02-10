# Control Center X Ultra - Installationsanleitung

## Inhaltsverzeichnis

1. [Systemvoraussetzungen](#1-systemvoraussetzungen)
2. [Vorbereitung](#2-vorbereitung)
3. [Installation](#3-installation)
4. [Konfiguration](#4-konfiguration)
5. [Frontend bauen](#5-frontend-bauen)
6. [Services starten](#6-services-starten)
7. [Discord Bot einrichten](#7-discord-bot-einrichten)
8. [Testen](#8-testen)
9. [Fehlerbehebung](#9-fehlerbehebung)

---

## 1. Systemvoraussetzungen

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| OS | Debian 11/12, Ubuntu 22.04+ | Debian 12 |
| RAM | 2 GB | 4 GB |
| Disk | 10 GB | 20 GB |
| CPU | 1 Core | 2 Cores |

**Benötigte Software (wird automatisch installiert):**
- Python 3.10+
- Node.js 18+ und Yarn
- MongoDB 7.0
- Redis
- Nginx
- Certbot (SSL)

---

## 2. Vorbereitung

### 2.1 DNS konfigurieren

Erstellen Sie einen A-Record für Ihre Domain:

```
ticket.ihre-domain.de  ->  IP-Adresse-Ihres-Servers
```

### 2.2 Discord Bot erstellen

1. Gehen Sie zu https://discord.com/developers/applications
2. Klicken Sie "New Application"
3. Name: z.B. "Ticket Bot"
4. Im Tab "Bot":
   - Klicken Sie "Reset Token" und **kopieren Sie den Token** (nur einmal sichtbar!)
   - Aktivieren Sie unter "Privileged Gateway Intents":
     - PRESENCE INTENT
     - SERVER MEMBERS INTENT
     - MESSAGE CONTENT INTENT
5. Im Tab "OAuth2" -> "URL Generator":
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Administrator`
   - Kopieren Sie die URL und laden Sie den Bot auf Ihren Server ein

### 2.3 Discord IDs ermitteln

Aktivieren Sie in Discord: Einstellungen -> Erweitert -> Entwicklermodus

Dann Rechtsklick -> "ID kopieren" für:
- **Server (Guild) ID**: Rechtsklick auf Server-Icon
- **Ticket-Kanal ID**: Rechtsklick auf den Kanal für das Ticket-Panel
- **Transcript-Log-Kanal ID**: Rechtsklick auf den Kanal für Transcripts
- **Ticket-Kategorie ID**: Rechtsklick auf die Kategorie für Ticket-Channels
- **Support-Rollen IDs**: Rechtsklick auf jede Support-Rolle

---

## 3. Installation

### 3.1 Projekt auf Server hochladen

```bash
# Option 1: Git Clone (wenn Repository verfügbar)
cd /opt
git clone https://github.com/ihr-repo/control-center-x-ultra.git ccx-ultra-source
cd ccx-ultra-source

# Option 2: Archiv hochladen
# Laden Sie Control-Center-X-Ultra-FINAL.tar.gz auf den Server
cd /opt
tar -xzvf Control-Center-X-Ultra-FINAL.tar.gz -C ccx-ultra-source
cd ccx-ultra-source
```

### 3.2 Installationsskript anpassen

Bearbeiten Sie die Variablen am Anfang von `deployment/install_v2.sh`:

```bash
nano deployment/install_v2.sh
```

Ändern Sie diese Werte:

```bash
DOMAIN="ticket.ihre-domain.de"        # Ihre Domain
ADMIN_EMAIL="admin@ihre-domain.de"    # Ihre E-Mail für SSL-Zertifikat
```

### 3.3 Installation ausführen

```bash
chmod +x deployment/install_v2.sh
sudo bash deployment/install_v2.sh
```

Das Skript installiert automatisch:
- MongoDB, Redis, Nginx
- Python Virtual Environment
- Alle Python-Dependencies
- SSL-Zertifikat (wenn DNS korrekt)
- Supervisor-Services
- Firewall-Regeln

---

## 4. Konfiguration

### 4.1 Backend konfigurieren

```bash
nano /opt/ccx-ultra/web/.env
```

**Wichtige Einstellungen:**

```env
# MongoDB (normalerweise nicht ändern)
MONGO_URL=mongodb://localhost:27017
DB_NAME=ccx_ultra

# JWT Secret (automatisch generiert, NICHT ändern)
JWT_SECRET=ihr-generierter-schluessel

# CORS (Ihre Domain eintragen)
CORS_ORIGINS=https://ticket.ihre-domain.de

# Discord Bot Token (WICHTIG!)
DISCORD_BOT_TOKEN=ihr-discord-bot-token

# Discord IDs (WICHTIG!)
DISCORD_GUILD_ID=123456789012345678
TICKET_CHANNEL_ID=123456789012345678
TRANSCRIPT_LOG_CHANNEL_ID=123456789012345678
TICKET_CATEGORY_ID=123456789012345678

# Support Rollen (komma-getrennt)
SUPPORT_ROLE_IDS=123456789012345678,234567890123456789
```

### 4.2 Bot konfigurieren

```bash
nano /opt/ccx-ultra/bot/config.env
```

**Gleiche Discord-Werte wie oben:**

```env
DISCORD_BOT_TOKEN=ihr-discord-bot-token
DISCORD_GUILD_ID=123456789012345678
TICKET_CHANNEL_ID=123456789012345678
TRANSCRIPT_LOG_CHANNEL_ID=123456789012345678
TICKET_CATEGORY_ID=123456789012345678
SUPPORT_ROLE_IDS=123456789012345678,234567890123456789

# API URL (normalerweise nicht ändern)
API_URL=http://localhost:8001/api

# Ticket-Einstellungen
MAX_TICKETS_PER_USER=3
SLA_FIRST_RESPONSE_MINUTES=30
AUTO_CLOSE_INACTIVE_HOURS=48
```

### 4.3 Dateien kopieren

```bash
# Backend
cp backend/server.py /opt/ccx-ultra/web/

# Bot
cp bot/bot.py /opt/ccx-ultra/bot/
cp bot/requirements.txt /opt/ccx-ultra/bot/
```

---

## 5. Frontend bauen

### 5.1 Node.js installieren (falls nicht vorhanden)

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
npm install -g yarn
```

### 5.2 Frontend bauen

```bash
# In das Frontend-Verzeichnis wechseln
cd /opt/ccx-ultra-source/frontend

# .env Datei erstellen
echo "REACT_APP_BACKEND_URL=https://ticket.ihre-domain.de" > .env

# Dependencies installieren
yarn install

# Production Build erstellen
yarn build

# Build nach Nginx-Verzeichnis kopieren
mkdir -p /opt/ccx-ultra/web/static
cp -r build/* /opt/ccx-ultra/web/static/
```

### 5.3 Nginx neu laden

```bash
nginx -t && systemctl reload nginx
```

---

## 6. Services starten

### 6.1 Backend starten

```bash
supervisorctl start ccx-webpanel
```

### 6.2 Backend prüfen

```bash
# Status prüfen
supervisorctl status ccx-webpanel

# Sollte zeigen: ccx-webpanel RUNNING

# API testen
curl http://localhost:8001/api/health
# Sollte zeigen: {"status":"ok","service":"Control Center X Ultra"}
```

### 6.3 Bot starten (nach Konfiguration!)

```bash
supervisorctl start ccx-bot
```

### 6.4 Alle Services prüfen

```bash
supervisorctl status
```

---

## 7. Discord Bot einrichten

### 7.1 Bot-Befehle synchronisieren

Nach dem Start des Bots werden die Slash-Commands automatisch synchronisiert.

### 7.2 Ticket-Panel erstellen

In Discord (als Admin) im gewünschten Kanal:

```
/ticket-panel
```

Dies erstellt das Panel mit den Sprach-Buttons.

---

## 8. Testen

### 8.1 Web-Panel testen

Öffnen Sie im Browser:

```
https://ticket.ihre-domain.de/login
```

Login mit:
- **Benutzer:** admin
- **Passwort:** admin123

**WICHTIG:** Ändern Sie das Passwort nach dem ersten Login!

### 8.2 Health Check ausführen

```bash
/opt/ccx-ultra/healthcheck.sh
```

### 8.3 Discord Bot testen

1. Klicken Sie auf einen Sprach-Button im Ticket-Panel
2. Füllen Sie das Formular aus
3. Ein neuer Ticket-Channel sollte erstellt werden

---

## 9. Fehlerbehebung

### Problem: Backend startet nicht

```bash
# Logs prüfen
tail -f /opt/ccx-ultra/logs/webpanel.err.log

# Häufige Ursachen:
# 1. .env Datei fehlt oder ist fehlerhaft
# 2. MongoDB läuft nicht: systemctl status mongod
# 3. Port 8001 belegt: fuser -k 8001/tcp
```

### Problem: Frontend zeigt 404

```bash
# Prüfen ob Build existiert
ls -la /opt/ccx-ultra/web/static/

# Falls leer: Frontend neu bauen (siehe Schritt 5)

# Nginx Konfiguration prüfen
nginx -t
```

### Problem: Bot startet nicht

```bash
# Logs prüfen
tail -f /opt/ccx-ultra/logs/bot.err.log

# Häufige Ursachen:
# 1. Bot Token falsch
# 2. Discord IDs falsch
# 3. Bot nicht auf Server eingeladen
```

### Problem: SSL Zertifikat fehlt

```bash
# Certbot manuell ausführen
certbot --nginx -d ticket.ihre-domain.de
```

### Problem: Login funktioniert nicht

```bash
# Backend-Logs prüfen
tail -f /opt/ccx-ultra/logs/webpanel.err.log

# MongoDB Verbindung prüfen
mongosh --eval "db.adminCommand('ping')"

# Admin-Benutzer manuell erstellen
mongosh ccx_ultra --eval "db.panel_users.insertOne({id:'admin-id',username:'admin',password_hash:'\$2b\$12\$...',role:'admin',created_at:new Date().toISOString()})"
```

### Nützliche Befehle

```bash
# Alle Services neu starten
supervisorctl restart all

# Einzelnen Service neu starten
supervisorctl restart ccx-webpanel
supervisorctl restart ccx-bot

# Logs live anzeigen
tail -f /opt/ccx-ultra/logs/webpanel.err.log
tail -f /opt/ccx-ultra/logs/bot.err.log

# MongoDB Status
systemctl status mongod

# Nginx Status und Test
systemctl status nginx
nginx -t

# Port-Belegung prüfen
netstat -tlnp | grep -E "(8001|27017|80|443)"

# Backup manuell erstellen
/opt/ccx-ultra/backup.sh
```

---

## Anhang: Verzeichnisstruktur

```
/opt/ccx-ultra/
├── web/                    # Backend
│   ├── server.py           # FastAPI Application
│   ├── .env                # Konfiguration
│   └── static/             # Frontend Build
│       ├── index.html
│       └── static/
│           ├── js/
│           └── css/
├── bot/                    # Discord Bot
│   ├── bot.py
│   └── config.env
├── venv/                   # Python Virtual Environment
├── logs/                   # Log-Dateien
│   ├── webpanel.err.log
│   ├── webpanel.out.log
│   ├── bot.err.log
│   └── bot.out.log
├── transcripts/            # Ticket-Transcripts
├── backups/                # Automatische Backups
├── healthcheck.sh          # System Health Check
└── backup.sh               # Backup Script
```

---

## Support

Bei Problemen:
1. Health Check ausführen: `/opt/ccx-ultra/healthcheck.sh`
2. Logs prüfen: `tail -f /opt/ccx-ultra/logs/*.err.log`
3. Diese Anleitung erneut durchgehen
