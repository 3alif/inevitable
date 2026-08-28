import discord
from discord.ext import commands
from discord import app_commands
import json
import datetime


class Settings(commands.Cog):
  def __init__(self, client):
    self.client = client


  # async def logchannel(self):
  #   with open("log_channels.json", "r") as f:
  #       logger = json.load(f)

  #       return logger
  

  # @app_commands.command(name = 'log', description = 'Sets the moderation log channel.')
  # @app_commands.describe(channel = 'The channel where moderation logs will be sent.')
  # @app_commands.checks.has_permissions(administrator=True)
  # @app_commands.guild_only()
  # async def log(self, interaction: discord.Interaction, channel: discord.TextChannel):
  #     with open('log_channels.json', 'r', encoding='utf-8') as f:
  #         log_channel = json.load(f)

  #     try:
  #         log_channel[str(interaction.guild.id)] = channel.id
  #     except KeyError:
  #         new = {str(interaction.guild.id): channel.id}
  #         log_channel.update(new)

  #     await interaction.response.send_message(f"Moderation log channel set to: {channel.mention}")

  #     with open('log_channels.json', 'w', encoding='utf-8') as fp:
  #         json.dump(log_channel, fp, indent=2)


  @app_commands.command(name = 'serverinfo', description = 'Shows information of the server.')
  async def serverinfo(self, interaction: discord.Interaction):
    await interaction.response.defer()

    guild = interaction.guild
    datecreated = guild.created_at.strftime("%d-%m-%Y")

    role_list = [role.name for role in guild.roles if role.name != "@everyone"]
    role_count = len(role_list)

    roles = ', '.join(role_list)
    if len(roles) > 1024:
      roles = roles[:1020] + '...'

    embed = discord.Embed(
      color = discord.Color.purple()
    )

    if guild.icon:
      embed.set_author(name = guild.name, icon_url = guild.icon.url)
      embed.set_thumbnail(url = guild.icon.url)
    else:
      embed.set_author(name = guild.name)

    embed.set_footer(text = f'ID: {guild.id} | Created On • {datecreated}')

    embed.set_thumbnail(url = interaction.guild.icon_url)

    embed.add_field(name = 'Owner', value = interaction.guild.owner, inline = True)
    embed.add_field(name = 'Members', value = interaction.guild.member_count, inline = True)
    embed.add_field(name = 'Roles', value = role_count, inline = True)
    embed.add_field(name = 'Categories', value = len(guild.categories), inline = True)
    embed.add_field(name = 'Text Channels', value = len(interaction.guild.text_channels), inline = True)
    embed.add_field(name = 'Voice Channels', value = len(interaction.guild.voice_channels), inline = True)
    if interaction.user.guild_permissions.administrator and role_list:
      embed.add_field(name = 'Role List', value = roles, inline = False)

    await interaction.followup.send(embed = embed)


  # @app_commands.command(name = 'config', description = 'Shows configuration information of the server.')
  # async def config(self, interaction: discord.Interaction):
  #   with open('log_channels.json', 'r') as f:
  #     logger = json.load(f)
  #   if str(interaction.guild.id) in logger:
  #     logcnl = self.client.get_channel(logger[str(interaction.guild.id)])
  #     channel = logcnl.mention
  #   else:
  #     channel = 'No log channel found. Use `/log` command to set up moderation log channel. [Administrative permission is required to run this command]'
  #   embed = discord.Embed(
  #     title = interaction.guild,
  #     color = discord.Color.purple(),
  #     timestamp = datetime.datetime.now()
  #   )
  #   embed.set_author(name = 'Configuration', icon_url = self.client.user.display_avatar.url)
  #   embed.set_thumbnail(url = interaction.guild.icon_url)
  #   embed.add_field(name = 'Prefix', value = '`i.` or `@mention`\nUse ***/help*** to get started.', inline = False)
  #   embed.add_field(name = 'Log Channel', value = channel, inline = False)
  #   embed.add_field(name = 'Useful Links', value = '[Invite](https://dsc.gg/inevitablebot) • [Vote](https://top.gg/bot/920757063599132683/vote) • [Support Server](https://discord.gg/F9N8DmsJyz)', inline = False)
  #   embed.set_footer(text = f'Requested by {interaction.user}', icon_url = interaction.user.display_avatar.url)
  #   await interaction.response.send_message(embed = embed)


async def setup(client):
  await client.add_cog(Settings(client))