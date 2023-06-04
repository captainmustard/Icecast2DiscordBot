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
required_keys = ["icecast_status_url", "icecast_url", "guild_id", "voice_channel_id", "discord_bot_key"]
for key in required_keys:
    if key not in config:
        logging.error(f"Missing required config key: {key}")
        exit(1)

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True

bot = discord.Client(intents=intents)

async def get_now_playing():
    url = config["icecast_status_url"]

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            status_json = await resp.json()

    return status_json["icestats"]["source"]["title"]

async def update_status():
    current_status = None
    while True:
        try:
            now_playing = await get_now_playing()
            if now_playing != current_status:
                await bot.change_presence(activity=discord.Game(name=now_playing))
                current_status = now_playing
            await asyncio.sleep(10)  # update status every 10 seconds if changed
        except Exception as e:
            logging.error(f"Error updating status: {e}")

async def connect_and_play(channel, icecast_url):
    try:
        voice_client = await channel.connect()
        voice_client.play(FFmpegPCMAudio(icecast_url))
    except Exception as e:
        logging.error(f"Error connecting and playing: {e}")

@bot.event
async def on_ready():
    logging.info('Bot is ready.')
    bot.loop.create_task(update_status())

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
    if len(channel.members) <= 1:  # Just the bot
        return

    # If the bot is not already in the channel, join it and start playing
    if not any(voice_client.channel == channel for voice_client in bot.voice_clients):
        await connect_and_play(channel, config["icecast_url"])

async def handle_user_left(channel):
    if len(channel.members) > 1:  # Someone other than the bot is still in the channel
        return

    # If the bot is the only one left in the channel, disconnect
    for voice_client in bot.voice_clients:
        if voice_client.channel == channel:
            await voice_client.disconnect()

bot.run(config["discord_bot_key"])
