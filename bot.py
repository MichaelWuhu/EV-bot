from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
from commands import setup_commands

load_dotenv()
TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="ev!", intents=intents)

@bot.event
async def on_ready():
    guild_count = 0

    for guild in bot.guilds:
        print(f"- {guild.id} (name: {guild.name})")
        guild_count += 1

    print("Bot is in " + str(guild_count) + " servers")

setup_commands(bot)

bot.run(TOKEN)