import asyncio
import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import datetime
from server import online
from db import get_log_channel
import traceback
from discord import app_commands


load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
VERSION = '0.9'


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True
        intents.members = True
        intents.message_content = True
        intents.presences = False
        super().__init__(
          command_prefix = commands.when_mentioned,
          help_command = None,
          intents = intents,
          application_id = 920757063599132683
        )

    async def setup_hook(self):
        for filename in os.listdir('./Cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'Cogs.{filename[:-3]}')
        self.tree.on_error = self.on_app_command_error
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Ensures every slash command failure still gets a response instead of hanging silently."""
        if isinstance(error, app_commands.MissingPermissions):
            msg = "❌ You don't have permission to use this command."
        elif isinstance(error, app_commands.NoPrivateMessage):
            msg = "❌ This command can only be used in a server."
        elif isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ This command is on cooldown. Try again in {error.retry_after:.1f}s."
        else:
            msg = "⚠️ Something went wrong running that command. It's been logged."
            print(f"[APP COMMAND ERROR] {interaction.command.name if interaction.command else 'unknown'}: {error}", flush=True)
            traceback.print_exception(type(error), error, error.__traceback__)

        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except discord.HTTPException:
            pass

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name='/help'))
        await self.tree.sync()
        print(f"imma ready in {len(self.guilds)} servers")


    async def _get_log_channel(self, guild_id: int):
        """Helper to fetch the log channel object for a guild."""
        channel_id = await get_log_channel(guild_id)
        if channel_id:
            return self.get_channel(channel_id)
        return None


    async def on_member_join(self, member):
        logcnl = await self._get_log_channel(member.guild.id)
        if logcnl:
            log = discord.Embed(
                title = 'Member Joined',
                description = f'{member} | {member.mention}',
                color = discord.Color.green(),
                timestamp = datetime.datetime.now()
            )
            log.set_author(name=str(member.guild), icon_url=member.guild.icon.url if member.guild.icon else None)
            log.set_thumbnail(url=member.display_avatar.url)
            account_age = datetime.datetime.now(datetime.timezone.utc) - member.created_at
            log.add_field(name='Account Age', value=str(account_age).split('.')[0], inline=False)
            log.set_footer(text=f'ID: {member.id}')
            await logcnl.send(embed=log)


    async def on_member_remove(self, member):
        logcnl = await self._get_log_channel(member.guild.id)
        if logcnl:
            log = discord.Embed(
                title = 'Member Left',
                description = f'{member} | {member.mention}',
                color = discord.Color.red(),
                timestamp = datetime.datetime.now()
            )
            log.set_author(name=str(member.guild), icon_url=member.guild.icon.url if member.guild.icon else None)
            log.set_footer(text=f'ID: {member.id}')
            await logcnl.send(embed=log)


    async def on_member_update(self, before, after):
        if before.display_name == after.display_name:
            return
        logcnl = await self._get_log_channel(before.guild.id)
        if logcnl:
            log = discord.Embed(
                description = f'**{before.mention} nickname changed**',
                color = discord.Color.dark_grey(),
                timestamp = datetime.datetime.now()
            )
            log.set_author(name=str(after), icon_url=after.display_avatar.url)
            log.add_field(name='Before', value=before.display_name, inline=False)
            log.add_field(name='After', value=after.display_name, inline=False)
            log.set_footer(text=f'ID: {after.id}')
            await logcnl.send(embed=log)


    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return
        logcnl = await self._get_log_channel(message.guild.id)
        if logcnl:
            content = message.content if message.content else '*[No text content]*'
            if len(content) > 1000:
                content = content[:1000] + '...'
            log = discord.Embed(
                description = f'**Message by {message.author.mention} deleted in {message.channel.mention}**\n{content}',
                color = discord.Color.dark_grey(),
                timestamp = datetime.datetime.now()
            )
            log.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
            log.set_footer(text=f'User ID: {message.author.id} | Message ID: {message.id}')
            await logcnl.send(embed=log)


    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild:
            return
        # Ignore embed-only updates (e.g. link previews loading in)
        if not before.embeds and after.embeds:
            return
        if before.content == after.content:
            return
        logcnl = await self._get_log_channel(before.guild.id)
        if logcnl:
            bedit = before.content[:500] + '...' if len(before.content) > 500 else before.content
            aedit = after.content[:500] + '...' if len(after.content) > 500 else after.content
            log = discord.Embed(
                description = f'**Message by {before.author.mention} edited in {before.channel.mention}** [[Jump]({after.jump_url})]',
                color = discord.Color.dark_grey(),
                timestamp = after.edited_at or datetime.datetime.now()
            )
            log.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)
            log.set_footer(text=f'User ID: {before.author.id} | Message ID: {after.id}')
            log.add_field(name='Before', value=bedit or '*[empty]*', inline=False)
            log.add_field(name='After', value=aedit or '*[empty]*', inline=False)
            await logcnl.send(embed=log)


    async def on_voice_state_update(self, member, before, after):
        if not (before.channel or after.channel):
            return
        guild_id = (before.channel or after.channel).guild.id
        logcnl = await self._get_log_channel(guild_id)
        if not logcnl:
            return

        des = ''
        if before.channel is not None:
            if after.channel is not None and before.channel != after.channel:
                des = f'{member.mention} switched from {before.channel.mention} to {after.channel.mention}'
            elif after.channel is None:
                des = f'{member.mention} left voice channel {before.channel.mention}'
        else:
            if after.channel is not None:
                des = f'{member.mention} joined voice channel {after.channel.mention}'

        if des:
            log = discord.Embed(
                description=des,
                color=discord.Color.dark_grey(),
                timestamp=datetime.datetime.now()
            )
            log.set_author(name=str(member), icon_url=member.display_avatar.url)
            log.set_footer(text=f'ID: {member.id}')
            await logcnl.send(embed=log)



if __name__ == '__main__':
    online()

    client = MyBot()

    async def main():
      async with client:
        await client.start(TOKEN)

    asyncio.run(main())
