import asyncio
import re
import random
import os
import discord
from discord.ext import commands
from aiohttp import web, ClientSession

# ---------------- DUMMY HTTP SERVER & SELF-PINGER ----------------
async def handle(request):
    return web.Response(text="Delay-bot is active!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def keep_alive_ping():
    """Pings its own Render URL every 10 minutes to prevent sleeping."""
    await asyncio.sleep(10)  # Wait for server startup
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not render_url:
        print("No RENDER_EXTERNAL_URL found, self-ping disabled.")
        return

    async with ClientSession() as session:
        while True:
            try:
                async with session.get(render_url) as response:
                    print(f"Self-ping successful: Status {response.status}")
            except Exception as e:
                print(f"Self-ping failed: {e}")
            await asyncio.sleep(600)  # Ping every 10 minutes

# Enable message permissions
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Per-server counter storage: { guild_id: delay_days }
server_delays = {}

def get_delay(guild_id: int) -> int:
    return server_delays.get(guild_id, 0)

def set_delay(guild_id: int, amount: int):
    server_delays[guild_id] = amount

SPICY_RESPONSES = [
    "bro... asking for the release date literally adds another day to the wait. read the rules bro",
    "congrats, you just delayed the game by another day. hope you're happy now. read the rules!",
    "another one asking for an ETA? that's +1 day on the clock.",
    "devs just pushed the release back a whole day because of this question. check the rules next time 🤦‍♂️",
    "stop asking when it's dropping! adding 1 day to the delay counter right now.",
    "every time someone asks 'when release', a dev cries and delays the game 1 day.",
    "did you really just ask for the release? +1 day penalty issued. read the rules channel!"
]

INSTANT_TRIGGERS = [
    r"\beta\b", r"\brelease date\b", r"\brelease-date\b", r"\blaunch date\b",
    r"\bwhen out\b", r"\bwen out\b", r"\bwhen release\b", r"\bwen release\b",
    r"\bapk link\b", r"\bdownload link\b", r"\bis it out\b", r"\bis it ready\b",
    r"\bapk drop\b", r"\bgame drop\b", r"\bwhen drop\b"
]

QUESTIONS = ["when", "wen", "whens", "wher", "where", "how long", "what time", "will", "is", "can", "should", "any", "status", "gimme", "give", "need", "eta"]
TARGETS = ["game", "apk", "demo", "beta", "update", "build", "mod", "patch", "version", "file", "link", "it", "download", "bot", "full version"]
ACTIONS = ["come", "com", "cum", "out", "release", "released", "releasing", "launch", "launching", "drop", "dropping", "available", "download", "play", "test", "testing", "done", "ready", "finish", "finished", "get", "obtain"]

def is_asking_about_release(text: str) -> bool:
    clean = re.sub(r"[^\w\s]", "", text.lower())

    for trigger in INSTANT_TRIGGERS:
        if re.search(trigger, clean):
            return True

    has_question = any(re.search(rf"\b{q}\b", clean) for q in QUESTIONS)
    has_target = any(re.search(rf"\b{t}\b", clean) for t in TARGETS)
    has_action = any(re.search(rf"\b{a}\b", clean) for a in ACTIONS)

    score = sum([has_question, has_target, has_action])
    return score >= 2

@bot.event
async def on_ready():
    print(f"Bot is ONLINE as {bot.user.name}!")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    if is_asking_about_release(message.content):
        guild_id = message.guild.id
        current_delay = get_delay(guild_id) + 1
        set_delay(guild_id, current_delay)

        reply_text = random.choice(SPICY_RESPONSES)

        embed = discord.Embed(
            title="🛑 Game Delayed!",
            description=f"{message.author.mention} {reply_text}",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Total Delay Counter",
            value=f"**{current_delay} day(s)** added so far.",
            inline=False
        )

        await message.channel.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def adddelay(ctx, amount: int = 1):
    current = get_delay(ctx.guild.id) + amount
    set_delay(ctx.guild.id, current)
    await ctx.send(f"Added {amount} day(s)! Current delay for this server: **{current} day(s)**.")

@bot.command()
@commands.has_permissions(administrator=True)
async def removedelay(ctx, amount: int = 1):
    current = max(0, get_delay(ctx.guild.id) - amount)
    set_delay(ctx.guild.id, current)
    await ctx.send(f"Removed {amount} day(s)! Current delay for this server: **{current} day(s)**.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setdelay(ctx, amount: int):
    set_delay(ctx.guild.id, amount)
    await ctx.send(f"Delay counter set to **{amount} day(s)** for this server.")

async def main():
    await start_web_server()
    asyncio.create_task(keep_alive_ping())
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN environment variable is missing!")
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
    
