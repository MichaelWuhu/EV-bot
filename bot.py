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

setup_commands(bot)

bot.run(TOKEN)