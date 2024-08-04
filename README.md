# Icecast2DiscordBot
This project includes a Discord bot capable of joining a voice channel and streaming music from an Icecast server. The bot's Discord status will reflect the currently playing track from the Icecast stream.

I created this specifically to stream the audio from [SDRtrunk](https://github.com/DSheirer/sdrtrunk) to my discord server.

## Installation

Install required packages using pip: 
```bash
pip install -r requirements.txt
```

## Configuration

You will need to configure the bot before use. This is done using the `config.yaml` file. The file contains the following fields:

- `guild_id`: The ID of your Discord server (guild).
- `voice_channel_id`: The ID of the voice channel you want the bot to join.
- `icecast_url`: The URL of your Icecast stream.
- `discord_bot_key`: The bot token for your Discord bot.

Replace the placeholders with your actual data.

## Usage

Once the bot is configured and running, it will automatically join the specified voice channel when a user enters and start streaming music from the Icecast server. The bot will leave the channel when no users are present.
