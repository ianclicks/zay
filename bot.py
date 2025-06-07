import discord
import asyncio
import re
import os

intents = discord.Intents.default()
intents.messages = True

client = discord.Client(intents=intents)

streaming_on = False
stream_text = "Streaming now!"
status_switching = False  # For compatibility, unused now

auto_react_enabled = False
auto_react_emoji = None

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

@client.event
async def on_message(message):
    global streaming_on, stream_text, auto_react_enabled, auto_react_emoji

    content = message.content.strip()

    # React to every message including own messages if autoreact enabled
    if auto_react_enabled and auto_react_emoji:
        try:
            await message.add_reaction(auto_react_emoji)
        except Exception as e:
            print(f"Failed to react: {e}")

    # Only process commands from self (selfbot commands)
    if message.author != client.user:
        return

    # $streamer - turn on streaming presence with current stream_text
    if content == '$streamer':
        if streaming_on:
            await message.channel.send('`Streaming presence is already ON.`')
            return
        streaming_on = True
        try:
            await client.change_presence(activity=discord.Streaming(name=stream_text, url="https://twitch.tv/example"))
            await message.channel.send('`Streaming presence turned ON.`')
        except Exception as e:
            await message.channel.send(f'`Error turning streaming ON: {e}`')
        return

    # $streameroff - turn off streaming presence (clear presence)
    if content == '$streameroff':
        if not streaming_on:
            await message.channel.send('`Streaming presence is already OFF.`')
            return
        streaming_on = False
        try:
            await client.change_presence(activity=None)
            await message.channel.send('`Streaming presence turned OFF.`')
        except Exception as e:
            await message.channel.send(f'`Error turning streaming OFF: {e}`')
        return

    # $streamertext <text> - change streaming status text if streaming is ON
    if content.startswith('$streamertext '):
        if not streaming_on:
            await message.channel.send('`Streaming presence is OFF. Use $streamer first.`')
            return
        new_text = content[len('$streamertext '):].strip()
        if not new_text:
            await message.channel.send('`Error: No streaming text provided.`')
            return
        stream_text = new_text
        try:
            await client.change_presence(activity=discord.Streaming(name=stream_text, url="https://twitch.tv/example"))
            await message.channel.send(f'`Streaming text updated to: {stream_text}`')
        except Exception as e:
            await message.channel.send(f'`Error updating streaming text: {e}`')
        return

    # $autoreact :emoji:
    if content.startswith('$autoreact '):
        emoji_str = content[len('$autoreact '):].strip()
        if not emoji_str:
            await message.channel.send('`Error: No emoji provided.`')
            return

        # Try adding reaction to check if valid emoji
        try:
            await message.add_reaction(emoji_str)
        except Exception as e:
            await message.channel.send(f'`Error: Invalid emoji or cannot use emoji: {e}`')
            return

        auto_react_enabled = True
        auto_react_emoji = emoji_str
        await message.channel.send(f'`Auto-react enabled with emoji: {auto_react_emoji}`')
        return

    # $autoreactoff
    if content == '$autoreactoff':
        if auto_react_enabled:
            auto_react_enabled = False
            auto_react_emoji = None
            await message.channel.send('`Auto-react disabled.`')
        else:
            await message.channel.send('`Auto-react is not enabled.`')
        return

    # $help
    if content == '$help':
        await message.channel.send('`Welcome To My Wrath`')
        help_text = """\
⠀⠀⠀⠀⠀⠀⠀⢀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⡀⣰⡿⠛⠛⠿⢶⣦⣀⠀⢀⣀⣀⣀⣀⣠⡾⠋⠀⠀⠹⣷⣄⣤⣶⡶⠿⠿⣷⡄⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢰⣿⠁⠀⠀⠀⠀⠈⠙⠛⠛⠋⠉⠉⢹⡟⠁⠀⠀⣀⣀⠘⣿⠉⠀⠀⠀⠀⠘⣿⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠁⠀⠀⣾⡋⣽⠿⠛⠿⢶⣤⣤⣤⣤⣿⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢸⣿⡴⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣄⡀⠀⢈⣻⡏⠀⠀⠀⠀⣿⣀⠀⠈⠙⣷⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣰⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠛⠛⠛⠙⢷⣄⣀⣀⣼⣏⣿⠀⠀⢀⣿⠀⠀⠀⠀
⠀⠀⠀⠀⢸⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⣿⡉⠉⠁⢀⣠⣿⡇⠀⠀⠀⠀
⠀⠀⠀⠀⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠗⠾⠟⠋⢹⣷⠀⠀⠀⠀
⢀⣤⣤⣤⣿⣤⣄⠀⠀⠀⠴⠚⠲⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣶⡆⠀⠀⠀⠀⢀⣈⣿⣀⣀⡀⠀
⠀⠀⠀⠈⣿⣠⣾⠟⠛⢷⡄⠀⠀⠀⠀⠀⠀⠀⡤⠶⢦⡀⠀⠀⠀⠀⠹⠯⠃⠀⠀⠀⠈⠉⢩⡿⠉⠉⠉⠁
⠀⠀⣤⡶⠿⣿⣇⠀⠀⠸⣷⠀⠀⠀⠀⠀⠀⠀⠓⠶⠞⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢤⣼⣯⣀⣀⠀⠀
⠀⢰⣯⠀⠀⠈⠻⠀⠀⠀⣿⣶⣤⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡿⠁⠉⠉⠁⠀
⠀⠀⠙⣷⣄⠀⠀⠀⠀⠀⢀⣀⣀⠙⢿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢈⣿⡿⢷⣄⡀⠀⠀⠀
⠀⠀⠀⠈⠙⣷⠀⠀⠀⣴⠟⠉⠉⠀⠀⣿⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣠⣤⣾⠟⠉⠀⠀⠈⠉⠀⠀⠀
⠀⠀⠀⠀⠰⣿⠀⠀⠀⠙⢧⣤⡶⠟⢀⣿⠛⢟⡟⡯⠽⢶⡶⠾⢿⣻⣏⣹⡏⣁⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠹⣷⣄⠀⠀⠀⠀⠀⣠⣾⠏⠀⠀⠙⠛⠛⠋⠀⠀⢀⣽⠟⠛⠖⠛⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠙⠻⠷⠶⠿⠟⠋⠹⣷⣤⣀⡀⠄⣡⣀⣠⣴⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠳⣍⣉⣻⣏⣉⣡⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
made by vor

$streamer - status says ur streaming
$streameroff - turns off streaming status
$streamertext <text> - changes stream text (must have streamer on)
$autoreact :emoji: - automatically react to all messages with the emoji
$autoreactoff - disable auto react
"""
        await message.channel.send(f'```\n{help_text}\n```')

# Run the client with your token from environment variables
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("Error: DISCORD_TOKEN environment variable is not set.")
else:
    client.run(token, bot=False)
