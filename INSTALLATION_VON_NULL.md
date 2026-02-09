# 🚀 Control Center X Ultra - Installation von Null (Leerer VPS)

## ✅ Was Sie brauchen

- ✅ Leerer VPS mit Debian 12
- ✅ Root Zugriff (SSH)
- ✅ Domain: `ticket.armesa.de` (DNS zeigt auf VPS IP)
- ✅ Discord Bot Token (von Discord Developer Portal)
- ✅ Dieses Installations-Paket auf Ihrem lokalen PC

---

## 📋 SCHRITT-FÜR-SCHRITT ANLEITUNG

### Schritt 1: Dateien auf Ihren PC herunterladen

**Das Paket ist bereits in diesem Chat verfügbar!**

1. Laden Sie die Datei herunter:
   - `ccx-ultra-fixed-20260209.tar.gz` (4.9 MB)

2. Speichern Sie sie auf Ihrem PC, z.B.:
   - Windows: `C:\Users\IhrName\Downloads\`
   - Mac/Linux: `~/Downloads/`

---

### Schritt 2: Mit Ihrem VPS verbinden

#### Windows (mit PuTTY oder PowerShell)

**Option A: PowerShell (empfohlen)**
```powershell
# PowerShell öffnen (Win + X → Windows PowerShell)
ssh root@IHRE_VPS_IP

# Passwort eingeben wenn gefragt
```

**Option B: PuTTY**
1. PuTTY öffnen
2. Host Name: `IHRE_VPS_IP`
3. Port: `22`
4. Connection Type: `SSH`
5. Click "Open"
6. Login als: `root`
7. Passwort eingeben

#### Mac/Linux
```bash
# Terminal öffnen
ssh root@IHRE_VPS_IP

# Passwort eingeben
```

---

### Schritt 3: Dateien auf VPS hochladen

#### Option A: Mit SCP (empfohlen)

**Von Windows (PowerShell):**
```powershell
# Neues PowerShell Fenster öffnen (NICHT das SSH Fenster!)
cd C:\Users\IhrName\Downloads

# Datei hochladen
scp ccx-ultra-fixed-20260209.tar.gz root@IHRE_VPS_IP:/root/
```

**Von Mac/Linux:**
```bash
# Neues Terminal öffnen
cd ~/Downloads

# Datei hochladen
scp ccx-ultra-fixed-20260209.tar.gz root@IHRE_VPS_IP:/root/
```

#### Option B: Mit WinSCP (Windows, grafisch)

1. WinSCP herunterladen: https://winscp.net/
2. Verbindung erstellen:
   - Protokoll: SFTP
   - Host: IHRE_VPS_IP
   - Port: 22
   - Username: root
   - Passwort: Ihr VPS Passwort
3. Datei per Drag & Drop nach `/root/` ziehen

---

### Schritt 4: Installation auf VPS durchführen

**Zurück im SSH Fenster (auf dem VPS):**

```bash
# 1. Prüfen ob Datei angekommen ist
ls -lh /root/ccx-ultra-fixed-*.tar.gz

# Sollte zeigen:
# -rw-r--r-- 1 root root 4.9M ... ccx-ultra-fixed-20260209.tar.gz

# 2. Datei extrahieren
cd /root
tar -xzf ccx-ultra-fixed-20260209.tar.gz

# 3. In Verzeichnis wechseln
cd ccx-fixed/deployment

# 4. Scripts ausführbar machen
chmod +x install_v2.sh post_install_setup.sh troubleshoot.sh

# 5. WICHTIG: Prüfen Sie Ihre Konfiguration
nano install_v2.sh
# Suchen Sie nach diesen Zeilen (Zeile 22-29):
# DOMAIN="ticket.armesa.de"         ← Ihre Domain hier
# ADMIN_EMAIL="admin@armesa.de"     ← Ihre Email hier
# Ändern Sie falls nötig, dann speichern: Ctrl+O, Enter, Ctrl+X

# 6. Basis-Installation starten (10-15 Minuten)
bash install_v2.sh
```

**❗ WÄHREND DER INSTALLATION:**
- Lassen Sie das Terminal offen
- Es werden viele Pakete installiert
- Bei Certbot: Falls DNS noch nicht fertig, macht nichts (später manuell)
- Am Ende sehen Sie "Installation Abgeschlossen!"

---

### Schritt 5: Post-Installation (Dateien kopieren & Frontend bauen)

```bash
# Noch im selben Verzeichnis (/root/ccx-fixed/deployment)

