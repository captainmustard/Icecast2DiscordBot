import discord
from discord import FFmpegPCMAudio
import yaml
import aiohttp
import asyncio

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

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
        now_playing = await get_now_playing()
        if now_playing != current_status:
            await bot.change_presence(activity=discord.Game(name=now_playing))
            current_status = now_playing
        await asyncio.sleep(1)  # update status every second if changed

async def connect_and_play(channel, icecast_url):
    try:
        voice_client = await channel.connect()
        voice_client.play(FFmpegPCMAudio(icecast_url))
    except Exception as e:
        print(f"Error: {e}")

@bot.event
async def on_ready():
    print('Bot is ready.')
    bot.loop.create_task(update_status())

@bot.event
async def on_voice_state_update(member, before, after):
    guild = discord.utils.get(bot.guilds, id=int(config["guild_id"]))

    if guild is None:
        print('Server not found!')
        return

    channel = discord.utils.get(guild.voice_channels, id=int(config["voice_channel_id"]))

    if channel is None:
        print('Voice channel not found!')
        return

    # If someone joined the configured voice channel
    if after.channel == channel:
        if len(after.channel.members) <= 1:  # Just the bot
            return

        # If the bot is not already in the channel, join it and start playing
        if not any(voice_client.channel == channel for voice_client in bot.voice_clients):
            await connect_and_play(channel, config["icecast_url"])

    # If someone left the configured voice channel
    elif before.channel == channel:
        if len(before.channel.members) > 1:  # Someone other than the bot is still in the channel
            return

        # If the bot is the only one left in the channel, disconnect
        for voice_client in bot.voice_clients:
            if voice_client.channel == channel:
                await voice_client.disconnect()

bot.run(config["discord_bot_key"])
