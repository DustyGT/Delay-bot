import asyncio
import re
import datetime
import random
import discord
from discord.ext import commands

# Enable message permissions
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Counter state
delay_days = 0

# Casual/AI response styles
SPICY_RESPONSES = [
    "bro... asking for the release date literally adds another day to the wait. read the rules bro",
    "congrats, you just delayed the game by another day. hope you're happy now. read the rules!",
    "another one asking for an ETA? that's +1 day on the clock. go read the rules while on timeout.",
    "devs just pushed the release back a whole day because of this question. check the rules next time 🤦‍♂️",
    "stop asking when it's dropping! adding 1 day to the delay counter right now. read the rules.",
    "every time someone asks 'when release', a dev cries and delays the game 1 day. enjoy your 1 min mute!",
    "did you really just ask for the APK/release? +1 day penalty issued. read the rules channel!"
]

# ---------------- BULLETPROOF DETECTION ENGINE ----------------

# Instant triggers (if ANY of these single words/phrases are found, instant trigger)
INSTANT_TRIGGERS = [
    r"\beta\b", r"\brelease date\b", r"\brelease-date\b", r"\blaunch date\b",
    r"\bwhen out\b", r"\bwen out\b", r"\bwhen release\b", r"\bwen release\b",
    r"\bapk link\b", r"\bdownload link\b", r"\bis it out\b", r"\bis it ready\b",
    r"\bapk drop\b", r"\bgame drop\b", r"\bwhen drop\b"
]

# Keyword Lists
QUESTIONS = ["when", "wen", "whens", "wher", "where", "how long", "what time", "will", "is", "can", "should", "any", "status", "gimme", "give", "need", "eta"]
TARGETS = ["game", "apk", "demo", "beta", "update", "build", "mod", "patch", "version", "file", "link", "it", "download", "bot", "full version"]
ACTIONS = ["come", "com", "cum", "out", "release", "released", "releasing", "launch", "launching", "drop", "dropping", "available", "download", "play", "test", "testing", "done", "ready", "finish", "finished", "get", "obtain"]

def is_asking_about_release(text: str) -> bool:
    # Clean up user message (remove punctuation so tricking the bot with symbols fails)
    clean = re.sub(r"[^\w\s]", "", text.lower())

    # 1. Check instant triggers
    for trigger in INSTANT_TRIGGERS:
        if re.search(trigger, clean):
            return True

    # 2. Point-based match system
    # Check if words from each category exist in the message
    has_question = any(re.search(rf"\b{q}\b", clean) for q in QUESTIONS)
    has_target = any(re.search(rf"\b{t}\b", clean) for t in TARGETS)
    has_action = any(re.search(rf"\b{a}\b", clean) for a in ACTIONS)

    # Score points based on categories matched
    score = sum([has_question, has_target, has_action])

    # If message matches 2 or more categories, it's asking about the release!
    if score >= 2:
        return True

    return False


@bot.event
async def on_ready():
    print(f"Bot is ONLINE as {bot.user.name}!")

@bot.event
async def on_message(message):
    global delay_days

    # Ignore bot messages
    if message.author.bot:
        return

    # Process commands first (!adddelay, etc.)
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # Check message with the new detection engine
    if is_asking_about_release(message.content):
        delay_days += 1

        # Attempt 1-minute timeout
        try:
            await message.author.timeout(datetime.timedelta(minutes=1), reason="Asked for game release/ETA")
        except Exception as e:
            print(f"Couldn't timeout {message.author}: {e}")

        reply_text = random.choice(SPICY_RESPONSES)

        embed = discord.Embed(
            title="🛑 Game Delayed!",
            description=f"{message.author.mention} {reply_text}",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Total Delay Counter",
            value=f"**{delay_days} day(s)** added so far.",
            inline=False
        )

        await message.channel.send(embed=embed)

# ---------------- ADMIN COMMANDS ----------------

@bot.command()
@commands.has_permissions(administrator=True)
async def adddelay(ctx, amount: int = 1):
    global delay_days
    delay_days += amount
    await ctx.send(f"Added {amount} day(s)! Current delay: **{delay_days} day(s)**.")

@bot.command()
@commands.has_permissions(administrator=True)
async def removedelay(ctx, amount: int = 1):
    global delay_days
    delay_days = max(0, delay_days - amount)
    await ctx.send(f"Removed {amount} day(s)! Current delay: **{delay_days} day(s)**.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setdelay(ctx, amount: int):
    global delay_days
    delay_days = amount
    await ctx.send(f"Delay counter set to **{delay_days} day(s)**.")

# Run bot (Replace with your token)
import os
bot.run(os.environ['DISCORD_TOKEN'])


