import asyncio
import discord
import os
from dotenv import load_dotenv
import json
from discord.ext import commands
from discord.ext.commands import CommandNotFound
import datetime
from server import online


load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
VERSION = '0.5'


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.presences = False
        super().__init__(
          command_prefix = 'i.',
          help_command = None,
          intents = intents,
          application_id = 920757063599132683
        )

    async def setup_hook(self):
        for filename in os.listdir('./Cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'Cogs.{filename[:-3]}')

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name='i.help | @Inevitable help'))
        print(f"imma ready in {len(self.guilds)} servers")


    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            print(error)
        raise error


    async def on_member_join(self, member):
        with open('log_channels.json', 'r') as f:
            logger = json.load(f)
        if str(member.guild.id) in logger:
            logcnl = self.get_channel(logger[str(member.guild.id)])
            if logcnl and hasattr(logcnl, 'send'):
                log = discord.Embed(
                    title = 'Member Joined',
                    description = f'{member} | {member.mention}',
                    color = discord.Color.dark_grey(),
                    timestamp = datetime.datetime.now()
                )
                log.set_author(name = f'{member.guild}', icon_url = member.guild.icon_url)
                log.set_thumbnail(url = member.avatar_url)
                log.add_field(name = 'Account Age', value = (datetime.datetime.now() - member.created_at), inline=False)
                log.set_footer(text = f'ID: {member.id}')
                await logcnl.send(embed = log)  # type: ignore


    async def on_member_remove(self, member):
        with open('log_channels.json', 'r') as f:
            logger = json.load(f)
        if str(member.guild.id) in logger:
            logcnl = self.get_channel(logger[str(member.guild.id)])
            if logcnl and hasattr(logcnl, 'send'):
                log = discord.Embed(
                    title = 'Member Left',
                    description = f'{member} | {member.mention}',
                    color = discord.Color.dark_grey(),
                    timestamp = datetime.datetime.now()
                )
                log.set_author(name = f'{member.guild}', icon_url = member.guild.icon_url)
                log.set_footer(text = f'ID: {member.id}')
                await logcnl.send(embed = log)  # type: ignore


    async def on_member_update(self, before, after):
        with open('log_channels.json', 'r') as f:
            logger = json.load(f)
        if str(before.guild.id) in logger:
            logcnl = self.get_channel(logger[str(before.guild.id)])
            if logcnl and hasattr(logcnl, 'send') and not before.display_name == after.display_name:
                log = discord.Embed(
                    description = f'**{before.mention} nickname changed**',
                    color = discord.Color.dark_grey(),
                    timestamp = datetime.datetime.now()
                )
                log.set_author(name = after, icon_url=after.avatar_url)
                log.add_field(name = 'Before', value = before.display_name, inline = False)
                log.add_field(name = 'After', value=after.display_name, inline = False)
                log.set_footer(text = f'ID: {after.id}')
                await logcnl.send(embed = log)  # type: ignore


    async def on_message_delete(self, message):
        with open("log_channels.json", "r") as f:
            logger = json.load(f)
        if message.author.bot:
            return
        if len(message.content) > 1000:
            edit = message.content[:1000] + '...'
        else:
            edit = message.content
        if str(message.guild.id) in logger:
            logcnl = self.get_channel(logger[str(message.guild.id)])
            if logcnl and hasattr(logcnl, 'send'):
                log = discord.Embed(
                    description = f'**Message sent by {message.author.mention} deleted in {message.channel.mention}**\n{edit}',
                    color = discord.Color.dark_grey(),
                    timestamp = datetime.datetime.now()
                )
                log.set_author(name = f'{message.author}', icon_url = message.author.avatar_url)
                log.set_footer(text = f'User ID: {message.author.id} | Message ID: {message.id}')
                await logcnl.send(embed = log)  # type: ignore


    async def on_message_edit(self, before, after):
        with open("log_channels.json", "r") as f:
            logger = json.load(f)
        if before.author.bot:
            return
        if not before.embeds and after.embeds:
            return
        if len(before.content) < 500:
            bedit = before.content
        else:
            bedit = before.content[:500] + '...'
        if len(after.content) < 500:
            aedit = after.content
        else:
            aedit = after.content[:500] + '...'
        if str(before.guild.id) in logger:
            logcnl = self.get_channel(logger[str(before.guild.id)])
            if logcnl and hasattr(logcnl, 'send'):
                log = discord.Embed(
                    description = f'**Message sent by {before.author.mention} edited in {before.channel.mention}**',
                    color = discord.Color.dark_grey(),
                    timestamp = after.created_at
                )
                log.set_author(name = f'{before.author}', icon_url=before.author.avatar_url)
                log.set_footer(text = f'User ID: {before.author.id} | Message ID: {after.id}')
                log.add_field(name = 'Before', value = bedit, inline = False)
                log.add_field(name = 'After', value = aedit, inline = False)
                await logcnl.send(embed = log)  # type: ignore


    async def on_voice_state_update(self, member, before, after):
        with open("log_channels.json", "r") as f:
            logger = json.load(f)

        channel = before.channel or after.channel

        if str(channel.guild.id) in logger:
            logcnl = self.get_channel(logger[str(channel.guild.id)])
            if logcnl and hasattr(logcnl, 'send'):
                des = ''
                if before.channel is not None:
                    if after.channel is not None and not before.channel == after.channel:
                        des = f'{member.mention} switched to {after.channel.mention} from {before.channel.mention}'
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
                    log.set_author(name = member, icon_url = member.avatar_url)
                    log.set_footer(text = f'ID: {member.id}')
                    await logcnl.send(embed = log)  # type: ignore



if __name__ == '__main__':
    online()

    client = MyBot()

    async def main():
      async with client:
        await client.start(TOKEN)

    asyncio.run(main())
