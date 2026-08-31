import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import datetime
import time
import psutil
import platform
from main import VERSION
import random

class Misc(commands.Cog):
  def __init__(self, client):
    self.client = client

  @commands.Cog.listener()
  async def on_message(self, message):
    # Ignore messages from bots so it doesn't loop
    if message.author.bot:
        return
        
    if "inevitable" in message.content.lower():
        greetings = [
            "Summoning me? ✨\n",
            "You called? 👀\n",
            "Someone said my name!\n",
            "Did I hear 'inevitable'? 😉\n",
            "",
            ""
        ]
        tips = [
            "Tip: You can use `/help` to see all my commands! 📚",
            "Did you know? You can play hot potato using `/hotpotato start` 🥔💥",
            "Tip: Try `/ping` to see how fast I'm running today! 🏓",
            "Fun fact: I am... inevitable. 😈",
            "Tip: Use `/stats` to see my current uptime and server count! 📈",
            "Bored? Roll a dice with `/dice`! 🎲",
            "Need to clean up chat? Server admins can use `/purge` to sweep things away! 🧹"
        ]
        
        greeting = random.choice(greetings)
        tip = random.choice(tips)
        
        reply = f"{greeting}**{tip}**"
        await message.channel.send(reply)


  @app_commands.command(name = 'ping', description = 'Shows the bot\'s latency.')
  async def ping(self, interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! :smirk: `{round(self.client.latency * 1000)} ms`")


  @app_commands.command(name = 'avatar', description = 'Shows avatar of an user.')
  @app_commands.describe(member = 'The member whose avatar you want to see.')
  async def avatar(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
    if member is None:
      member = interaction.user
    
    image = member.display_avatar.url
    name = member.name
    
    embed = discord.Embed(
      title = f'{name}\'s Avatar',
      color = discord.Colour.purple(),
      timestamp = datetime.datetime.now()
    )
    embed.set_image(url = image)
    await interaction.response.send_message(embed = embed)


  @app_commands.command(name = 'stats', description = 'Shows the current statistics of Inevitable.')
  async def stats(self, interaction: discord.Interaction):
    await interaction.response.defer()

    proc = psutil.Process()

    with proc.oneshot():
      uptime = datetime.timedelta(seconds = round(time.time() - proc.create_time()))
    
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    ut_str = ""
    if days > 0:
        ut_str += f"{days} Day{'s' if days > 1 else ''}, "
    if hours > 0:
        ut_str += f"{hours} Hour{'s' if hours > 1 else ''}, "
    if minutes > 0:
        ut_str += f"{minutes} Min, "
    ut_str += f"{seconds} Sec"

    cpu_usage = round(proc.cpu_percent()) / psutil.cpu_count()
    mem_usage = round(proc.memory_info().rss / (1024**2))
    
    pyver = platform.python_version()
    dpyver = discord.__version__
    servers = len(self.client.guilds)
    
    total_text_channels = sum(len(guild.text_channels) for guild in self.client.guilds)
    total_voice_channels = sum(len(guild.voice_channels) for guild in self.client.guilds)
    channel_count = total_text_channels + total_voice_channels

    members = sum(guild.member_count for guild in self.client.guilds if guild.member_count)

    embed = discord.Embed(
      title = 'Inevitable',
      description = f'[Invite](https://dsc.gg/inevitablebot) • [Vote](https://top.gg/bot/920757063599132683/vote) • [Support Server](https://discord.gg/F9N8DmsJyz)',
      colour = discord.Colour.orange(),
      timestamp = datetime.datetime.now()
    )

    embed.set_author(name = 'Statistics', icon_url = self.client.user.display_avatar.url)
    embed.set_footer(text = f'Requested by {interaction.user}', icon_url = interaction.user.display_avatar.url)
    embed.set_thumbnail(url = self.client.user.display_avatar.url)
    embed.add_field(name = 'Bot Uptime', value = f'`{ut_str}`', inline = False)
    embed.add_field(name = 'Servers', value = f'`{servers}`', inline = True)
    embed.add_field(name = 'Users', value = f'`{members}`', inline = True)
    embed.add_field(name = 'Channels', value = f'`{channel_count} (Text: {total_text_channels} | Voice: {total_voice_channels})`', inline = True)
    embed.add_field(name = 'CPU Usage', value = f'`{cpu_usage}%`', inline = True)
    embed.add_field(name = 'RAM Usage', value = f'`{mem_usage} MB`', inline = True)
    embed.add_field(name = 'Library Versions', value = f'`Python: v{pyver}\nDiscord.py: v{dpyver}`', inline = False)
    embed.add_field(name = 'Inevitable', value = f'`v{VERSION}`', inline = True)

    await interaction.followup.send(embed = embed)


  help_group = app_commands.Group(name="help", description="Shows commands information.")

  @help_group.command(name='moderation', description='Shows moderation commands.')
  async def help_moderation(self, interaction: discord.Interaction):
    modEmbed = discord.Embed(
      title = 'Moderation Commands',
      description = 'Cooldown: 3 seconds',
      color = discord.Color.gold(),
      timestamp = datetime.datetime.now()
    )
    modEmbed.set_author(name = 'Inevitable', icon_url = self.client.user.display_avatar.url)
    modEmbed.add_field(name = 'lang', value = '```Permission: Manage Messages\nUsage: /lang [MEMBER] [LANGUAGE]```', inline = False)
    modEmbed.add_field(name = 'topic', value = '```Permission: Manage Messages\nUsage: /topic [MEMBER] #off-topic-channel```', inline = False)
    modEmbed.add_field(name = 'purge', value = '```Permission: Administrator\nUsage: /purge [AMOUNT]```', inline = False)
    modEmbed.add_field(name = 'kick', value = '```Permission: Kick Members\nUsage: /kick [MEMBER] {reason}```', inline = False)
    modEmbed.add_field(name = 'ban', value = '```Permission: Ban Members\nUsage: /ban [MEMBER] {reason}```', inline = False)
    modEmbed.add_field(name = 'unban', value = '```Permission: Ban Members\nUsage: /unban [MEMBER] {reason}```', inline = False)
    modEmbed.add_field(name = 'notice', value = '```Permission: Administrator\nUsage: /notice #channel {message}```', inline = False)
    modEmbed.add_field(name = 'announce', value = '```Permission: Administrator\nUsage: /announce #channel {message}```', inline = False)
    modEmbed.add_field(name = 'timeout', value = '```Permission: Moderate Members\nUsage: /timeout [MEMBER] [MINUTES] {reason}```', inline = False)
    modEmbed.set_footer(text = f'Requested by {interaction.user}', icon_url = interaction.user.display_avatar.url)
    await interaction.response.send_message(embed = modEmbed)

  @help_group.command(name='settings', description='Shows settings commands.')
  async def help_settings(self, interaction: discord.Interaction):
    setEmbed = discord.Embed(
      title = 'Settings Commands',
      color = discord.Color.gold(),
      timestamp = datetime.datetime.now()
    )
    setEmbed.set_author(name = 'Inevitable', icon_url = self.client.user.display_avatar.url)
    setEmbed.add_field(name = 'log', value = '```Permission: Administrator\nUsage: /log #channel\nSets the moderation log channel.```', inline = False)
    setEmbed.add_field(name = 'removelog', value = '```Permission: Administrator\nUsage: /removelog\nRemoves the moderation log channel.```', inline = False)
    setEmbed.add_field(name = 'config', value = '```Usage: /config\nShows the current server configuration.```', inline = False)
    setEmbed.add_field(name = 'serverinfo', value = '```Usage: /serverinfo\nShows detailed information about the server.```', inline = False)
    setEmbed.set_footer(text = f'Requested by {interaction.user}', icon_url = interaction.user.display_avatar.url)
    await interaction.response.send_message(embed = setEmbed)

  @help_group.command(name='music', description='Shows music commands.')
  async def help_music(self, interaction: discord.Interaction):
    musicEmbed = discord.Embed(
      title = 'Music Commands',
      color = discord.Color.gold(),
      timestamp = datetime.datetime.now()
    )
    musicEmbed.set_author(name = 'Inevitable', icon_url = self.client.user.display_avatar.url)
    musicEmbed.add_field(name = 'join', value = '```Usage: /join```', inline = False)
    musicEmbed.add_field(name = 'leave', value = '```Usage: /leave```', inline = False)
    musicEmbed.add_field(name = 'play', value = '```Usage: /play [song]```', inline = False)
    musicEmbed.add_field(name = 'queue', value = '```Usage: /queue```', inline = False)
    musicEmbed.add_field(name = 'skip', value = '```Usage: /skip```', inline = False)
    musicEmbed.add_field(name = 'pause', value = '```Usage: /pause```', inline = False)
    musicEmbed.add_field(name = 'resume', value = '```Usage: /resume```', inline = False)
    musicEmbed.add_field(name = 'stop', value = '```Usage: /stop```', inline = False)
    musicEmbed.set_footer(text = f'Requested by {interaction.user}', icon_url = interaction.user.display_avatar.url)
    await interaction.response.send_message(embed = musicEmbed)

  @help_group.command(name='misc', description='Shows miscellaneous commands.')
  async def help_misc(self, interaction: discord.Interaction):
    miscEmbed = discord.Embed(
      title = 'Miscellaneous Commands',
      color = discord.Color.gold(),
      timestamp = datetime.datetime.now()
    )
    miscEmbed.set_author(name = 'Inevitable', icon_url = self.client.user.display_avatar.url)
    miscEmbed.add_field(name = 'help', value = '```Usage: /help [category]```', inline = False)
    miscEmbed.add_field(name = 'ping', value = '```Usage: /ping```', inline = False)
    miscEmbed.add_field(name = 'stats', value = '```Usage: /stats```', inline = False)
    miscEmbed.add_field(name = 'avatar', value = '```Usage: /avatar [MEMBER](Optional)```', inline = False)
    miscEmbed.add_field(name = 'serverinfo', value = '```Usage: /serverinfo```', inline = False)
    miscEmbed.set_footer(text = f'Requested by {interaction.user}', icon_url = interaction.user.display_avatar.url)
    await interaction.response.send_message(embed = miscEmbed)
  
  @help_group.command(name='games', description='Shows game commands.')
  async def help_games(self, interaction: discord.Interaction):
    gameEmbed = discord.Embed(
      title = 'Game Commands',
      color = discord.Color.gold(),
      timestamp = datetime.datetime.now()
    )
    gameEmbed.set_author(name = 'Inevitable', icon_url = self.client.user.display_avatar.url)
    gameEmbed.add_field(name = 'dice', value = '```Usage: /dice```', inline = False)
    gameEmbed.add_field(name = 'hotpotato start', value = '```Usage: /hotpotato start [TIME](Optional)```', inline = False)
    gameEmbed.add_field(name = 'hotpotato pass', value = '```Usage: /hotpotato pass [USER]```', inline = False)
    gameEmbed.add_field(name = 'hotpotato help', value = '```Usage: /hotpotato help```', inline = False)
    gameEmbed.set_footer(text = f'Requested by {interaction.user}', icon_url = interaction.user.display_avatar.url)
    await interaction.response.send_message(embed = gameEmbed)
  
  @help_group.command(name='all', description='Shows all command categories.')
  async def help_all(self, interaction: discord.Interaction):
    helpEmbed = discord.Embed(
      description = '[Invite](https://dsc.gg/inevitablebot) • [Vote](https://top.gg/bot/920757063599132683/vote) • [Support Server](https://discord.gg/F9N8DmsJyz)\nType `/help <category>` for more information regarding a specific category.',
      color = discord.Colour.orange(),
      timestamp = datetime.datetime.now()
    )

    helpEmbed.set_author(name = 'Commands', icon_url = self.client.user.display_avatar.url)
    helpEmbed.add_field(name = 'Moderation', value = '`/lang`, `/topic`, `/purge`, `/kick`, `/ban`, `/unban`, `/timeout`, `/notice`, `/announce`', inline = False)
    helpEmbed.add_field(name = 'Settings', value = '`/log`, `/removelog`, `/config`, `/serverinfo`', inline = False)
    helpEmbed.add_field(name = 'Music', value = '`/join`, `/leave`, `/play`, `/queue`, `/pause`, `/resume`, `/skip`, `/stop`', inline = False)
    helpEmbed.add_field(name = 'Misc', value = '`/ping`, `/stats`, `/avatar`', inline = False)
    helpEmbed.add_field(name = 'Games', value = '`/dice`, `/hotpotato start`, `/hotpotato pass`, `/hotpotato help`', inline = False)
    helpEmbed.set_footer(text = f'Requested by {interaction.user}', icon_url = interaction.user.display_avatar.url)

    await interaction.response.send_message(embed = helpEmbed)
    await interaction.channel.send('Need more help? Join the official support server, if you can\'t understand something: https://discord.gg/F9N8DmsJyz')


async def setup(client):
  await client.add_cog(Misc(client))
