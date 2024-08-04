import discord
from discord import FFmpegPCMAudio
import yaml
import aiohttp
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Validate configuration
required_keys = ["icecast_url", "guild_id", "voice_channel_id", "discord_bot_key"]
for key in required_keys:
    if key not in config:
        logging.error(f"Missing required config key: {key}")
        exit(1)

# Extract the base URL from the icecast_url and construct the status URL
icecast_base_url = '/'.join(config["icecast_url"].split('/')[:-1])
icecast_status_url = f"{icecast_base_url}/status-json.xsl"

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True

bot = discord.Client(intents=intents)

async def fetch_icecast_status(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data
            else:
                logging.error(f"Failed to fetch data: {resp.status}")
                return None

async def get_now_playing():
    status_data = await fetch_icecast_status(icecast_status_url)

    if status_data and "icestats" in status_data:
        icestats = status_data["icestats"]

        # Check for artist and title
        artist = icestats.get('artist')
        title = icestats.get('title')
        if artist and title:
            now_playing = f"{artist} : {title}"
        # Check for server_name
        elif 'server_name' in icestats:
            now_playing = icestats['server_name']
        # Fallback to host and source extracted from the URL
        else:
            host = icestats.get('host', 'unknown host')
            stream_url = config["icecast_url"]
            source = stream_url.split('/')[-1]  # Extracts the last part of the URL
            now_playing = f"{host} : {source}"

        return now_playing
    else:
        return "Unknown"

async def update_status():
    current_status = None
    while True:
        try:
            now_playing = await get_now_playing()
            if now_playing != current_status:
                await bot.change_presence(activity=discord.Game(name=now_playing))
                current_status = now_playing
            await asyncio.sleep(60)  # update status every 60 seconds
        except Exception as e:
            logging.error(f"Error updating status: {e}")

async def connect_and_play(channel, icecast_url):
    try:
        voice_client = await channel.connect()
        audio_source = FFmpegPCMAudio(icecast_url, options="-loglevel debug")
        voice_client.play(audio_source)
    except Exception as e:
        logging.error(f"Error connecting and playing: {e}")

@bot.event
async def on_ready():
    logging.info('Bot is ready.')
    bot.loop.create_task(update_status())
    await check_and_join_voice_channel()

async def check_and_join_voice_channel():
    guild = discord.utils.get(bot.guilds, id=int(config["guild_id"]))
    if guild is None:
        logging.error('Server not found!')
        return

    channel = discord.utils.get(guild.voice_channels, id=int(config["voice_channel_id"]))
    if channel is None:
        logging.error('Voice channel not found!')
        return

    if len(channel.members) > 0:
        await handle_user_joined(channel)

@bot.event
async def on_voice_state_update(member, before, after):
    guild = discord.utils.get(bot.guilds, id=int(config["guild_id"]))

    if guild is None:
        logging.error('Server not found!')
        return

    channel = discord.utils.get(guild.voice_channels, id=int(config["voice_channel_id"]))

    if channel is None:
        logging.error('Voice channel not found!')
        return

    # If someone joined the configured voice channel
    if after.channel == channel:
        await handle_user_joined(channel)

    # If someone left the configured voice channel
    elif before.channel == channel:
        await handle_user_left(channel)

async def handle_user_joined(channel):
    non_bot_members = [member for member in channel.members if not member.bot]
    if len(non_bot_members) == 0:
        return

    # If the bot is not already in the channel, join it and start playing
    if not any(voice_client.channel == channel for voice_client in bot.voice_clients):
        await connect_and_play(channel, config["icecast_url"])

async def handle_user_left(channel):
    non_bot_members = [member for member in channel.members if not member.bot]
    if len(non_bot_members) > 0:
        return

    # If the bot is the only one left in the channel, disconnect
    for voice_client in bot.voice_clients:
        if voice_client.channel == channel:
            await voice_client.disconnect()

bot.run(config["discord_bot_key"])
