import discord
from discord.ext import commands
from discord import app_commands
import datetime
from db import get_log_channel, set_log_channel, remove_log_channel


class Settings(commands.Cog):
  def __init__(self, client):
    self.client = client


  @app_commands.command(name='log', description='Sets the moderation log channel for this server.')
  @app_commands.describe(channel='The channel where moderation logs will be sent.')
  @app_commands.checks.has_permissions(administrator=True)
  @app_commands.guild_only()
  async def log(self, interaction: discord.Interaction, channel: discord.TextChannel):
    await set_log_channel(interaction.guild.id, channel.id)
    embed = discord.Embed(
      description=f'✅ Moderation log channel has been set to {channel.mention}.',
      color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)


  @app_commands.command(name='removelog', description='Removes the moderation log channel for this server.')
  @app_commands.checks.has_permissions(administrator=True)
  @app_commands.guild_only()
  async def removelog(self, interaction: discord.Interaction):
    channel_id = await get_log_channel(interaction.guild.id)
    if channel_id is None:
      await interaction.response.send_message('❌ No log channel is set for this server.', ephemeral=True)
      return
    await remove_log_channel(interaction.guild.id)
    embed = discord.Embed(
      description='✅ Moderation log channel has been removed.',
      color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)


  @app_commands.command(name='config', description='Shows the configuration of the server.')
  async def config(self, interaction: discord.Interaction):
    channel_id = await get_log_channel(interaction.guild.id)
    if channel_id:
      logcnl = self.client.get_channel(channel_id)
      channel_val = logcnl.mention if logcnl else f'Channel not found (ID: {channel_id})'
    else:
      channel_val = 'Not set. Use `/log #channel` to configure. *(Admin only)*'

    embed = discord.Embed(
      title=str(interaction.guild),
      color=discord.Color.purple(),
      timestamp=datetime.datetime.now()
    )
    embed.set_author(name='Configuration', icon_url=self.client.user.display_avatar.url)
    if interaction.guild.icon:
      embed.set_thumbnail(url=interaction.guild.icon.url)
    embed.add_field(name='Prefix', value='`i.` or Slash Commands\nUse ***/help all*** to get started.', inline=False)
    embed.add_field(name='Log Channel', value=channel_val, inline=False)
    embed.add_field(name='Useful Links', value='[Invite](https://dsc.gg/inevitablebot) • [Vote](https://top.gg/bot/920757063599132683/vote) • [Support Server](https://discord.gg/F9N8DmsJyz)', inline=False)
    embed.set_footer(text=f'Requested by {interaction.user}', icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)


  @app_commands.command(name='serverinfo', description='Shows information of the server.')
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
      color=discord.Color.purple()
    )

    if guild.icon:
      embed.set_author(name=guild.name, icon_url=guild.icon.url)
      embed.set_thumbnail(url=guild.icon.url)
    else:
      embed.set_author(name=guild.name)

    embed.set_footer(text=f'ID: {guild.id} | Created On • {datecreated}')

    embed.add_field(name='Owner', value=interaction.guild.owner, inline=True)
    embed.add_field(name='Members', value=interaction.guild.member_count, inline=True)
    embed.add_field(name='Roles', value=role_count, inline=True)
    embed.add_field(name='Categories', value=len(guild.categories), inline=True)
    embed.add_field(name='Text Channels', value=len(interaction.guild.text_channels), inline=True)
    embed.add_field(name='Voice Channels', value=len(interaction.guild.voice_channels), inline=True)
    if interaction.user.guild_permissions.administrator and role_list:
      embed.add_field(name='Role List', value=roles, inline=False)

    await interaction.followup.send(embed=embed)


async def setup(client):
  await client.add_cog(Settings(client))