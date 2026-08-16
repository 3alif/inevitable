import discord
from discord.ext import commands
from discord import app_commands
import datetime
import time
import psutil
import platform
import random
from main import VERSION


class Misc(commands.Cog):
  def __init__(self, client):
    self.client = client


  @app_commands.command(help = 'Shows the bot\'s latency.')
  async def ping(self, interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! :smirk: `{round(self.client.latency * 1000)} ms`")


  @app_commands.command(help = 'Gives you a random number from 1 to 6.')
  async def dice(self, interaction: discord.Interaction):
    number = ['1', '2', '3', '4', '5', '6']
    await interaction.response.send_message('🎲 You have got ' + random.choice(number))


  @commands.command(aliases = ['av'], help = 'Shows avatar of an user.')
  async def avatar(self, ctx, uid = None):
    image = ctx.author.display_avatar.url
    name = ctx.author.name

    if not uid == None:
      member = await ctx.guild.fetch_member(uid)
      image = member.display_avatar.url
      name = member.name
    
    embed = discord.Embed(
      title = f'{name}\'s Avatar',
      color = discord.Colour.purple()
    )
    embed.set_image(url = image)
    await ctx.send(embed = embed)


  @commands.command(aliases = ['statistics'], help = 'Shows the current statistics of Inevitable.')
  async def stats(self, ctx):
    proc = psutil.Process()

    with proc.oneshot():
      uptime = datetime.timedelta(seconds = round(time.time() - proc.create_time()))
    ut_str = f'{uptime}'
    ut_h, ut_m, ut_s = ut_str.split(':')
    if ut_h == '0':
      hour = ''
    elif ut_h == '1':
      hour = f'{ut_h} Hour, '
    else:
      hour = f'{ut_h} Hours, '
    minute = f'{ut_m} Min, '
    second = f'{ut_s} Sec'

    cpu_usage = round(psutil.cpu_percent())

    mem_tot = psutil.virtual_memory().total / (1024**2)
    mem_of_tot = proc.memory_percent()
    mem_usage = round(mem_tot * (mem_of_tot / 100))
    
    pyver = platform.python_version()
    dpyver = discord.__version__
    servers = len(self.client.guilds)
    
    channel_list = []
    for guild in self.client.guilds:
      for channel in guild.channels:
        if str(channel.type) == 'text':
          channel_list.append(channel)
        if str(channel.type) == 'voice':
          channel_list.append(channel)
    channel_count = len(channel_list)

    members = 0
    for guild in self.client.guilds:
      members += guild.member_count

    embed = discord.Embed(
      title = 'Inevitable',
      description = f'[Invite](https://dsc.gg/inevitablebot) • [Vote](https://top.gg/bot/920757063599132683/vote) • [Support Server](https://discord.gg/F9N8DmsJyz)',
      colour = discord.Colour.orange(),
      timestamp = datetime.datetime.now()
    )

    embed.set_author(name = 'Statistics', icon_url = self.client.user.display_avatar.url)
    embed.set_footer(text = f'Requested by {ctx.author}', icon_url = ctx.author.display_avatar.url)
    embed.set_thumbnail(url = self.client.user.display_avatar.url)
    embed.add_field(name = 'Uptime', value = f'`{hour}{minute}{second}`', inline = True)
    embed.add_field(name = 'Memory Usage', value = f'`{mem_usage}`', inline = True)
    embed.add_field(name = 'CPU Usage', value = f'`{cpu_usage}%`', inline = True)
    embed.add_field(name = 'Servers', value = f'`{servers}`', inline = True)
    embed.add_field(name = 'Channels', value = f'`{channel_count}`', inline = True)
    embed.add_field(name = 'Members', value = f'`{members}`', inline = True)
    embed.add_field(name = 'discord.py', value = f'`v{dpyver}`', inline = True)
    embed.add_field(name = 'Python', value = f'`v{pyver}`', inline = True)
    embed.add_field(name = 'Inevitable', value = f'`v{VERSION}`', inline = True)

    await ctx.send(embed = embed)


  @commands.command(help = 'Shows this message.')
  async def help(self, ctx, category = None):
    if category == 'moderation' or category == 'Moderation':
      modEmbed = discord.Embed(
        title = 'Moderation Commands',
        description = 'Cooldown: 3 seconds',
        color = discord.Color.gold()
      )
      modEmbed.set_author(name = 'Inevitable', icon_url = self.client.user.display_avatar.url)
      modEmbed.add_field(name = 'lang', value = '```Permission: Manage Messages\nUsage: i.lang [USER_ID] [LANGUAGE]\nAliases: language```', inline = False)
      modEmbed.add_field(name = 'topic', value = '```Permission: Manage Messages\nUsage: i.topic [USER_ID] #off-topic-channel```', inline = False)
      modEmbed.add_field(name = 'clear', value = '```Permission: Administrator\nUsage: i.clear [AMOUNT]\nAliases: purge```', inline = False)
      modEmbed.add_field(name = 'kick', value = '```Permission: Kick Members\nUsage: i.kick [USER_ID] {reason}```', inline = False)
      modEmbed.add_field(name = 'ban', value = '```Permission: Ban Members\nUsage: i.ban [USER_ID] {reason}```', inline = False)
      modEmbed.add_field(name = 'unban', value = '```Permission: Ban Members\nUsage: i.unban [USER_ID] {reason}```', inline = False)
      modEmbed.add_field(name = 'notice', value = '```Permission: Administrator\nUsage: i.notice #channel-mention {message}```', inline = False)
      modEmbed.add_field(name = 'announce', value = '```Permission: Administrator\nUsage: i.announce #channel-mention {message}```', inline = False)
      await ctx.send(embed = modEmbed)

    elif category == 'settings' or category == 'Settings':
      setEmbed = discord.Embed(
        title = 'Setting Commands',
        color = discord.Color.gold()
      )
      setEmbed.set_author(name = 'Inevitable', icon_url = self.client.user.display_avatar.url)
      setEmbed.add_field(name = 'guildinfo', value = '```Usage: i.guildinfo\nAliases: serverinfo```', inline = False)
      setEmbed.add_field(name = 'log', value = '```Permission: Administrator\nUsage: i.log #channel-mention```', inline = False)
      setEmbed.add_field(name = 'config', value = '```Usage: i.config```', inline = False)
      await ctx.send(embed = setEmbed)

    # elif category == 'music' or category == 'Music':
    #   musicEmbed = discord.Embed(
    #     title = 'Music Commands',
    #     color = discord.Color.gold()
    #   )
    #   musicEmbed.set_author(name = 'Inevitable', icon_url = self.client.user.display_avatar.url)
    #   musicEmbed.add_field(name = 'join', value = '```Usage: i.join\nAliases: connect```', inline = False)
    #   musicEmbed.add_field(name = 'leave', value = '```Usage: i.leave\nAliases: disconnect, dc```', inline = False)
    #   musicEmbed.add_field(name = 'play', value = '```Usage: i.play {song}\nAliases: p```', inline = False)
    #   musicEmbed.add_field(name = 'queue', value = '```Usage: i.queue```', inline = False)
    #   musicEmbed.add_field(name = 'pause', value = '```Usage: i.pause```', inline = False)
    #   musicEmbed.add_field(name = 'resume', value = '```Usage: i.resume```', inline = False)
    #   musicEmbed.add_field(name = 'skip', value = '```Usage: i.skip```', inline = False)
    #   musicEmbed.add_field(name = 'stop', value = '```Usage: i.stop```', inline = False)
    #   await ctx.send(embed = musicEmbed)

    elif category == 'misc' or category == 'Misc':
      miscEmbed = discord.Embed(
        title = 'Miscellaneous Commands',
        color = discord.Color.gold()
      )
      miscEmbed.set_author(name = 'Inevitable', icon_url = self.client.user.display_avatar.url)
      miscEmbed.add_field(name = 'help', value = '```Usage: i.help {category}(Optional)```', inline = False)
      miscEmbed.add_field(name = 'ping', value = '```Usage: i.ping```', inline = False)
      miscEmbed.add_field(name = 'stats', value = '```Usage: i.stats\nAliases: statistics```', inline = False)
      miscEmbed.add_field(name = 'avatar', value = '```Usage: i.avatar [USER_ID](Optional)\nAliases: av```', inline = False)
      miscEmbed.add_field(name = 'dice', value = '```Usage: i.dice```', inline = False)
      await ctx.send(embed = miscEmbed)

    else:
      helpEmbed = discord.Embed(
        description = '[Invite](https://dsc.gg/inevitablebot) • [Vote](https://top.gg/bot/920757063599132683/vote) • [Support Server](https://discord.gg/F9N8DmsJyz)\nType `ihelp <category>` for more information regarding a specific category.',
        color = discord.Colour.orange(),
        timestamp = datetime.datetime.now()
      )
  
      helpEmbed.set_author(name = 'Commands', icon_url = self.client.user.display_avatar.url)
      helpEmbed.add_field(name = 'Moderation', value = '`lang`, `topic`, `clear`, `kick`, `ban`, `unban`, `notice`, `announce`', inline = False)
      helpEmbed.add_field(name = 'Settings', value = '`guildinfo`, `log`, `config`', inline = False)
      helpEmbed.add_field(name = 'Music', value = '`join`, `leave`, `play`, `queue`, `pause`, `resume`, `skip`, `stop`', inline = False)
      helpEmbed.add_field(name = 'Misc', value = '`help`, `ping`, `stats`, `avatar`, `dice`', inline = False)
      helpEmbed.set_footer(text = f'Requested by {ctx.author}', icon_url = ctx.author.display_avatar.url)
  
      await ctx.send(embed = helpEmbed)
      await ctx.send('Need more help? Join the official support server, if you can\'t understand something: https://discord.gg/F9N8DmsJyz')


async def setup(client):
  await client.add_cog(Misc(client))