# Post-Installation ausführen (5-10 Minuten)
bash post_install_setup.sh
```

**Was passiert:**
- ✅ Backend & Bot Dateien werden kopiert
- ✅ Python Dependencies installiert
- ✅ Node.js & Yarn installiert
- ✅ Frontend wird gebaut (dauert am längsten)
- ✅ Services werden gestartet

---

### Schritt 6: Discord Bot Token konfigurieren

#### 6a) Discord Bot Token holen

1. Gehen Sie zu: https://discord.com/developers/applications
2. Wählen Sie Ihre Application
3. Bot Tab → Click "Reset Token" → Token kopieren
4. **WICHTIG:** Token speichern! (wird nur einmal angezeigt)

#### 6b) Discord IDs sammeln

**Developer Mode aktivieren:**
1. Discord → Einstellungen → Erweitert
2. ✅ Entwicklermodus aktivieren

**IDs kopieren:**
- **Server ID:** Rechtsklick auf Server → ID kopieren
- **Support Rollen IDs:** Server → Rollen → Rechtsklick → ID kopieren (jede Rolle)
- **Channel IDs:** Rechtsklick auf Channels → ID kopieren

Notieren Sie:
```
Server (Guild) ID: _________________
Support Rolle 1 ID: _________________
Support Rolle 2 ID: _________________
Support Rolle 3 ID: _________________
Ticket Channel ID: _________________
Log Channel ID: _________________
Category ID: _________________
```

#### 6c) Backend konfigurieren

```bash
# Backend .env bearbeiten
nano /opt/ccx-ultra/web/.env

# Ändern Sie diese Zeilen:
DISCORD_BOT_TOKEN=IHREN_BOT_TOKEN_HIER_EINFÜGEN
DISCORD_GUILD_ID=IHRE_SERVER_ID
TICKET_CHANNEL_ID=IHRE_CHANNEL_ID
TRANSCRIPT_LOG_CHANNEL_ID=IHRE_LOG_CHANNEL_ID
TICKET_CATEGORY_ID=IHRE_CATEGORY_ID
SUPPORT_ROLE_IDS=ROLLE1_ID,ROLLE2_ID,ROLLE3_ID

# Speichern: Ctrl+O, Enter, Ctrl+X
```

#### 6d) Bot konfigurieren

```bash
# Bot config.env bearbeiten
nano /opt/ccx-ultra/bot/config.env

# Ändern Sie diese Zeilen (gleiche Werte wie oben):
DISCORD_BOT_TOKEN=IHREN_BOT_TOKEN_HIER_EINFÜGEN
DISCORD_GUILD_ID=IHRE_SERVER_ID
TICKET_CHANNEL_ID=IHRE_CHANNEL_ID
TRANSCRIPT_LOG_CHANNEL_ID=IHRE_LOG_CHANNEL_ID
TICKET_CATEGORY_ID=IHRE_CATEGORY_ID
SUPPORT_ROLE_IDS=ROLLE1_ID,ROLLE2_ID,ROLLE3_ID

# Speichern: Ctrl+O, Enter, Ctrl+X
```

---

### Schritt 7: Services starten

```bash
# Alle Services neu starten
supervisorctl restart all

# Warten 5 Sekunden
sleep 5

# Status prüfen
supervisorctl status

# Sollte zeigen:
# ccx-bot         RUNNING   pid 12345, uptime 0:00:05
# ccx-webpanel    RUNNING   pid 12346, uptime 0:00:05
```

**Falls "FATAL" oder "EXITED":**
```bash
# Logs prüfen
tail -n 30 /opt/ccx-ultra/logs/webpanel.err.log
tail -n 30 /opt/ccx-ultra/logs/bot.err.log
```

---

### Schritt 8: System testen

```bash
# Troubleshoot Script ausführen
bash troubleshoot.sh
```

**Was geprüft wird:**
- ✅ MongoDB läuft
- ✅ Redis läuft
- ✅ Nginx läuft
- ✅ Backend antwortet
- ✅ Bot läuft
- ✅ Ports offen
- ✅ DNS korrekt
- ✅ SSL aktiv

**Oder manuell testen:**
```bash
# Backend API Test
curl http://localhost:8001/api/health

