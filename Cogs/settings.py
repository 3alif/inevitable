import discord
from discord.ext import commands
from discord import app_commands
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
  

  @app_commands.command(name = 'log', description = 'Sets the moderation log channel.')
  @app_commands.describe(channel = 'The channel where moderation logs will be sent.')
  @app_commands.checks.has_permissions(administrator=True)
  @app_commands.guild_only()
  async def log(self, interaction: discord.Interaction, channel: discord.TextChannel):
      with open('log_channels.json', 'r', encoding='utf-8') as f:
          log_channel = json.load(f)

      try:
          log_channel[str(interaction.guild.id)] = channel.id
      except KeyError:
          new = {str(interaction.guild.id): channel.id}
          log_channel.update(new)

      await interaction.response.send_message(f"Moderation log channel set to: {channel.mention}")

      with open('log_channels.json', 'w', encoding='utf-8') as fp:
          json.dump(log_channel, fp, indent=2)


  @app_commands.command(name = 'serverinfo', description = 'Shows information of the server.')
  async def serverinfo(self, interaction: discord.Interaction):
    datecreated = interaction.guild.created_at.strftime("%d-%m-%Y")

    category_channels = []
    for category in interaction.guild.channels:
      if str(category.type) == 'category':
        category_channels.append(category)
    categories = len(category_channels)

    role_list = []
    for role in interaction.guild.roles:
      role_list.append(role.name)
    roles = ', '.join(role_list)
    role_count = len(role_list)

    embed = discord.Embed(
      color = discord.Color.purple()
    )

    embed.set_author(name = interaction.guild, icon_url = interaction.guild.icon_url)
    embed.set_footer(text = f'ID: {interaction.guild.id} | Created On • {datecreated}')
    embed.set_thumbnail(url = interaction.guild.icon_url)

    embed.add_field(name = 'Owner', value = interaction.guild.owner, inline = True)
    embed.add_field(name = 'Members', value = interaction.guild.member_count, inline = True)
    embed.add_field(name = 'Roles', value = role_count, inline = True)
    embed.add_field(name = 'Categories', value = categories, inline = True)
    embed.add_field(name = 'Text Channels', value = len(interaction.guild.text_channels), inline = True)
    embed.add_field(name = 'Voice Channels', value = len(interaction.guild.voice_channels), inline = True)
    if interaction.user.guild_permissions.administrator:
      embed.add_field(name = 'Role List', value = roles, inline = False)

    await interaction.response.send_message(embed = embed)


  @app_commands.command(name = 'config', description = 'Shows configuration information of the server.')
  async def config(self, interaction: discord.Interaction):
    with open('log_channels.json', 'r') as f:
      logger = json.load(f)
    if str(interaction.guild.id) in logger:
      logcnl = self.client.get_channel(logger[str(interaction.guild.id)])
      channel = logcnl.mention
    else:
      channel = 'No log channel found. Use `/log` command to set up moderation log channel. [Administrative permission is required to run this command]'
    embed = discord.Embed(
      title = interaction.guild,
      color = discord.Color.purple(),
      timestamp = datetime.datetime.now()
    )
    embed.set_author(name = 'Configuration', icon_url = self.client.user.display_avatar.url)
    embed.set_thumbnail(url = interaction.guild.icon_url)
    embed.add_field(name = 'Prefix', value = '`i.` or `@mention`\nUse ***/help*** to get started.', inline = False)
    embed.add_field(name = 'Log Channel', value = channel, inline = False)
    embed.add_field(name = 'Useful Links', value = '[Invite](https://dsc.gg/inevitablebot) • [Vote](https://top.gg/bot/920757063599132683/vote) • [Support Server](https://discord.gg/F9N8DmsJyz)', inline = False)
    embed.set_footer(text = f'Requested by {interaction.user}', icon_url = interaction.user.display_avatar.url)
    await interaction.response.send_message(embed = embed)


async def setup(client):
  await client.add_cog(Settings(client))