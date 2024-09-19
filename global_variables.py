import os

import discord
from discord.ext import commands

TOKEN = os.getenv('TOKEN')
GUILD_ID = [os.getenv('GUILD_ID')]

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(intents=intents)
client.remove_command('help')
