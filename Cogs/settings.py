import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
import json
import datetime


class Settings(commands.Cog):
  def __init__(self, client):
    self.client = client


  async def logchannel(self):
    with open("log_channels.json", "r") as f:
        logger = json.load(f)

        return logger
  

  @commands.command(hidden=True)
  @commands.guild_only()
  @has_permissions(administrator=True)
  async def log(self, ctx, channel: discord.TextChannel):
      with open('log_channels.json', 'r', encoding='utf-8') as f:
          log_channel = json.load(f)

      try:
          log_channel[str(ctx.guild.id)] = channel.id
      except KeyError:
          new = {str(ctx.guild.id): channel.id}
          log_channel.update(new)

      await ctx.send(f"Moderation log channel set to: {channel.mention}")

      with open('log_channels.json', 'w', encoding='utf-8') as fp:
          json.dump(log_channel, fp, indent=2)


  @commands.command(aliases = ['serverinfo'], help = 'Shows information of the server.')
  async def guildinfo(self, ctx):
    datecreated = ctx.guild.created_at.strftime("%d-%m-%Y")

    category_channels = []
    for category in ctx.guild.channels:
      if str(category.type) == 'category':
        category_channels.append(category)
    categories = len(category_channels)

    role_list = []
    for role in ctx.guild.roles:
      role_list.append(role.name)
    roles = ', '.join(role_list)
    role_count = len(role_list)

    embed = discord.Embed(
      color = discord.Color.purple()
    )

    embed.set_author(name = ctx.guild, icon_url = ctx.guild.icon_url)
    embed.set_footer(text = f'ID: {ctx.guild.id} | Created On • {datecreated}')
    embed.set_thumbnail(url = ctx.guild.icon_url)

    embed.add_field(name = 'Owner', value = ctx.guild.owner, inline = True)
    embed.add_field(name = 'Members', value = ctx.guild.member_count, inline = True)
    embed.add_field(name = 'Roles', value = role_count, inline = True)
    embed.add_field(name = 'Categories', value = categories, inline = True)
    embed.add_field(name = 'Text Channels', value = len(ctx.guild.text_channels), inline = True)
    embed.add_field(name = 'Voice Channels', value = len(ctx.guild.voice_channels), inline = True)
    if ctx.author.guild_permissions.administrator:
      embed.add_field(name = 'Role List', value = roles, inline = False)

    await ctx.send(embed = embed)


  @commands.command(aliases = ['configuration'])
  async def config(self, ctx):
    with open('log_channels.json', 'r') as f:
      logger = json.load(f)
    if str(ctx.guild.id) in logger:
      logcnl = self.client.get_channel(logger[str(ctx.guild.id)])
      channel = logcnl.mention
    else:
      channel = 'No log channel found. Use `log` command to set up moderation log channel. [Administrative permission is required to run this command]'
    embed = discord.Embed(
      title = ctx.guild,
      color = discord.Color.purple(),
      timestamp = datetime.datetime.now()
    )
    embed.set_author(name = 'Configuration', icon_url = self.client.user.display_avatar.url)
    embed.set_thumbnail(url = ctx.guild.icon_url)
    embed.add_field(name = 'Prefix', value = '`i.` or `@mention`\nType ***i.help*** or ***`@Inevitable` help*** to get started.', inline = False)
    embed.add_field(name = 'Log Channel', value = channel, inline = False)
    embed.add_field(name = 'Useful Links', value = '[Invite](https://dsc.gg/inevitablebot) • [Vote](https://top.gg/bot/920757063599132683/vote) • [Support Server](https://discord.gg/F9N8DmsJyz)', inline = False)
    embed.set_footer(text = f'Requested by {ctx.author}', icon_url = ctx.author.display_avatar.url)
    await ctx.send(embed = embed)


async def setup(client):
  await client.add_cog(Settings(client))