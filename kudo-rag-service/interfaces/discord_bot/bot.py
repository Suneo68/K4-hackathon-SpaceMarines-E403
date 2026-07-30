import discord
from discord.ext import commands

# Configure Discord Intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

# Initialize Bot Instance
bot = commands.Bot(command_prefix="!", intents=intents)
