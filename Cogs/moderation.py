import discord
import json
from discord.ext import commands
from discord import app_commands
import datetime


class Moderation(commands.Cog):
  def __init__(self, client):
    self.client = client

    
  @app_commands.command(name = 'topic', description = 'Alert a member not to go off-topic in a topic wise channel and mention an off-topic channel.')
  @app_commands.describe(member = 'The member to alert.', channel = 'The channel to avoid off-topic in.')
  @app_commands.checks.cooldown(1, 3.0)
  @app_commands.checks.has_permissions(manage_messages=True)
  async def topic(self, interaction: discord.Interaction, member: discord.Member, channel: discord.TextChannel):
    await channel.send(f'Please, avoid going off-topic in this channel {member.mention}. You can share any day-to-day stuff in {channel}')
    await interaction.response.send_message(f'Alert sent to {member} in {channel.mention}', ephemeral=True)



  @app_commands.command(name = 'lang', description = 'Alert a member to use a certain language in a language channel.')
  @app_commands.describe(member = 'The member to alert.', language = 'The language to use in the channel.')
  @app_commands.checks.cooldown(1, 3.0)
  @app_commands.checks.has_permissions(manage_messages=True)
  async def lang(self, interaction: discord.Interaction, member: discord.Member, language: str):
    await interaction.channel.send(f'Please, refrain from texting any language other than {language} in this channel, {member.mention}.')
    await interaction.response.send_message(f'Alert sent to {member} in {interaction.channel.mention}', ephemeral=True)

  @app_commands.command(name = 'purge', description = 'Clears a certain amount of messages.')
  @app_commands.checks.cooldown(1, 3.0)
  @app_commands.checks.has_permissions(manage_messages=True)
  async def purge(self, interaction: discord.Interaction, amount: int = 0):
    await interaction.response.send_message(f'Purging {amount} messages...', ephemeral=True)
    await interaction.channel.purge(limit = amount)

    with open("log_channels.json", "r") as f:
        logger = json.load(f)
    if str(interaction.guild.id) in logger:
        logcnl = self.client.get_channel(logger[str(interaction.guild.id)])
        log = discord.Embed(
          description = f'Used `purge` in {interaction.channel.mention}\n{interaction.message.content}',
          color = discord.Color.dark_grey(),
          timestamp = datetime.datetime.now()
        )
        log.set_author(name = f'{interaction.user}', icon_url = interaction.user.display_avatar.url)
        await logcnl.send(embed = log)


  @app_commands.command(name = 'notice', description = 'Publish a notice in a specific channel.')
  @app_commands.checks.cooldown(1, 3.0)
  @app_commands.checks.has_permissions(administrator=True)
  async def notice(self, interaction: discord.Interaction, channel: discord.TextChannel, *, message: str):
    await channel.send(message)
    await interaction.response.send_message(f'Notice sent in {channel.mention}', ephemeral=True)

    with open("log_channels.json", "r") as f:
        logger = json.load(f)
    if str(interaction.guild.id) in logger:
        logcnl = self.client.get_channel(logger[str(interaction.guild.id)])
        log = discord.Embed(
          description = f'Used `notice` in {interaction.channel.mention}\n{interaction.message.content}',
          color = discord.Color.dark_grey(),
          timestamp = datetime.datetime.now()
        )
        log.set_author(name = f'{interaction.user}', icon_url = interaction.user.display_avatar.url)
        await logcnl.send(embed = log)


  @app_commands.command(name = 'announce', description = 'Announce an embed message in a specific channel.')
  @app_commands.checks.cooldown(1, 3.0)
  @app_commands.checks.has_permissions(administrator=True)
  async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, *, message: str):
    embed = discord.Embed(
      title = 'Announcement!',
      description = message,
      color = discord.Colour.purple()
    )
    await channel.send(embed=embed)
    await interaction.response.send_message(f'Announcement sent in {channel.mention}', ephemeral=True)

    with open("log_channels.json", "r") as f:
        logger = json.load(f)
    if str(interaction.guild.id) in logger:
        logcnl = self.client.get_channel(logger[str(interaction.guild.id)])
        log = discord.Embed(
          description = f'Used `announce` in {interaction.channel.mention}\n{interaction.message.content}',
          color = discord.Color.dark_grey(),
          timestamp = datetime.datetime.now()
        )
        log.set_author(name = f'{interaction.user}', icon_url = interaction.user.display_avatar.url)
        await logcnl.send(embed = log)



  #Kick-Ban-Unban
  @app_commands.command(name = 'kick', description = 'Kicks a member from server.')
  @app_commands.describe(member = 'The member to kick.', reason = 'The reason for kicking the member.')
  @app_commands.checks.cooldown(1, 3)
  @app_commands.checks.has_permissions(kick_members=True)
  async def kick(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = None):
    server = interaction.guild
    dm = discord.Embed(
        description= f'***You are kicked from {server}*** | {reason}',
        colour=discord.Colour.orange())
    embed = discord.Embed(
      description= f'***:white_check_mark: {member} has been kicked*** | {reason}',
      colour=discord.Colour.gold())
    await interaction.response.send_message(embed=embed)
    await member.send(embed = dm)
    await member.kick(reason=reason)

    # with open("log_channels.json", "r") as f:
    #     logger = json.load(f)
    # if str(interaction.guild.id) in logger:
    #     logcnl = self.client.get_channel(logger[str(interaction.guild.id)])
    #     log = discord.Embed(
    #       color = discord.Color.dark_grey(),
    #       timestamp = datetime.datetime.now()
    #     )
    #     log.set_author(name = f'Kicked | {member}', icon_url = member.display_avatar.url)
    #     log.add_field(name = 'User:', Value = f'{member}', inline = True)
    #     log.add_field(name = 'Moderator:', value = interaction.user, inline = True)
    #     log.add_field(name = 'Reason:', value = reason, inline = True)
    #     await logcnl.send(embed = log)


  @kick.error
  async def kick_error(self, interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
      print('A fool tried to kick someone xD')
    else:
      embed = discord.Embed(
        title= 'Command: /kick',
        description= 'Kicks a member\n\n**Cooldown:** *3 seconds*\n**Usage:** */kick [MEMBER] {reason}(Optional)*\n**Example:** */kick @User for making an example.*',
        colour=discord.Colour.blue())
      await interaction.response.send_message(embed=embed, ephemeral=True)


  @app_commands.command(name = 'ban', description = 'Bans a member from server.')
  @app_commands.describe(member = 'The member to ban.', reason = 'The reason for banning the member.')
  @app_commands.checks.cooldown(1, 3)
  @app_commands.checks.has_permissions(ban_members=True)
  async def ban(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = None):
    server = interaction.guild
    dm = discord.Embed(
      description= f'***You are banned from {server}*** | {reason}',
      colour=discord.Colour.red())
    embed = discord.Embed(
      description= f'***:white_check_mark: {member} has been banned.*** | {reason}',
      colour=discord.Colour.red())
    await interaction.response.send_message(embed=embed)
    await member.send(embed = dm)
    await member.ban(reason=reason)

    # with open("log_channels.json", "r") as f:
    #     logger = json.load(f)
    # if str(interaction.guild.id) in logger:
    #     logcnl = self.client.get_channel(logger[str(interaction.guild.id)])
    #     log = discord.Embed(
    #       color = discord.Color.dark_grey(),
    #       timestamp = datetime.datetime.now()
    #     )
    #     log.set_author(name = f'Banned | {member}', icon_url = member.display_avatar.url)
    #     log.add_field(name = 'User:', value = f'{member}', inline = True)
    #     log.add_field(name = 'Moderator:', value = interaction.user, inline = True)
    #     log.add_field(name = 'Reason:', value = reason, inline = True)
    #     await logcnl.send(embed = log)


  @ban.error
  async def ban_error(self, interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
      print('A dumbass tried to run ban command :kek:')
    else:
      embed = discord.Embed(
        title='Command: /ban',
        description= 'Bans a member\n\n**Cooldown:** *3 seconds*\n**Usage:** */ban [MEMBER] {reason}(Optional)*\n**Example:** */ban @User for making an example.*',
        colour=discord.Colour.blue())
      await interaction.response.send_message(embed=embed, ephemeral=True)


  @app_commands.command(name = 'unban', description = 'Unbans a banned user.')
  @app_commands.checks.cooldown(1, 3.0)
  @app_commands.checks.has_permissions(ban_members=True)
  async def unban(self, interaction: discord.Interaction, member: discord.Member):
    banned_users = await interaction.guild.bans()

    for ban_entry in banned_users:
      user = ban_entry.user

      if (user == member):
        await interaction.guild.unban(user)
        embed = discord.Embed(
          description= f'***:white_check_mark: {member} has been unbanned.***',
          colour=discord.Colour.green())
        await interaction.response.send_message(embed=embed)

    # with open("log_channels.json", "r") as f:
    #     logger = json.load(f)
    # if str(interaction.guild.id) in logger:
    #     logcnl = self.client.get_channel(logger[str(interaction.guild.id)])
    #     log = discord.Embed(
    #       color = discord.Color.dark_grey(),
    #       timestamp = datetime.datetime.now()
    #     )
    #     log.set_author(name = f'Unbanned | {member}', icon_url = member.display_avatar.url)
    #     log.add_field(name = 'User:', value = f'{member}', inline = True)
    #     log.add_field(name = 'Moderator:', value = interaction.user.mention, inline = True)
    #     await logcnl.send(embed = log)


  @unban.error
  async def unban_error(self, interaction: discord.Interaction, error):
      if isinstance(error, app_commands.MissingPermissions):
          print('A dumbass tried again to unban an user :kekw:')
      else:
          embed = discord.Embed(
              title='Command: /unban',
              description=
              'Unbans a banned user\n\n**Cooldown:** *3 seconds*\n**Usage:** */unban [MEMBER]*\n**Example:** */unban @User*',
              colour=discord.Colour.blue())
          await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client):
  await client.add_cog(Moderation(client))