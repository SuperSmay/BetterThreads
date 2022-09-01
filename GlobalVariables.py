import discord
from discord.ext import commands

intents = discord.Intents().default()
intents.members = True
intents.guilds = True

bot = commands.Bot(description="Make threads better!", intents=intents, help_command=None, case_insensitive=True, strip_after_prefix=True, debug_guilds=[764385563289452545])
bot.owner_id = 243759220057571328