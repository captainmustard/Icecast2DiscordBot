# Icecast2DiscordBot
This project includes a Discord bot capable of joining a voice channel and streaming music from an Icecast server. The bot will automatically join a voice channel when a user enters and start streaming, and leave when no users are present. The bot's Discord status will reflect the currently playing track from the Icecast stream.

Install required packages using pip: 
    ```
    pip install -r requirements.txt
    ```

## Configuration

You will need to configure the bot before use. This is done using the `config.yaml` file. The file contains the following fields:

- `guild_id`: The ID of your Discord server (guild).
- `voice_channel_id`: The ID of the voice channel you want the bot to join.
- `icecast_url`: The URL of your Icecast stream.
- `discord_bot_key`: The bot token for your Discord bot.
- `icecast_status_url`: The URL to the `status-json.xsl` endpoint of your Icecast server.

Replace the placeholders with your actual data.
