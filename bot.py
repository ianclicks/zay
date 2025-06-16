import discord
import asyncio
import requests
import os
import re

# Read token from environment variable 'TOKEN' for Railway deployment
token = os.getenv("TOKEN")
if not token:
    print("Error: TOKEN environment variable not found.")
    exit(1)

intents = discord.Intents.default()
intents.messages = True  # message_content not available in v1.7.3
client = discord.Client(intents=intents)

stream_text = "Streaming"
command_prefix = "$"
guild_rotation_task = None
INTERVAL = 5  # default delay

DISCORD_API_URL = "https://discord.com/api/v9/users/@me/clan"

# Load guilds from file
def load_guilds():
    path = "guild/guilds.txt"
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        return {f"Guild {i+1}": line for i, line in enumerate(lines)}

def change_identity(guild_name, guild_id):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    payload = {
        "identity_guild_id": guild_id,
        "identity_enabled": True
    }
    try:
        r = requests.put(DISCORD_API_URL, headers=headers, json=payload)
        if r.status_code == 200:
            print(f"[✓] Changed to: {guild_name}")
        else:
            print(f"[✗] {guild_name} failed: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"[!] Error switching to {guild_name}: {e}")

def parse_time_argument(arg):
    match = re.match(r"(\d+)([smh])", arg)
    if not match:
        return None
    val, unit = int(match.group(1)), match.group(2)
    return val * {"s": 1, "m": 60, "h": 3600}[unit]

async def rotate_guilds_dynamic(guild_map, interval):
    items = list(guild_map.items())
    total = len(items)
    i = 0
    while True:
        name, gid = items[i]
        change_identity(name, gid)
        await asyncio.sleep(1 if i == 1 else interval)
        i = (i + 1) % total

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")

@client.event
async def on_message(message):
    global stream_text, command_prefix
    global guild_rotation_task, INTERVAL

    if message.author.id != client.user.id:
        return

    content = message.content.strip()

    # --- Prefix ---
    if content.startswith(command_prefix + "prefix set "):
        command_prefix = content[len(command_prefix + "prefix set "):].strip()
        await message.channel.send(f"```Prefix changed to: {command_prefix}```")
        return

    if content == command_prefix + "prefix reset":
        command_prefix = "$"
        await message.channel.send("```Prefix reset to: $```")
        return

    # --- Streamer ---
    if content == command_prefix + "streamer":
        await client.change_presence(activity=discord.Streaming(name=stream_text, url="https://twitch.tv/?"))
        await message.channel.send(f"```Streaming status set to: {stream_text}```")
        return

    if content == command_prefix + "streameroff":
        await client.change_presence(activity=None)
        await message.channel.send("```Streaming status cleared.```")
        return

    if content.startswith(command_prefix + "streamer text "):
        stream_text = content[len(command_prefix + "streamer text "):].strip()
        await message.channel.send(f"```Stream text set to: {stream_text}```")
        return

    # --- Guild Rotation ---
    if content.startswith(command_prefix + "guild rotate"):
        parts = content.split(maxsplit=3)
        if len(parts) >= 3:
            interval = parse_time_argument(parts[2])
            if interval is None:
                await message.channel.send("```Invalid time format. Use like 5s, 1m, or 2h.```")
                return
            INTERVAL = interval
        else:
            INTERVAL = 5

        # Handle optional custom guild list
        guild_map = {}
        if len(parts) == 4:
            raw_ids = parts[3].replace(",", " ").split()
            for i, gid in enumerate(raw_ids):
                gid = gid.strip()
                if gid.isdigit():
                    guild_map[f"Guild {i+1}"] = gid
                else:
                    await message.channel.send("```All guild IDs must be numeric.```")
                    return
        else:
            guild_map = load_guilds()
            if not guild_map:
                await message.channel.send("```No guilds found in guild/guilds.txt```")
                return

        if guild_rotation_task is None:
            guild_rotation_task = asyncio.create_task(rotate_guilds_dynamic(guild_map, INTERVAL))
            await message.channel.send(f"```Guild rotation started (every {INTERVAL} sec).```")
        else:
            await message.channel.send("```Guild rotation is already running.```")
        return

    if content == command_prefix + "guild reset":
        if guild_rotation_task:
            guild_rotation_task.cancel()
            guild_rotation_task = None
            await message.channel.send("```Guild rotation stopped.```")
        else:
            await message.channel.send("```Guild rotation is not running.```")
        return

    # --- Purge ---
    if content.startswith(command_prefix + "purge"):
        parts = content.split()
        if len(parts) != 2 or not parts[1].isdigit():
            await message.channel.send("```Usage: purge <amount>```")
            return
        limit = int(parts[1])
        deleted = 0
        async for msg in message.channel.history(limit=1000):
            if msg.author.id == client.user.id:
                await msg.delete()
                deleted += 1
                if deleted >= limit:
                    break
        await message.channel.send(f"```Purged {deleted} messages.```")
        return

    # --- Help Menus ---
    if content == command_prefix + "help":
        with open("assets/help.txt", "r", encoding="utf-8") as f:
            help_text = f.read()
        await message.channel.send(f"`What was said?`\n```\n{help_text}\n```")
        return

    if content == command_prefix + "help streamer":
        with open("assets/streamer.txt", "r", encoding="utf-8") as f:
            text = f.read()
        await message.channel.send(f"```\n{text}\n```")
        return

    if content == command_prefix + "help prefix":
        with open("assets/prefix.txt", "r", encoding="utf-8") as f:
            text = f.read()
        await message.channel.send(f"```\n{text}\n```")
        return

    if content == command_prefix + "help guild":
        with open("assets/guild.txt", "r", encoding="utf-8") as f:
            text = f.read()
        await message.channel.send(f"```\n{text}\n```")
        return

    if content == command_prefix + "help purge":
        with open("assets/purge.txt", "r", encoding="utf-8") as f:
            text = f.read()
        await message.channel.send(f"```\n{text}\n```")
        return

# Run
client.run(token, bot=False)
