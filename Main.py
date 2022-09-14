from asyncio import tasks
import pathlib
import discord
from discord.ext import commands, tasks
import logging
import ThreadResponder
import ThreadActions
from GlobalVariables import bot



logging.basicConfig()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

tokenFile = open(pathlib.Path('token'), 'r')
TOKEN = tokenFile.read()


persistent_views_added = False

@bot.event
async def on_ready():

    global persistent_views_added
    if not persistent_views_added:
        bot.add_view(bot.get_cog('ThreadResponder').ThreadResponseView())
        persistent_views_added = True

    try:
        thread_archive_prevention.start()
    except RuntimeError:  # If the task is already running, do a loop because the bot lost connection at some point
        await ThreadActions.run_on_loop()


    logger.info(f'Bot startup complete. Logged in as {bot.user}')
    async for guild in bot.fetch_guilds(limit=150):
        logger.info(f'Logged in to guild: {guild.name}')

# disable_group = bot.create_group(name='disable', description="Disable commands")

@bot.slash_command(name='prevent-autoarchive', description="Stop a thread from automatically archiving")
async def prevent_autoarchive(ctx: discord.ApplicationContext, thread: discord.Option(discord.Thread)):

    logger.info(f"Adding thread {thread.id} to archive prevention list")

    if not isinstance(thread, discord.Thread):
        await ctx.respond(f"{thread} is not a thread!")
        return

    ThreadActions.add_thread_to_archive_prevention(thread=thread)

    await ctx.respond(f"`{thread.name} will not auto archive`")

@bot.slash_command(name='allow-autoarchive', description="Allow a thread to automatically archive")
async def allow_autoarchive(ctx: discord.ApplicationContext, thread: discord.Option(discord.Thread)):

    logger.info(f"Removing thread {thread.id} from archive prevention list")

    if not isinstance(thread, discord.Thread):
        await ctx.respond(f"{thread} is not a thread!")
        return

    ThreadActions.remove_thread_from_archive_prevention(thread_id=thread.id)

    await ctx.respond(f'`{thread.name} will auto archive normally`')

@tasks.loop(seconds=3000)  # Run a bit before every hour
async def thread_archive_prevention():
    await ThreadActions.run_on_loop()




def start():
    logger.info("Bot starting up...")
    bot.add_cog(ThreadResponder.ThreadResponder())
    bot.run(token=TOKEN)

if __name__ == '__main__':
    start()