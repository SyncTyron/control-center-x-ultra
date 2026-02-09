# 📋 Control Center X Ultra - Quick Reference Card

## 🚀 3-SCHRITTE INSTALLATION (Leerer VPS)

### 1️⃣ DATEI HOCHLADEN (Von Ihrem PC)
```bash
scp ccx-ultra-fixed-20260209.tar.gz root@IHRE_VPS_IP:/root/
```

### 2️⃣ AUF VPS INSTALLIEREN (via SSH)
```bash
cd /root
tar -xzf ccx-ultra-fixed-20260209.tar.gz
cd ccx-fixed/deployment
chmod +x *.sh
bash install_v2.sh          # 10-15 Min
bash post_install_setup.sh  # 5-10 Min
```

### 3️⃣ KONFIGURIEREN & STARTEN
```bash
nano /opt/ccx-ultra/web/.env        # Discord Bot Token
nano /opt/ccx-ultra/bot/config.env  # Discord Bot Token
supervisorctl restart all
bash troubleshoot.sh
```

**LOGIN:** https://ticket.armesa.de → admin / admin123

---

## 🔑 WICHTIGE DISCORD SETUP SCHRITTE

### Bot Token holen:
1. https://discord.com/developers/applications
2. Bot Tab → Reset Token → Kopieren

### Privileged Intents aktivieren:
- ✅ PRESENCE INTENT
- ✅ SERVER MEMBERS INTENT  
- ✅ MESSAGE CONTENT INTENT

### Discord IDs sammeln:
```
Developer Mode aktivieren → Rechtsklick → ID kopieren

Server (Guild) ID: _________________
Support Rolle 1: _________________
Support Rolle 2: _________________
Support Rolle 3: _________________
Ticket Channel: _________________
Log Channel: _________________
Category: _________________
```

---

## 🛠️ WICHTIGSTE BEFEHLE

### Services verwalten
```bash
supervisorctl status              # Status anzeigen
supervisorctl restart all         # Alle neu starten
supervisorctl restart ccx-webpanel  # Backend neu starten
supervisorctl restart ccx-bot     # Bot neu starten
```

### Logs ansehen
```bash
tail -f /opt/ccx-ultra/logs/webpanel.err.log  # Backend Errors
tail -f /opt/ccx-ultra/logs/bot.err.log       # Bot Errors
tail -f /var/log/nginx/error.log              # Nginx Errors
```

### System Status
```bash
/opt/ccx-ultra/healthcheck.sh     # Health Check
bash troubleshoot.sh              # Vollständige Diagnose
```

### Backend API testen
```bash
curl http://localhost:8001/api/health
# Sollte: {"status":"ok","service":"Control Center X Ultra"}
```

---

## 🐛 SCHNELLE PROBLEMLÖSUNG

### ❌ Problem: 404 Not Found beim Login
```bash
supervisorctl restart ccx-webpanel
sleep 3
curl http://localhost:8001/api/health
bash troubleshoot.sh
```

### ❌ Problem: Bot offline
```bash
tail -f /opt/ccx-ultra/logs/bot.err.log
# Token prüfen:
grep DISCORD_BOT_TOKEN /opt/ccx-ultra/bot/config.env
# Intents prüfen: Discord Developer Portal
supervisorctl restart ccx-bot
```

### ❌ Problem: Services starten nicht
```bash
supervisorctl status
tail -f /opt/ccx-ultra/logs/*.log
# Dependencies installieren:
source /opt/ccx-ultra/venv/bin/activate
pip install -r /opt/ccx-ultra/web/requirements.txt
supervisorctl restart all
```

### ❌ Problem: SSL fehlt
```bash
# DNS prüfen:
dig ticket.armesa.de
# Certbot:
certbot --nginx -d ticket.armesa.de
systemctl reload nginx
```

---

## 📁 WICHTIGE DATEIEN & VERZEICHNISSE

```
/opt/ccx-ultra/
├── web/
│   ├── server.py           # Backend Code
│   ├── .env                # Backend Konfiguration ⚙️
│   └── static/             # Frontend Build
├── bot/
│   ├── bot.py              # Bot Code
│   └── config.env          # Bot Konfiguration ⚙️
├── logs/                   # Alle Logs 📝
├── backups/                # Automatische Backups 💾
├── healthcheck.sh          # System Check ✅
└── backup.sh               # Manuelles Backup 💾

/etc/nginx/sites-available/ticket.armesa.de  # Nginx Config
/etc/supervisor/conf.d/ccx-*.conf            # Services
```

---

## 🔐 KONFIGURATIONSDATEIEN

### Backend .env (`/opt/ccx-ultra/web/.env`)
```bash
MONGO_URL=mongodb://localhost:27017
DB_NAME=ccx_ultra
JWT_SECRET=auto_generated
CORS_ORIGINS=https://ticket.armesa.de
DISCORD_BOT_TOKEN=YOUR_TOKEN_HERE          # ← ÄNDERN
DISCORD_GUILD_ID=YOUR_GUILD_ID             # ← ÄNDERN
SUPPORT_ROLE_IDS=ID1,ID2,ID3               # ← ÄNDERN
```

