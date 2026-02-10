# Control Center X Ultra - Enterprise Discord Ticket System
## Complete Documentation

---

## Quick Start

```bash
# On Debian 12 VPS:
sudo bash install.sh
```

---

## Start/Stop Commands

```bash
# Check status
sudo supervisorctl status

# Start all
sudo supervisorctl start all

# Stop all
sudo supervisorctl stop all

# Restart bot
sudo supervisorctl restart ccx-bot

# Restart web panel
sudo supervisorctl restart ccx-webpanel

# View logs
tail -f /opt/ccx-ultra/logs/bot.out.log
tail -f /opt/ccx-ultra/logs/webpanel.out.log
tail -f /opt/ccx-ultra/logs/webpanel.err.log
```

---

## Update Guide

```bash
# 1. Backup first
/opt/ccx-ultra/backup.sh

# 2. Pull/copy new files
cp bot.py /opt/ccx-ultra/bot/
cp server.py /opt/ccx-ultra/web/

# 3. Update dependencies
source /opt/ccx-ultra/venv/bin/activate
pip install -r requirements.txt

# 4. Restart
sudo supervisorctl restart all
```

---

## Backup Guide

```bash
# Manual backup
/opt/ccx-ultra/backup.sh

# Automatic daily backup (already configured via cron at 3 AM)
crontab -l

# Restore from backup
mongorestore --db ccx_ultra /opt/ccx-ultra/backups/YYYYMMDD_HHMMSS/mongodb/ccx_ultra/
```

---

## Troubleshooting

### Bot not starting
```bash
# Check logs
tail -50 /opt/ccx-ultra/logs/bot.err.log

# Common issues:
# 1. Invalid token -> Check config.env DISCORD_BOT_TOKEN
# 2. Missing intents -> Enable in Discord Developer Portal
# 3. Python module not found -> Activate venv and pip install
```

### Web Panel not accessible
```bash
# Check if running
supervisorctl status ccx-webpanel
curl http://localhost:8001/api/health

# Check nginx
nginx -t
systemctl status nginx

# Check SSL
certbot certificates
certbot renew
```

### MongoDB issues
```bash
# Check status
systemctl status mongod

# Check logs
tail -50 /var/log/mongodb/mongod.log

# Repair
mongosh --eval "db.adminCommand({repairDatabase: 1})"
```

### Tickets not creating
```bash
# Check bot permissions in Discord
# Bot role must be ABOVE support roles
# Ensure category has correct permissions

# Check API connectivity
curl http://localhost:8001/api/health
```

---

## Discord Developer Portal Setup

### Required Privileged Intents
- **PRESENCE INTENT** - For online status detection and auto-ping
- **SERVER MEMBERS INTENT** - For member access and role checking
- **MESSAGE CONTENT INTENT** - For transcript generation

### Bot Permissions (Required)
| Permission | Reason |
|---|---|
| Manage Channels | Create/edit ticket channels |
| Read Messages | View ticket channels |
| Send Messages | Send messages in tickets |
| Manage Messages | Delete/pin messages |
| Embed Links | Send rich embeds |
| Attach Files | Upload transcripts |
| Read Message History | Generate transcripts |
| Add Reactions | React to messages |
| Use Slash Commands | /ticket-panel command |

### OAuth2 Scopes
- `bot`
- `applications.commands`

### Invite URL
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&scope=bot%20applications.commands
```

### Role Position
The bot's role must be positioned **ABOVE** all support roles in Server Settings > Roles to manage permissions correctly.

---

## API Documentation

### Auth
| Method | Route | Description |
|---|---|---|
| POST | /api/auth/login | Login with username/password |
| GET | /api/auth/me | Get current user info |

### Tickets
| Method | Route | Description |
|---|---|---|
| GET | /api/tickets | List tickets (supports filters) |
| GET | /api/tickets/:id | Get ticket details |
| PUT | /api/tickets/:id/claim | Claim a ticket |
| PUT | /api/tickets/:id/close | Close a ticket |
| PUT | /api/tickets/:id/reopen | Reopen a ticket |
| PUT | /api/tickets/:id/escalate | Escalate a ticket |
| PUT | /api/tickets/:id/notes | Update notes/priority |

### Analytics
| Method | Route | Description |
|---|---|---|
| GET | /api/kpi | Dashboard KPIs |
| GET | /api/support_stats | Support performance |
| GET | /api/sla | SLA compliance data |
| GET | /api/search?q=term | Search tickets |
| GET | /api/analytics/volume | Ticket volume over time |
| GET | /api/analytics/priority_distribution | Priority breakdown |
| GET | /api/analytics/type_distribution | Type breakdown |

### Live Events
| Method | Route | Description |
|---|---|---|
| GET | /api/events | SSE stream |
| GET | /api/recent_events | Recent events list |

### Bot Webhooks
| Method | Route | Description |
|---|---|---|
| POST | /api/bot/ticket | Create ticket from bot |
| POST | /api/bot/event | Push event from bot |

### Admin
| Method | Route | Description |
|---|---|---|
| GET | /api/admin/users | List panel users |
| POST | /api/admin/users | Create panel user |
| DELETE | /api/admin/users/:id | Delete panel user |

### Audit
| Method | Route | Description |
|---|---|---|
| GET | /api/audit_log | View audit log |

---

## Default Credentials

**Web Panel:**
- Admin: `admin` / `admin123`
- Support: `support` / `support123`

**CHANGE THESE IN PRODUCTION!**

---

## Architecture

```
Discord Users
    |
    v
Discord Bot (bot.py) <---> Discord API
    |
    | REST API webhooks
    v
FastAPI Web Panel (server.py)
    |
    v
MongoDB
    |
    v
React Dashboard (Frontend)
```

## File Structure

```
/opt/ccx-ultra/
  bot/
    bot.py           # Discord bot
    config.env       # Bot configuration
  web/
    server.py        # FastAPI web panel
    .env             # Web panel configuration
    static/          # Built React frontend
  venv/              # Python virtual environment
  logs/              # Application logs
  backups/           # Database backups
  transcripts/       # Ticket transcripts
```
