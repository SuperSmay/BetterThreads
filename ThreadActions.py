import asyncio
from asyncio import threads
import discord
import logging
import sqlite3

from GlobalVariables import bot

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

TABLE_NAME = 'thread_ids'
TABLE_SIGNATURE = 'thread_id INT PRIMARY KEY, guild_id INT'

async def add_users_to_thread(thread: discord.Thread, members: list[discord.Member]):
    complete_list = [f'<@{member.id}>' for member in members]
    # complete_list = [f'<@812156805244911647>', '<@332653982470242314>']
    current_list = complete_list.copy()
    while len(current_list) > 0:
        current_string = ''
        while len(current_string) < 1900 and len(current_list) > 0:
            current_string += current_list[0]
            del(current_list[0])
        message = await thread.send(content=current_string)
        logger.info('Mass ping message sent')
        await message.delete()

def add_thread_to_archive_prevention(thread: discord.Thread):
    with sqlite3.Connection('thread_id_list.sqlite') as con:
        cur = con.cursor()
        cur.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} ({TABLE_SIGNATURE})")
        cur.execute(f"INSERT OR IGNORE INTO {TABLE_NAME} VALUES (?, ?)", (thread.id, thread.guild.id))
            

def remove_thread_from_archive_prevention(thread: discord.Thread):
    with sqlite3.Connection('thread_id_list.sqlite') as con:
        cur = con.cursor()
        cur.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} ({TABLE_SIGNATURE})")
        cur.execute(f"DELETE FROM {TABLE_NAME} WHERE thread_id = (?)", (thread.id,))

async def run_on_loop():
    with sqlite3.Connection('thread_id_list.sqlite') as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        columns: list[sqlite3.Row] = cur.execute(f"SELECT * FROM {TABLE_NAME}").fetchall()

        for column in columns:
            # Fetch the guild and give up if guild not found
            try:
                # Try just getting it from the cache
                guild = bot.get_guild(column['guild_id'])

                # Go fetch it if it's not in the cache
                if guild is None:
                    guild = await bot.fetch_guild(column['guild_id'])

            # Fail if guild isn't found
            except discord.errors.Forbidden:
                logger.warning(f"Failed to fetch guild {column['guild_id']}, removing thread from archive prevention list")
                remove_thread_from_archive_prevention(thread)
                return

            try:
                # Try just getting it from the cache
                thread = guild.get_channel(column['thread_id'])

                # Go fetch it if it's not in the cache
                if thread is None:
                    thread = await guild.fetch_channel(column['thread_id'])

            # Fail if thread isn't found
            except discord.errors.Forbidden or discord.errors.NotFound:
                logger.warning(f"Failed to fetch thread {column['thread_id']}, removing from archive prevention list")
                remove_thread_from_archive_prevention(thread)
                return

            # Fail if thread is somehow not a thread
            if not isinstance(thread, discord.Thread):
                logger.warning(f"Thread {column['thread_id']} is not a thread, removing from archive prevention list")
                remove_thread_from_archive_prevention(thread)
                return

            # Fail if thread is locked. This is almost certainly an intentional action by a user and should be respected
            if thread.locked:
                logger.info(f"Thread {column['thread_id']} is locked, removing from archive prevention list")
                remove_thread_from_archive_prevention(thread)
                return

            bot.loop.create_task(archive_cycle(thread))
            logger.info(f"Archive cycle started for thread {column['thread_id']}")

async def archive_cycle(thread: discord.Thread):
    # Do the thing. This is better than sending a message because it won't send a notification anywhere
    try:
        await thread.archive()
        await asyncio.sleep(2)
        await thread.unarchive()

        logger.info(f"Thread {thread.id} successfully archive cycled")
    except discord.errors.Forbidden or discord.errors.NotFound:
        logger.warn(f"Thread {thread.id} could not be archive cycled, removing from archive prevention list")
        remove_thread_from_archive_prevention(thread)

async def unarchive_if_tracked(thread: discord.Thread):
    with sqlite3.Connection('thread_id_list.sqlite') as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        columns: list[sqlite3.Row] = cur.execute(f"SELECT * FROM {TABLE_NAME}").fetchall()

        if thread.id in [col['thread_id'] for col in columns]:
            # Fail if thread is somehow not a thread
            if not isinstance(thread, discord.Thread):
                logger.warning(f"Thread {thread.id} is not a thread, removing from archive prevention list")
                remove_thread_from_archive_prevention(thread)
                return

            # Fail if thread is locked. This is almost certainly an intentional action by a user and should be respected
            if thread.locked:
                logger.info(f"Thread {thread.id} is locked, removing from archive prevention list")
                remove_thread_from_archive_prevention(thread)
                return

            try:
                await thread.unarchive()
                logger.info(f"Thread {thread.id} successfully unarchived")

            except discord.errors.Forbidden or discord.errors.NotFound:
                logger.warn(f"Thread {thread.id} could not be unarchived, removing from archive prevention list")
                remove_thread_from_archive_prevention(thread)