### Bot config.env (`/opt/ccx-ultra/bot/config.env`)
```bash
DISCORD_BOT_TOKEN=YOUR_TOKEN_HERE          # ← ÄNDERN
DISCORD_GUILD_ID=YOUR_GUILD_ID             # ← ÄNDERN
TICKET_CHANNEL_ID=YOUR_CHANNEL_ID          # ← ÄNDERN
TRANSCRIPT_LOG_CHANNEL_ID=YOUR_LOG_ID      # ← ÄNDERN
TICKET_CATEGORY_ID=YOUR_CATEGORY_ID        # ← ÄNDERN
SUPPORT_ROLE_IDS=ID1,ID2,ID3               # ← ÄNDERN
API_URL=http://localhost:8001/api
```

---

## 📊 SERVICE PORTS

| Service | Port | Check |
|---------|------|-------|
| Backend | 8001 | `netstat -tlnp \| grep 8001` |
| MongoDB | 27017 | `systemctl status mongod` |
| Redis | 6379 | `systemctl status redis-server` |
| Nginx | 80, 443 | `systemctl status nginx` |

---

## 🆘 VOLLSTÄNDIGE DIAGNOSE

```bash
cd /root/ccx-fixed/deployment
bash troubleshoot.sh
```

**Prüft automatisch:**
- ✅ Alle Services (MongoDB, Redis, Nginx, Backend, Bot)
- ✅ Alle Ports (8001, 27017, 6379, 80, 443)
- ✅ DNS & SSL
- ✅ Backend API
- ✅ Konfiguration
- ✅ Logs
- ✅ Gibt konkrete Lösungsvorschläge

---

## 🔄 UPDATES DURCHFÜHREN

```bash
# Backend aktualisieren
cp neue/server.py /opt/ccx-ultra/web/
supervisorctl restart ccx-webpanel

# Bot aktualisieren
cp neue/bot.py /opt/ccx-ultra/bot/
supervisorctl restart ccx-bot

# Frontend aktualisieren
cd frontend/
yarn build
cp -r build/* /opt/ccx-ultra/web/static/
systemctl reload nginx
```

---

## 💾 BACKUP & RESTORE

```bash
# Manuelles Backup
/opt/ccx-ultra/backup.sh

# Backups anzeigen
ls -lh /opt/ccx-ultra/backups/

# Restore
mongorestore --db ccx_ultra /opt/ccx-ultra/backups/20250209_030000/mongodb/ccx_ultra/
```

**Automatische Backups:** Täglich um 03:00 Uhr (crontab)

---

## 📱 ZUGRIFFE

| Was | URL/Info |
|-----|----------|
| **Web Panel** | https://ticket.armesa.de |
| **Login** | admin / admin123 |
| **Discord Command** | `/ticket-panel` |
| **Backend API** | https://ticket.armesa.de/api/health |
| **Discord Dev Portal** | https://discord.com/developers/applications |

---

## ✅ POST-INSTALLATION CHECKLIST

- [ ] DNS zeigt auf VPS (`dig ticket.armesa.de`)
- [ ] SSL aktiv (`https://ticket.armesa.de`)
- [ ] Services laufen (`supervisorctl status`)
- [ ] Backend API ok (`curl http://localhost:8001/api/health`)
- [ ] Login funktioniert (Browser)
- [ ] Bot ist online (Discord)
- [ ] Ticket Panel erstellt (`/ticket-panel`)
- [ ] Test-Ticket funktioniert
- [ ] Admin Passwort geändert

---

## 📚 VOLLSTÄNDIGE DOKUMENTATION

Alle Details in:
- `INSTALLATION_VON_NULL.md` - Komplette Anleitung
- `INSTALLATION_GUIDE.md` - Detaillierte Dokumentation
- `QUICKSTART.md` - Schnellstart
- `PROBLEM_SOLUTION_ANALYSIS.md` - Technische Analyse

---

## 🎯 TYPISCHER ABLAUF BEI PROBLEMEN

```
1. Problem bemerkt (z.B. Login geht nicht)
       ↓
2. Troubleshoot ausführen
   bash troubleshoot.sh
       ↓
3. Zeigt was falsch ist + Lösung
       ↓
4. Lösung anwenden (z.B. Service neu starten)
       ↓
5. Erneut testen
       ↓
6. ✅ Problem behoben!
```

---

## ⚡ NOTFALL-RECOVERY

```bash
# Alles neu starten
systemctl restart mongod
systemctl restart redis-server
systemctl restart nginx
supervisorctl restart all

# System-Check
/opt/ccx-ultra/healthcheck.sh

# Vollständige Diagnose
bash /root/ccx-fixed/deployment/troubleshoot.sh

# Logs prüfen
tail -f /opt/ccx-ultra/logs/*.log
```

---

**Control Center X Ultra v2.0**  
*Quick Reference - Drucken Sie diese Seite für schnellen Zugriff aus*

Bei Problemen: `bash troubleshoot.sh` ausführen!
