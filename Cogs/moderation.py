import discord
from discord.ext import commands
from discord import app_commands
import datetime
from db import get_log_channel


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

    channel_id = await get_log_channel(interaction.guild.id)
    if channel_id:
        logcnl = self.client.get_channel(channel_id)
        if logcnl:
            log = discord.Embed(
              description = f'🧹 {interaction.user.mention} purged **{amount}** messages in {interaction.channel.mention}',
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

    channel_id = await get_log_channel(interaction.guild.id)
    if channel_id:
        logcnl = self.client.get_channel(channel_id)
        if logcnl:
            log = discord.Embed(
              description = f'📢 {interaction.user.mention} sent a **notice** in {channel.mention}\n\n{message}',
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

    channel_id = await get_log_channel(interaction.guild.id)
    if channel_id:
        logcnl = self.client.get_channel(channel_id)
        if logcnl:
            log = discord.Embed(
              description = f'📣 {interaction.user.mention} sent an **announcement** in {channel.mention}\n\n{message}',
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
    try:
        await member.send(embed=dm)
    except discord.Forbidden:
        pass
    await member.kick(reason=reason)

    channel_id = await get_log_channel(interaction.guild.id)
    if channel_id:
        logcnl = self.client.get_channel(channel_id)
        if logcnl:
            log = discord.Embed(
              color = discord.Color.dark_orange(),
              timestamp = datetime.datetime.now()
            )
            log.set_author(name = f'👢 Kicked | {member}', icon_url = member.display_avatar.url)
            log.add_field(name = 'User', value = f'{member.mention} ({member.id})', inline = True)
            log.add_field(name = 'Moderator', value = interaction.user.mention, inline = True)
            log.add_field(name = 'Reason', value = reason or 'No reason provided', inline = False)
            await logcnl.send(embed = log)


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
    try:
        await member.send(embed=dm)
    except discord.Forbidden:
        pass
    await member.ban(reason=reason)

    channel_id = await get_log_channel(interaction.guild.id)
    if channel_id:
        logcnl = self.client.get_channel(channel_id)
        if logcnl:
            log = discord.Embed(
              color = discord.Color.red(),
              timestamp = datetime.datetime.now()
            )
            log.set_author(name = f'🔨 Banned | {member}', icon_url = member.display_avatar.url)
            log.add_field(name = 'User', value = f'{member.mention} ({member.id})', inline = True)
            log.add_field(name = 'Moderator', value = interaction.user.mention, inline = True)
            log.add_field(name = 'Reason', value = reason or 'No reason provided', inline = False)
            await logcnl.send(embed = log)


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
  @app_commands.describe(user_id = 'The ID of the user to unban.')
  @app_commands.checks.cooldown(1, 3.0)
  @app_commands.checks.has_permissions(ban_members=True)
  async def unban(self, interaction: discord.Interaction, user_id: str):
    await interaction.response.defer()

    try:
       target_id = int(user_id)
    except ValueError:
       embed = discord.Embed(
          description = "❌ Enter a valid user ID."
       )
       await interaction.followup.send(embed=embed)
       return
    
    banned_users = [ban_entry async for ban_entry in interaction.guild.bans()]

    for ban_entry in banned_users:
      user = ban_entry.user

      if user.id == target_id:
        await interaction.guild.unban(user)

        embed = discord.Embed(
          description= f'***:white_check_mark: {user} has been unbanned.***',
          colour=discord.Colour.green())
        await interaction.followup.send(embed=embed)

        channel_id = await get_log_channel(interaction.guild.id)
        if channel_id:
            logcnl = self.client.get_channel(channel_id)
            if logcnl:
                log = discord.Embed(
                  color = discord.Color.green(),
                  timestamp = datetime.datetime.now()
                )
                log.set_author(name = f'✅ Unbanned | {user}', icon_url = user.display_avatar.url)
                log.add_field(name = 'User', value = f'{user.mention} ({user.id})', inline = True)
                log.add_field(name = 'Moderator', value = interaction.user.mention, inline = True)
                await logcnl.send(embed = log)
        return


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


  @app_commands.command(name='timeout', description='Times out a member for a specified duration.')
  @app_commands.describe(member='The member to timeout.', minutes='Duration in minutes.', reason='Reason for the timeout.')
  @app_commands.checks.cooldown(1, 3.0)
  @app_commands.checks.has_permissions(moderate_members=True)
  async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, *, reason: str = None):
    duration = datetime.timedelta(minutes=minutes)
    try:
        await member.timeout(duration, reason=reason)
        dm = discord.Embed(
          description= f'***You are timed out from {interaction.guild} for {minutes} minutes*** | {reason}',
          colour=discord.Colour.orange())
        embed = discord.Embed(
            description=f'***:white_check_mark: {member} has been timed out for {minutes} minutes.*** | {reason}',
            colour=discord.Colour.orange()
        )
        await interaction.response.send_message(embed=embed)
        
        try:
            await member.send(embed=dm)
        except discord.Forbidden:
            pass

        channel_id = await get_log_channel(interaction.guild.id)
        if channel_id:
            logcnl = self.client.get_channel(channel_id)
            if logcnl:
                log = discord.Embed(
                  color = discord.Color.orange(),
                  timestamp = datetime.datetime.now()
                )
                log.set_author(name = f'⏱️ Timed Out | {member}', icon_url = member.display_avatar.url)
                log.add_field(name = 'User', value = f'{member.mention} ({member.id})', inline = True)
                log.add_field(name = 'Moderator', value = interaction.user.mention, inline = True)
                log.add_field(name = 'Duration', value = f'{minutes} minutes', inline = True)
                log.add_field(name = 'Reason', value = reason or 'No reason provided', inline = False)
                await logcnl.send(embed = log)
            
    except discord.Forbidden:
        await interaction.response.send_message(f'I lack permissions to time out {member.mention}. Are they higher in the role hierarchy?', ephemeral=True)


  @timeout.error
  async def timeout_error(self, interaction: discord.Interaction, error):
      if isinstance(error, app_commands.MissingPermissions):
          print('Someone tried to timeout without permissions.')
      else:
          embed = discord.Embed(
              title='Command: /timeout',
              description='Times out a member\n\n**Cooldown:** *3 seconds*\n**Usage:** */timeout [MEMBER] [MINUTES] {reason}*\n**Example:** */timeout @User 10 for spamming.*',
              colour=discord.Colour.blue()
          )
          if not interaction.response.is_done():
              await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client):
  await client.add_cog(Moderation(client))