"""
Enterprise Discord Ticket Bot - Control Center X Ultra
======================================================
Standalone Discord Bot (Python / discord.py)
Communicates with the Web Control Center via REST API webhooks.

Requirements: discord.py, aiohttp, python-dotenv

Setup:
  1. Copy config.env.template to config.env
  2. Fill in your Discord Bot Token and API details
  3. pip install -r requirements.txt
  4. python bot.py
"""

import os
import asyncio
import json
import html
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
from dotenv import load_dotenv

# Load config
load_dotenv(Path(__file__).parent / 'config.env')

TOKEN = os.environ['DISCORD_BOT_TOKEN']
GUILD_ID = int(os.environ['DISCORD_GUILD_ID'])
TICKET_CHANNEL_ID = int(os.environ['TICKET_CHANNEL_ID'])
TRANSCRIPT_LOG_CHANNEL_ID = int(os.environ['TRANSCRIPT_LOG_CHANNEL_ID'])
TICKET_CATEGORY_ID = int(os.environ['TICKET_CATEGORY_ID'])
SUPPORT_ROLE_IDS = [int(x.strip()) for x in os.environ['SUPPORT_ROLE_IDS'].split(',')]
API_URL = os.environ.get('API_URL', 'http://localhost:8001/api')
MAX_TICKETS_PER_USER = int(os.environ.get('MAX_TICKETS_PER_USER', '3'))
SLA_MINUTES = int(os.environ.get('SLA_FIRST_RESPONSE_MINUTES', '30'))
AUTO_CLOSE_HOURS = int(os.environ.get('AUTO_CLOSE_INACTIVE_HOURS', '48'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('TicketBot')

# --- Bot Setup ---
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Track active tickets: { user_id: [channel_id, ...] }
user_tickets: dict[int, list[int]] = {}
# Track ticket data: { channel_id: { ... } }
ticket_data: dict[int, dict] = {}
# Rate limiting
last_ticket_time: dict[int, datetime] = {}
RATE_LIMIT_SECONDS = 60


# --- API Helper ---
async def api_request(method, path, data=None):
    """Send request to the web panel API."""
    headers = {
        'Content-Type': 'application/json',
        'X-Bot-Token': TOKEN
    }
    async with aiohttp.ClientSession() as session:
        url = f"{API_URL}{path}"
        try:
            if method == 'POST':
                async with session.post(url, json=data, headers=headers) as resp:
                    return await resp.json()
            elif method == 'GET':
                async with session.get(url, headers=headers) as resp:
                    return await resp.json()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None


def is_support(member: discord.Member) -> bool:
    """Check if member has a support role."""
    return any(role.id in SUPPORT_ROLE_IDS for role in member.roles)


# --- Ticket Creation Modal ---
class TicketModal(discord.ui.Modal):
    def __init__(self, lang: str):
        self.lang = lang
        title = "Ticket erstellen" if lang == "de" else "Create Ticket"
        super().__init__(title=title)

        self.ticket_type = discord.ui.TextInput(
            label="Typ / Type" if lang == "de" else "Type",
            placeholder="general, technical, billing, bug_report, feature_request",
            max_length=50,
            required=True
        )
        self.subject = discord.ui.TextInput(
            label="Betreff" if lang == "de" else "Subject",
            placeholder="Kurze Beschreibung des Problems" if lang == "de" else "Short description",
            max_length=200,
            required=True
        )
        self.description = discord.ui.TextInput(
            label="Beschreibung" if lang == "de" else "Description",
            style=discord.TextStyle.paragraph,
            placeholder="Detaillierte Beschreibung..." if lang == "de" else "Detailed description...",
            max_length=2000,
            required=True
        )
        self.priority = discord.ui.TextInput(
            label="Prioritaet (low/medium/high/critical)" if lang == "de" else "Priority (low/medium/high/critical)",
            placeholder="medium",
            max_length=10,
            required=True
        )

        self.add_item(self.ticket_type)
        self.add_item(self.subject)
        self.add_item(self.description)
        self.add_item(self.priority)

    async def on_submit(self, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild

        # Rate limit check
        now = datetime.now(timezone.utc)
        if user.id in last_ticket_time:
            diff = (now - last_ticket_time[user.id]).total_seconds()
            if diff < RATE_LIMIT_SECONDS:
                msg = f"Bitte warte {int(RATE_LIMIT_SECONDS - diff)}s" if self.lang == "de" else f"Please wait {int(RATE_LIMIT_SECONDS - diff)}s"
                await interaction.response.send_message(msg, ephemeral=True)
                return

        # Ticket limit check
        active = user_tickets.get(user.id, [])
        if len(active) >= MAX_TICKETS_PER_USER:
            msg = f"Du hast bereits {MAX_TICKETS_PER_USER} offene Tickets." if self.lang == "de" else f"You already have {MAX_TICKETS_PER_USER} open tickets."
            await interaction.response.send_message(msg, ephemeral=True)
            return

        # Duplicate check (same subject in last 5 min)
        for ch_id, td in ticket_data.items():
            if td['user_id'] == user.id and td['subject'].lower() == self.subject.value.lower():
                created = datetime.fromisoformat(td['created_at'])
                if (now - created).total_seconds() < 300:
                    msg = "Duplikat erkannt. Bitte warte." if self.lang == "de" else "Duplicate detected. Please wait."
                    await interaction.response.send_message(msg, ephemeral=True)
                    return

        # Validate priority
        priority = self.priority.value.lower().strip()
        if priority not in ('low', 'medium', 'high', 'critical'):
            priority = 'medium'

        await interaction.response.defer(ephemeral=True)

        # Create ticket channel
        category = guild.get_channel(TICKET_CATEGORY_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
        }
        for role_id in SUPPORT_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_num = len(ticket_data) + 1
        channel = await guild.create_text_channel(
            name=f"ticket-{ticket_num:04d}",
            category=category,
            overwrites=overwrites,
            topic=f"Ticket by {user.display_name} | {self.subject.value[:80]}"
        )

        # Store ticket data
        created_at = now.isoformat()
        td = {
            'channel_id': str(channel.id),
            'guild_id': str(guild.id),
            'user_id': user.id,
            'username': user.display_name,
            'subject': self.subject.value,
            'type': self.ticket_type.value.lower().strip(),
            'lang': self.lang,
            'priority': priority,
            'description': self.description.value,
            'created_at': created_at,
            'claimed_by': None,
        }
        ticket_data[channel.id] = td
        user_tickets.setdefault(user.id, []).append(channel.id)
        last_ticket_time[user.id] = now

        # Send to API
        await api_request('POST', '/bot/ticket', td)

        # Create ticket embed in channel
        embed = discord.Embed(
            title=f"{'Ticket' if self.lang == 'de' else 'Ticket'} #{ticket_num:04d}",
            color=discord.Color.blue(),
            timestamp=now
        )
        embed.add_field(name="Subject", value=self.subject.value, inline=False)
        embed.add_field(name="Type", value=self.ticket_type.value, inline=True)
        embed.add_field(name="Priority", value=priority.upper(), inline=True)
        embed.add_field(name="Language", value=self.lang.upper(), inline=True)
        embed.add_field(name="Description", value=self.description.value[:1024], inline=False)
        embed.set_footer(text=f"Created by {user.display_name}")

        # Action buttons
        view = TicketActions(self.lang)
        await channel.send(embed=embed, view=view)

        # Notify support
        support_pings = []
        for role_id in SUPPORT_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                support_pings.append(role.mention)
        if support_pings:
            ping_msg = ' '.join(support_pings) + f" - {'Neues Ticket!' if self.lang == 'de' else 'New ticket!'}"
            await channel.send(ping_msg, delete_after=30)

        # Confirm to user
        msg = f"Ticket erstellt: {channel.mention}" if self.lang == "de" else f"Ticket created: {channel.mention}"
        await interaction.followup.send(msg, ephemeral=True)


# --- Ticket Action Buttons ---
class TicketActions(discord.ui.View):
    def __init__(self, lang: str = "en"):
        super().__init__(timeout=None)
        self.lang = lang

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary, custom_id="ticket_claim", emoji=None)
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_support(interaction.user):
            await interaction.response.send_message("No permission.", ephemeral=True)
            return
        td = ticket_data.get(interaction.channel.id)
        if not td:
            await interaction.response.send_message("Ticket not found.", ephemeral=True)
            return
        if td.get('claimed_by'):
            await interaction.response.send_message(f"Already claimed by {td['claimed_by']}.", ephemeral=True)
            return
        td['claimed_by'] = interaction.user.display_name
        await api_request('POST', '/bot/event', {
            'event_type': 'ticket_claim',
            'data': {'ticket_id': td['channel_id'], 'claimed_by': interaction.user.display_name, 'subject': td['subject']}
        })
        embed = discord.Embed(description=f"Claimed by **{interaction.user.display_name}**", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_support(interaction.user):
            await interaction.response.send_message("No permission.", ephemeral=True)
            return
        td = ticket_data.get(interaction.channel.id)
        if not td:
            await interaction.response.send_message("Ticket not found.", ephemeral=True)
            return
        await interaction.response.defer()
        # Generate transcript
        transcript = await generate_transcript(interaction.channel, td)
        # Send transcript to log channel
        log_channel = interaction.guild.get_channel(TRANSCRIPT_LOG_CHANNEL_ID)
        if log_channel and transcript:
            file = discord.File(fp=transcript, filename=f"transcript-{interaction.channel.name}.html")
            await log_channel.send(
                f"Transcript for **{interaction.channel.name}** (closed by {interaction.user.display_name})",
                file=file
            )
        # Move to archive (rename + remove user perms)
        user_id = td.get('user_id')
        if user_id:
            user_tickets.get(user_id, []).remove(interaction.channel.id) if interaction.channel.id in user_tickets.get(user_id, []) else None
        await interaction.channel.edit(name=f"closed-{interaction.channel.name}")
        await interaction.channel.set_permissions(interaction.guild.default_role, read_messages=False)
        embed = discord.Embed(description=f"Ticket closed by **{interaction.user.display_name}**", color=discord.Color.green())
        await interaction.followup.send(embed=embed)
        # API event
        await api_request('POST', '/bot/event', {
            'event_type': 'ticket_close',
            'data': {'ticket_id': td['channel_id'], 'closed_by': interaction.user.display_name, 'subject': td['subject']}
        })

    @discord.ui.button(label="Reopen", style=discord.ButtonStyle.secondary, custom_id="ticket_reopen")
    async def reopen_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_support(interaction.user):
            await interaction.response.send_message("No permission.", ephemeral=True)
            return
        td = ticket_data.get(interaction.channel.id)
        if td:
            user_id = td.get('user_id')
            if user_id:
                user_tickets.setdefault(user_id, []).append(interaction.channel.id)
        name = interaction.channel.name.replace("closed-", "")
        await interaction.channel.edit(name=name)
        embed = discord.Embed(description=f"Ticket reopened by **{interaction.user.display_name}**", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)


# --- Transcript Generator ---
async def generate_transcript(channel: discord.TextChannel, td: dict):
    """Generate an HTML transcript of the ticket channel."""
    import io
    messages = []
    async for msg in channel.history(limit=500, oldest_first=True):
        messages.append({
            'author': html.escape(msg.author.display_name),
            'content': html.escape(msg.content) if msg.content else '[Embed/Attachment]',
            'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'avatar': str(msg.author.display_avatar.url) if msg.author.display_avatar else '',
        })

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Transcript - {html.escape(channel.name)}</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #e0e0e0; margin: 0; padding: 20px; }}
.header {{ background: #16213e; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
.header h1 {{ margin: 0; color: #3b82f6; font-size: 1.5em; }}
.header p {{ margin: 5px 0 0; color: #94a3b8; font-size: 0.9em; }}
.message {{ display: flex; gap: 12px; padding: 10px; border-bottom: 1px solid #27272a; }}
.message:hover {{ background: rgba(255,255,255,0.03); }}
.avatar {{ width: 36px; height: 36px; border-radius: 50%; background: #3b82f6; }}
.author {{ font-weight: bold; color: #f8fafc; }}
.time {{ color: #64748b; font-size: 0.8em; margin-left: 8px; }}
.content {{ margin-top: 4px; line-height: 1.5; }}
</style>
</head>
<body>
<div class="header">
<h1>Transcript: {html.escape(channel.name)}</h1>
<p>Subject: {html.escape(td.get('subject', 'N/A'))} | Type: {td.get('type', 'N/A')} | Priority: {td.get('priority', 'N/A')}</p>
<p>Created: {td.get('created_at', 'N/A')} | Messages: {len(messages)}</p>
</div>
"""
    for msg in messages:
        html_content += f"""<div class="message">
<img class="avatar" src="{msg['avatar']}" onerror="this.style.display='none'">
<div>
<span class="author">{msg['author']}</span><span class="time">{msg['timestamp']}</span>
<div class="content">{msg['content']}</div>
</div>
</div>
"""
    html_content += "</body></html>"

    return io.BytesIO(html_content.encode('utf-8'))


# --- Ticket Panel Command ---
class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Deutsch", style=discord.ButtonStyle.primary, custom_id="ticket_de")
    async def de_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal(lang="de"))

    @discord.ui.button(label="English", style=discord.ButtonStyle.secondary, custom_id="ticket_en")
    async def en_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal(lang="en"))


@bot.tree.command(name="ticket-panel", description="Create the ticket panel with language selection")
@app_commands.default_permissions(administrator=True)
async def ticket_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Support Ticket System",
        description="Click a button below to create a support ticket.\nKlicke einen Button um ein Support-Ticket zu erstellen.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Control Center X Ultra // Enterprise Ticket System")
    await interaction.response.send_message(embed=embed, view=TicketPanelView())


# --- SLA Check Task ---
@tasks.loop(minutes=5)
async def sla_check():
    """Check for SLA violations and auto-close inactive tickets."""
    now = datetime.now(timezone.utc)
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    for channel_id, td in list(ticket_data.items()):
        channel = guild.get_channel(channel_id)
        if not channel:
            continue

        created = datetime.fromisoformat(td['created_at'])
        age_minutes = (now - created).total_seconds() / 60

        # SLA warning
        if not td.get('claimed_by') and age_minutes > SLA_MINUTES:
            if not td.get('sla_warned'):
                td['sla_warned'] = True
                embed = discord.Embed(
                    description=f"SLA Warning: This ticket has been open for {int(age_minutes)} minutes without response!",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)
                # Ping support
                for role_id in SUPPORT_ROLE_IDS:
                    role = guild.get_role(role_id)
                    if role:
                        await channel.send(f"{role.mention} - SLA breach imminent!", delete_after=60)

        # Auto-escalate after 2x SLA time
        if not td.get('claimed_by') and age_minutes > SLA_MINUTES * 2 and not td.get('escalated'):
            td['escalated'] = True
            td['priority'] = 'critical'
            await api_request('POST', '/bot/event', {
                'event_type': 'escalation',
                'data': {'ticket_id': td['channel_id'], 'reason': 'SLA breach - auto escalated', 'subject': td['subject']}
            })
            embed = discord.Embed(
                description="This ticket has been auto-escalated due to SLA breach!",
                color=discord.Color.dark_red()
            )
            await channel.send(embed=embed)

        # Auto-close inactive
        try:
            last_message = None
            async for msg in channel.history(limit=1):
                last_message = msg
            if last_message:
                msg_age_hours = (now - last_message.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                if msg_age_hours > AUTO_CLOSE_HOURS and 'closed' not in channel.name:
                    embed = discord.Embed(
                        description=f"Auto-closed after {AUTO_CLOSE_HOURS}h of inactivity.",
                        color=discord.Color.greyple()
                    )
                    await channel.send(embed=embed)
                    await channel.edit(name=f"closed-{channel.name}")
        except Exception as e:
            logger.error(f"Auto-close check error: {e}")


# --- Auto-ping when support comes online ---
@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    """Ping support when they come online if there are unclaimed tickets."""
    if before.status == discord.Status.offline and after.status != discord.Status.offline:
        if is_support(after):
            unclaimed = [td for td in ticket_data.values() if not td.get('claimed_by')]
            if unclaimed:
                guild = after.guild
                for td in unclaimed[:3]:  # Max 3 pings
                    channel = guild.get_channel(int(td['channel_id']))
                    if channel and 'closed' not in channel.name:
                        embed = discord.Embed(
                            description=f"{after.mention} is now online! This ticket is waiting for support.",
                            color=discord.Color.green()
                        )
                        await channel.send(embed=embed, delete_after=120)


# --- Bot Events ---
@bot.event
async def on_ready():
    logger.info(f'Bot ready as {bot.user} (ID: {bot.user.id})')
    bot.add_view(TicketPanelView())
    bot.add_view(TicketActions())
    try:
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        logger.info(f'Synced {len(synced)} commands to guild {GUILD_ID}')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')
    sla_check.start()


if __name__ == '__main__':
    bot.run(TOKEN)
