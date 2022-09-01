import asyncio
import logging
import discord
from discord.ext import commands
from GlobalVariables import bot

import ThreadActions

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class ThreadResponder(commands.Cog):

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        await self.send_thread_options(thread)

    async def send_thread_options(self, thread: discord.Thread):
        view = self.ThreadResponseView()
        embed = discord.Embed(description='Thread Options', color=8435455)
        await thread.send(embed=embed, view=view)

    class ThreadResponseView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(self.AddUsersButton())
            self.add_item(self.PreventArchiveButton())
            self.add_item(self.AllowArchiveButton())


        class AddUsersButton(discord.ui.Button):
            def __init__(self):
                super().__init__(style=discord.enums.ButtonStyle.blurple, label='Add All Users (this will ping everyone!)', custom_id='add_all_users_button')

            async def callback(self, interaction: discord.Interaction):
                logger.info(f'Add members button for guild {interaction.guild_id}')

                if not interaction.channel.permissions_for(interaction.user).mention_everyone:
                    await interaction.response.send_message(content='Sorry, you need @everyone permission to use that', ephemeral=True)
                    return

                self.disabled = True
                message = interaction.message
                content = message.content
                view = self.view
                embeds = message.embeds

                await message.edit(content=content, view=view, embeds=embeds)
                await interaction.response.send_message(content='`Adding all members... (This may take several seconds)`')
                if isinstance(interaction.channel, discord.Thread):
                    await ThreadActions.add_users_to_thread(interaction.channel, interaction.channel.parent.members)
                await interaction.delete_original_message()
                await interaction.followup.send(content='`All users added!`', delete_after=5)

        class PreventArchiveButton(discord.ui.Button):
            def __init__(self):
                super().__init__(style=discord.enums.ButtonStyle.blurple, label='Prevent Thread Auto-Archive', custom_id='prevent_autoarchive_button')

            async def callback(self, interaction: discord.Interaction):
                logger.info(f'Adding thread {interaction.channel_id} to archive prevention')

                if not interaction.channel.permissions_for(interaction.user).manage_threads:
                    await interaction.response.send_message(content='Sorry, you need manage threads permission to use that', ephemeral=True)
                    return

                await interaction.response.send_message(content='`This thread will not auto archive`', delete_after=5)
                if isinstance(interaction.channel, discord.Thread):
                    ThreadActions.add_thread_to_archive_prevention(thread=interaction.channel)

        class AllowArchiveButton(discord.ui.Button):
            def __init__(self):
                super().__init__(style=discord.enums.ButtonStyle.gray, label='Allow Thread Auto-Archive', custom_id='allow_autoarchive_button')

            async def callback(self, interaction: discord.Interaction):
                logger.info(f'Remove thread {interaction.channel_id} from archive prevention')

                if not interaction.channel.permissions_for(interaction.user).manage_threads:
                    await interaction.response.send_message(content='Sorry, you need manage threads permission to use that', ephemeral=True)
                    return

                await interaction.response.send_message(content='`This thread will auto archive normally`', delete_after=5)
                if isinstance(interaction.channel, discord.Thread):
                    ThreadActions.add_thread_to_archive_prevention(thread=interaction.channel)

        