# Sollte zurückgeben:
# {"status":"ok","service":"Control Center X Ultra"}
```

---

### Schritt 9: Im Browser testen

1. **Öffnen Sie:** `https://ticket.armesa.de/login`

2. **Login:**
   - Username: `admin`
   - Password: `admin123`

3. **Erwartetes Ergebnis:**
   - ✅ Login funktioniert
   - ✅ Redirect zum Dashboard
   - ✅ KPI Daten werden angezeigt
   - ✅ Keine Errors in Browser Console (F12)

**Falls "404 Not Found":**
```bash
# Zurück zum VPS Terminal
bash troubleshoot.sh

# Zeigt Ihnen was falsch ist und wie Sie es beheben
```

---

### Schritt 10: Discord Bot aktivieren

#### 10a) Bot zum Server einladen (falls noch nicht geschehen)

1. Discord Developer Portal: https://discord.com/developers/applications
2. Ihre Application auswählen
3. OAuth2 → URL Generator
4. Scopes: ✅ `bot` ✅ `applications.commands`
5. Bot Permissions: ✅ `Administrator` (oder spezifisch)
6. Generierte URL kopieren und im Browser öffnen
7. Server auswählen → Autorisieren

#### 10b) Privileged Intents aktivieren

1. Bot Tab → Privileged Gateway Intents
2. ✅ **PRESENCE INTENT** aktivieren
3. ✅ **SERVER MEMBERS INTENT** aktivieren
4. ✅ **MESSAGE CONTENT INTENT** aktivieren
5. Save Changes

#### 10c) Bot sollte jetzt online sein

- Prüfen Sie im Discord: Bot sollte "Online" sein
- Falls nicht:
  ```bash
  # Auf VPS:
  tail -f /opt/ccx-ultra/logs/bot.err.log
  # Zeigt Fehler an
  ```

#### 10d) Ticket Panel erstellen

**Im Discord Server als Admin:**
```
/ticket-panel
```

Der Bot erstellt ein Ticket Panel mit Deutsch/English Buttons.

---

## 🎉 FERTIG!

Ihr System ist jetzt vollständig installiert und funktioniert!

### ✅ Was Sie jetzt tun können:

1. **Login ändern:**
   - Im Web Panel → Settings → Change Password
   - Standard: admin / admin123

2. **Weitere User anlegen:**
   - Web Panel → Settings → Users → Add User
   - Rollen: admin, support, viewer

3. **Tickets testen:**
   - Im Discord auf Ticket Panel Button klicken
   - Ticket erstellen
   - Im Web Panel ansehen

4. **System überwachen:**
   ```bash
   # Health Check
   /opt/ccx-ultra/healthcheck.sh
   
   # Services Status
   supervisorctl status
   
   # Logs live ansehen
   tail -f /opt/ccx-ultra/logs/webpanel.out.log
   ```

---

## 🔧 HÄUFIGE PROBLEME

### Problem: "404 Not Found" beim Login

```bash
# Lösung 1: Troubleshoot ausführen
cd /root/ccx-fixed/deployment
bash troubleshoot.sh

# Lösung 2: Backend neu starten
supervisorctl restart ccx-webpanel
sleep 3
curl http://localhost:8001/api/health

# Lösung 3: Logs prüfen
tail -f /opt/ccx-ultra/logs/webpanel.err.log
```

### Problem: Bot ist offline

```bash
# Logs prüfen
tail -f /opt/ccx-ultra/logs/bot.err.log

# Häufige Ursachen:
# 1. Bot Token falsch → nano /opt/ccx-ultra/bot/config.env
# 2. Intents nicht aktiviert → Discord Developer Portal
# 3. Guild ID falsch → config.env prüfen

# Bot neu starten
supervisorctl restart ccx-bot
```

### Problem: SSL Zertifikat fehlt

```bash
# DNS prüfen
dig ticket.armesa.de

# Sollte Ihre VPS IP zeigen

# Certbot manuell ausführen
certbot --nginx -d ticket.armesa.de

# Nginx neu laden
systemctl reload nginx
```

