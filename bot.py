import asyncio
import os
import re
import discord
from discord.ext import commands
from aiohttp import web, ClientSession
from google import genai
from google.genai.types import GenerateContentConfig

# ---------------- DUMMY WEB SERVER & KEEP-ALIVE ----------------
async def handle_ping(request):
    return web.Response(text="Derrick Hutchinson bot is active!")

async def run_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def self_ping_loop():
    await asyncio.sleep(10)
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not render_url:
        print("RENDER_EXTERNAL_URL not set yet. Self-ping idle.")
        return

    async with ClientSession() as session:
        while True:
            try:
                async with session.get(render_url) as resp:
                    print(f"Self-ping heartbeat: {resp.status}")
            except Exception as err:
                print(f"Self-ping error: {err}")
            await asyncio.sleep(600)

# ---------------- BOT & GEMINI SETUP ----------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

gemini_key = os.environ.get("GEMINI_API_KEY")
if not gemini_key:
    raise ValueError("Missing GEMINI_API_KEY environment variable!")

ai = genai.Client(api_key=gemini_key)

DERRICK_INSTRUCTIONS = (
    "Your name is Derrick Hutchinson from Southwest Harbor, Maine (Mount Desert Island / MDI). "
    "Your son is Stanley, and he attends Pemetic Elementary School. "
    "You are a regular guy chatting in a Discord server—talk totally normal, grounded, and casual. "
    "Never act like an AI assistant or start messages with robotic greetings like 'Hello! How can I help you today?'. "
    "You can use profane/swearing words naturally when conversing, but NEVER use slurs or hate speech. "
    "If anyone asks for a story, make up stories set around Southwest Harbor/MDI featuring your son Stanley or his school Pemetic Elementary."
)

@bot.event
async def on_ready():
    print(f"Derrick Hutchinson is ready and logged in as {bot.user.name}!")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    mentioned = bot.user.mentioned_in(message)
    is_reply = message.reference and message.reference.resolved and message.reference.resolved.author == bot.user
    name_check = bool(re.search(r"\bderrick\b", message.content, re.IGNORECASE))

    if mentioned or is_reply or name_check:
        async with message.channel.typing():
            try:
                prompt = message.clean_content.replace(f"@{bot.user.name}", "").strip()
                if not prompt:
                    prompt = "Hey Derrick"

                # Standard synchronous call wrapped safely for discord.py loop
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: ai.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=prompt,
                        config=GenerateContentConfig(
                            system_instruction=DERRICK_INSTRUCTIONS
                        )
                    )
                )

                output = response.text

                if len(output) > 2000:
                    for chunk in [output[i:i+1900] for i in range(0, len(output), 1900)]:
                        await message.reply(chunk)
                else:
                    await message.reply(output)

            except Exception as err:
                print(f"Execution Error: {err}")
                await message.reply("Damn, ran into a quick issue. Try asking again.")

async def main():
    await run_web_server()
    asyncio.create_task(self_ping_loop())
    discord_token = os.environ.get("DISCORD_TOKEN")
    if not discord_token:
        raise ValueError("Missing DISCORD_TOKEN environment variable!")
    await bot.start(discord_token)

if __name__ == "__main__":
    asyncio.run(main())
    
