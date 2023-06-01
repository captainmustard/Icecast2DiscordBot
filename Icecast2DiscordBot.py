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
        print(f'Someone joined the channel: {channel.name} (ID: {channel.id})')

        # If the bot is not already in the channel, join it and start playing
        if not any(voice_client.channel == channel for voice_client in bot.voice_clients):
            try:
                voice_client = await channel.connect()
                voice_client.play(FFmpegPCMAudio(config["icecast_url"]))
            except Exception as e:
                print(f"An error occurred: {e}")

    # If someone left the configured voice channel
    elif before.channel == channel:
        # Wait for a second to allow the members list to update
        await asyncio.sleep(1)

        # If the bot is the only one left in the channel, disconnect
        if len(before.channel.members) == 1:
            for voice_client in bot.voice_clients:
                if voice_client.channel == channel:
                    await voice_client.disconnect()

    # If someone left any channel
    elif before.channel is not None:
        # Wait for a second to allow the members list to update
        await asyncio.sleep(1)

        # If the bot is the only one left in the channel, disconnect
        if len(before.channel.members) == 1:
            for voice_client in bot.voice_clients:
                if voice_client.channel == before.channel:
                    await voice_client.disconnect()

bot.run(config["discord_bot_key"])