### Problem: Frontend zeigt weiße Seite

```bash
# Prüfen ob Build existiert
ls /opt/ccx-ultra/web/static/index.html

# Falls nicht:
cd /root/ccx-fixed/frontend
yarn install
echo 'REACT_APP_BACKEND_URL=https://ticket.armesa.de' > .env
yarn build
cp -r build/* /opt/ccx-ultra/web/static/

# Nginx neu laden
systemctl reload nginx
```

---

## 📞 HILFE BEKOMMEN

### Vollständige Diagnose:

```bash
# Umfassendes Troubleshooting
cd /root/ccx-fixed/deployment
bash troubleshoot.sh

# Zeigt:
# - Was funktioniert ✅
# - Was nicht funktioniert ❌
# - Konkrete Lösungsvorschläge
```

### Logs analysieren:

```bash
# Alle aktuellen Logs
ls -lh /opt/ccx-ultra/logs/

# Backend Errors
tail -n 50 /opt/ccx-ultra/logs/webpanel.err.log

# Bot Errors
tail -n 50 /opt/ccx-ultra/logs/bot.err.log

# Nginx Errors
tail -n 50 /var/log/nginx/error.log
```

### System Status:

```bash
# Health Check
/opt/ccx-ultra/healthcheck.sh

# Services
supervisorctl status

# Ports
netstat -tlnp | grep -E "(8001|27017|80|443)"

# Ressourcen
free -h
df -h
```

---

## 📋 CHECKLISTE

Haken Sie ab, wenn erledigt:

- [ ] VPS erreichbar via SSH
- [ ] Domain zeigt auf VPS IP (DNS A Record)
- [ ] Paket auf VPS hochgeladen
- [ ] `install_v2.sh` erfolgreich durchgelaufen
- [ ] `post_install_setup.sh` erfolgreich durchgelaufen
- [ ] Discord Bot Token konfiguriert
- [ ] Discord IDs konfiguriert
- [ ] Services laufen (`supervisorctl status`)
- [ ] Backend API antwortet (`curl http://localhost:8001/api/health`)
- [ ] HTTPS funktioniert (`https://ticket.armesa.de`)
- [ ] Login funktioniert (admin/admin123)
- [ ] Discord Bot ist online
- [ ] Ticket Panel erstellt (`/ticket-panel`)
- [ ] Test-Ticket erstellt
- [ ] Ticket im Web Panel sichtbar

---

## 🚀 ZUSAMMENFASSUNG DER BEFEHLE

```bash
# === AUF IHREM PC ===
# Datei hochladen
scp ccx-ultra-fixed-20260209.tar.gz root@IHRE_VPS_IP:/root/

# === AUF DEM VPS (via SSH) ===
# Extrahieren
cd /root
tar -xzf ccx-ultra-fixed-20260209.tar.gz
cd ccx-fixed/deployment
chmod +x *.sh

# Installation
bash install_v2.sh          # 10-15 Min
bash post_install_setup.sh  # 5-10 Min

# Konfiguration
nano /opt/ccx-ultra/web/.env        # Bot Token eintragen
nano /opt/ccx-ultra/bot/config.env  # Bot Token eintragen

# Services starten
supervisorctl restart all

# Testen
bash troubleshoot.sh
curl http://localhost:8001/api/health

# === IM BROWSER ===
# https://ticket.armesa.de/login
# admin / admin123

# === IN DISCORD ===
# /ticket-panel
```

---

## ✅ ERFOLG!

Wenn alle Schritte durchgeführt wurden, haben Sie jetzt:

✅ Vollständig funktionierendes Discord Ticket System  
✅ Web Control Panel mit Live-Dashboard  
✅ Discord Bot mit Ticket-Erstellung  
✅ MongoDB Datenbank  
✅ SSL/HTTPS Verschlüsselung  
✅ Automatische Backups  
✅ Umfassende Monitoring-Tools  

**Viel Erfolg mit Ihrem Control Center X Ultra!** 🎉

---

*Bei Fragen lesen Sie: INSTALLATION_GUIDE.md oder PROBLEM_SOLUTION_ANALYSIS.md*
