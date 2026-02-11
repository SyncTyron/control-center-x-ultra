# -*- coding: utf-8 -*-
"""
Enterprise Discord Ticket Bot - Control Center X Ultra
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

load_dotenv(Path(__file__).parent / 'config.env')

TOKEN = os.environ['DISCORD_BOT_TOKEN']
GUILD_ID = int(os.environ['DISCORD_GUILD_ID'])
TICKET_CHANNEL_ID = int(os.environ['TICKET_CHANNEL_ID'])
TRANSCRIPT_LOG_CHANNEL_ID = int(os.environ['TRANSCRIPT_LOG_CHANNEL_ID'])
TICKET_CATEGORY_ID = int(os.environ['TICKET_CATEGORY_ID'])
SUPPORT_ROLE_IDS = [int(x.strip()) for x in os.environ['SUPPORT_ROLE_IDS'].split(',')]
API_URL = os.environ.get('API_URL', 'http://localhost:8002/api')
MAX_TICKETS_PER_USER = int(os.environ.get('MAX_TICKETS_PER_USER', '3'))
SLA_MINUTES = int(os.environ.get('SLA_FIRST_RESPONSE_MINUTES', '30'))
AUTO_CLOSE_HOURS = int(os.environ.get('AUTO_CLOSE_INACTIVE_HOURS', '48'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('TicketBot')

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

user_tickets = {}
ticket_data = {}
last_ticket_time = {}
RATE_LIMIT_SECONDS = 60
ticket_counter = 0


async def api_request(method, path, data=None):
    headers = {'Content-Type': 'application/json', 'X-Bot-Token': TOKEN}
    async with aiohttp.ClientSession() as session:
        url = f"{API_URL}{path}"
        logger.info(f"API Request: {method} {url}")
        try:
            if method == 'POST':
                async with session.post(url, json=data, headers=headers) as resp:
                    result = await resp.json()
                    logger.info(f"API Response: {resp.status} - {result}")
                    return result
            elif method == 'GET':
                async with session.get(url, headers=headers) as resp:
                    result = await resp.json()
                    logger.info(f"API Response: {resp.status} - {result}")
                    return result
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None


def is_support(member):
    return any(role.id in SUPPORT_ROLE_IDS for role in member.roles)


class PrioritySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Low", value="low", description="Low Priority"),
            discord.SelectOption(label="Medium", value="medium", description="Medium Priority"),
            discord.SelectOption(label="High", value="high", description="High Priority"),
            discord.SelectOption(label="Critical", value="critical", description="Critical Priority"),
        ]
        super().__init__(placeholder="Select Priority", min_values=1, max_values=1, options=options)

    async def callback(self, interaction):
        self.view.priority = self.values[0]
        await interaction.response.send_modal(TicketModal(lang=self.view.lang, priority=self.values[0]))


class TicketModal(discord.ui.Modal):
    def __init__(self, lang, priority):
        self.lang = lang
        self.priority = priority
        title = "Ticket erstellen" if lang == "de" else "Create Ticket"
        super().__init__(title=title)
        self.ticket_type = discord.ui.TextInput(label="Type", placeholder="general, technical, billing", max_length=50, required=True)
        self.subject = discord.ui.TextInput(label="Subject", placeholder="Short description", max_length=200, required=True)
        self.description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, placeholder="Detailed description", max_length=2000, required=True)
        self.add_item(self.ticket_type)
        self.add_item(self.subject)
        self.add_item(self.description)

    async def on_submit(self, interaction):
        global ticket_counter
        user = interaction.user
        guild = interaction.guild
        now = datetime.now(timezone.utc)

        if user.id in last_ticket_time:
            diff = (now - last_ticket_time[user.id]).total_seconds()
            if diff < RATE_LIMIT_SECONDS:
                await interaction.response.send_message(f"Please wait {int(RATE_LIMIT_SECONDS - diff)}s", ephemeral=True)
                return

        active = user_tickets.get(user.id, [])
        if len(active) >= MAX_TICKETS_PER_USER:
            await interaction.response.send_message(f"You already have {MAX_TICKETS_PER_USER} open tickets.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

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

        ticket_counter += 1
        lang_prefix = "de" if self.lang == "de" else "en"
        channel_name = f"{lang_prefix}-ticket-{self.priority}-{ticket_counter:04d}"

        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites, topic=f"Ticket by {user.display_name}")

        td = {
            'channel_id': str(channel.id),
            'guild_id': str(guild.id),
            'user_id': str(user.id),
            'username': user.display_name,
            'subject': self.subject.value,
            'type': self.ticket_type.value.lower().strip(),
            'lang': self.lang,
            'priority': self.priority,
            'description': self.description.value,
            'created_at': now.isoformat(),
            'claimed_by': None,
        }
        ticket_data[channel.id] = td
        user_tickets.setdefault(user.id, []).append(channel.id)
        last_ticket_time[user.id] = now

        await api_request('POST', '/bot/ticket', td)

        colors = {'low': discord.Color.green(), 'medium': discord.Color.blue(), 'high': discord.Color.orange(), 'critical': discord.Color.red()}
        embed = discord.Embed(title=f"Ticket #{ticket_counter:04d}", color=colors.get(self.priority, discord.Color.blue()), timestamp=now)
        embed.add_field(name="Subject", value=self.subject.value, inline=False)
        embed.add_field(name="Type", value=self.ticket_type.value, inline=True)
        embed.add_field(name="Priority", value=self.priority.upper(), inline=True)
        embed.add_field(name="Description", value=self.description.value[:1024], inline=False)
        embed.set_footer(text=f"Created by {user.display_name}")

        view = TicketActions(self.lang)
        await channel.send(embed=embed, view=view)

        for role_id in SUPPORT_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                await channel.send(f"{role.mention} - New ticket!", delete_after=10)

        await interaction.followup.send(f"Ticket created: {channel.mention}", ephemeral=True)


class PrioritySelectionView(discord.ui.View):
    def __init__(self, lang):
        super().__init__(timeout=60)
        self.lang = lang
        self.priority = "medium"
        self.add_item(PrioritySelect())


class TicketActions(discord.ui.View):
    def __init__(self, lang="en"):
        super().__init__(timeout=None)
        self.lang = lang

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary, custom_id="ticket_claim")
    async def claim_button(self, interaction, button):
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
        await api_request('POST', '/bot/event', {'event_type': 'ticket_claim', 'data': {'ticket_id': td['channel_id'], 'claimed_by': interaction.user.display_name}})
        embed = discord.Embed(description=f"Claimed by **{interaction.user.display_name}**", color=discord.Color.gold())
        msg = await interaction.response.send_message(embed=embed)
        await asyncio.sleep(10)
        try:
            await (await interaction.original_response()).delete()
        except:
            pass

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close_button(self, interaction, button):
        if not is_support(interaction.user):
            await interaction.response.send_message("No permission.", ephemeral=True)
            return
        td = ticket_data.get(interaction.channel.id)
        if not td:
            await interaction.response.send_message("Ticket not found.", ephemeral=True)
            return
        await interaction.response.defer()
        user_id = td.get('user_id')
        if user_id:
            uid = int(user_id)
            if uid in user_tickets and interaction.channel.id in user_tickets.get(uid, []):
                user_tickets[uid].remove(interaction.channel.id)
        
        embed = discord.Embed(description=f"Ticket closed by **{interaction.user.display_name}**. Channel will be deleted in 5 seconds.", color=discord.Color.green())
        await interaction.followup.send(embed=embed)
        await api_request('POST', '/bot/event', {'event_type': 'ticket_close', 'data': {'ticket_id': td['channel_id'], 'closed_by': interaction.user.display_name}})
        
        await asyncio.sleep(5)
        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user.display_name}")

    @discord.ui.button(label="Reopen", style=discord.ButtonStyle.secondary, custom_id="ticket_reopen")
    async def reopen_button(self, interaction, button):
        if not is_support(interaction.user):
            await interaction.response.send_message("No permission.", ephemeral=True)
            return
        td = ticket_data.get(interaction.channel.id)
        if td:
            uid = int(td.get('user_id', 0))
            if uid:
                user_tickets.setdefault(uid, []).append(interaction.channel.id)
        name = interaction.channel.name.replace("closed-", "")
        await interaction.channel.edit(name=name)
        embed = discord.Embed(description=f"Ticket reopened by **{interaction.user.display_name}**", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Deutsch", style=discord.ButtonStyle.primary, custom_id="ticket_de")
    async def de_button(self, interaction, button):
        view = PrioritySelectionView(lang="de")
        await interaction.response.send_message("Waehle die Prioritaet:", view=view, ephemeral=True)

    @discord.ui.button(label="English", style=discord.ButtonStyle.secondary, custom_id="ticket_en")
    async def en_button(self, interaction, button):
        view = PrioritySelectionView(lang="en")
        await interaction.response.send_message("Select priority:", view=view, ephemeral=True)


@bot.tree.command(name="ticket-panel", description="Create the ticket panel")
@app_commands.default_permissions(administrator=True)
async def ticket_panel(interaction):
    embed = discord.Embed(title="Support Ticket System", description="Click a button to create a ticket.", color=discord.Color.blue())
    embed.set_footer(text="Control Center X Ultra")
    await interaction.response.send_message(embed=embed, view=TicketPanelView())


@tasks.loop(minutes=5)
async def sla_check():
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
        if not td.get('claimed_by') and age_minutes > SLA_MINUTES and not td.get('sla_warned'):
            td['sla_warned'] = True
            embed = discord.Embed(description=f"SLA Warning: {int(age_minutes)} minutes without response!", color=discord.Color.red())
            await channel.send(embed=embed)


@bot.event
async def on_ready():
    global ticket_counter
    logger.info(f'Bot ready as {bot.user} (ID: {bot.user.id})')
    bot.add_view(TicketPanelView())
    bot.add_view(TicketActions())
    guild = bot.get_guild(GUILD_ID)
    if guild:
        category = guild.get_channel(TICKET_CATEGORY_ID)
        if category:
            for ch in category.channels:
                if 'ticket' in ch.name.lower():
                    ticket_counter += 1
    try:
        g = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=g)
        synced = await bot.tree.sync(guild=g)
        logger.info(f'Synced {len(synced)} commands to guild {GUILD_ID}')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')
    sla_check.start()


if __name__ == '__main__':
    bot.run(TOKEN)
