import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp as youtube_dl
import datetime


youtube_dl.utils.bug_reports_message = lambda: ''
FFMPEG_OPTIONS = {
   'options': '-vn',
   'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ydl_opts = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ytdl = youtube_dl.YoutubeDL(ydl_opts)

queue = []
for_queue = []


class  YTDLSource(discord.PCMVolumeTransformer):
  def __init__(self, source, *, data, volume = 1.0):
    super().__init__(source, volume)

    self.data = data
    self.url = data.get('url')
    self.title = data.get('title')
    self.thumbnail = data.get('thumbnail')

  @classmethod
  async def from_url(cls, url, *, loop = None, stream = False):
      loop = loop or asyncio.get_event_loop()
      data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download = not stream))

      if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

      filename = data['url'] if stream else ytdl.prepare_filename(data)
      return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)


class Music(commands.Cog):
  def __init__(self, client):
    self.client = client


  @app_commands.command(name = 'join', description = 'Connects to your voice channel.')
  async def join(self, interaction: discord.Interaction):
      await interaction.response.defer()
      if interaction.user.voice:
          if not interaction.guild.voice_client:
              user_channel = interaction.user.voice.channel
              await user_channel.connect()
              await interaction.response.send_message('Successfully joined the voice channel.')
          else:
              await interaction.response.send_message('I am already in a voice channel.')
      else:
          await interaction.response.send_message('You need to join in a voice channel first.')


  @app_commands.command(name = 'leave', description = 'Disconnects from your voice channel.')
  async def leave(self, interaction: discord.Interaction):
      if interaction.user.voice:
          if interaction.guild.voice_client:
              await interaction.guild.voice_client.disconnect()
              await interaction.response.send_message('Successfully left the voice channel.')
          else:
              await interaction.response.send_message('I am not in a voice channel.')
      else:
          await interaction.response.send_message('You need to join in a voice channel first.')


  @app_commands.command(name = 'play', description = 'Starts playing your requested music.')
  @app_commands.describe(query = 'Enter the name or URL of the song you want to play.')
  async def play(self, interaction: discord.Interaction, query: str):
      if not interaction.user.voice:
          return await interaction.response.send_message('You need to join in a voice channel first.')
      
      global queue
      global for_queue

      await interaction.response.defer()
      if not interaction.guild.voice_client:
          channel = interaction.user.voice.channel
          await channel.connect()
      try:
        last = await YTDLSource.from_url(queue, loop = self.client.loop, stream = True)
        queue.append(query)
        for_queue.append(f'{last.title} | `Requested by: {interaction.user}`')
        await interaction.channel.send(f'Track added to queue: **{last.title}**')
      except Exception as e:
        return await interaction.channel.send(f'Error loading track: {str(e)}')
          
      while queue:
        voice_client = interaction.guild.voice_client
        if not voice_client:
            break
        if voice_client.is_playing() or voice_client.is_paused():
            await asyncio.sleep(2)
            continue

        try:
            current_queue = queue.pop(0)
            for_queue.pop(0)
            player = await YTDLSource.from_url(current_queue, loop=self.client.loop, stream=True)
            voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            
            embed = discord.Embed(
              title = 'Started Playing:',
              description = f'{player.title}\n\nAll your votes inspire us. [Vote Here](https://top.gg/bot/920757063599132683/vote)',
              color = discord.Colour.greyple()
            )
            if player.thumbnail:
               embed.set_thumbnail(url = player.thumbnail)
            await interaction.channel.send(embed = embed)
        except Exception as e:
            print(f'Queue error: {e}')
            break


  @app_commands.command(name = 'queue', description = 'Shows the music queue.')
  async def queue(self, interaction: discord.Interaction):
    global for_queue
    if interaction.user.voice:
      if len(for_queue) == 0:
        await interaction.response.send_message('Empty queue.')
      else:
        queuembed = discord.Embed(
          title = 'Queue',
          description = '\n'.join(for_queue),
          color = discord.Color.greyple(),
          timestamp = datetime.datetime.utcnow()
        )
        queuembed.set_author(name = interaction.guild, icon_url = interaction.guild.icon_url)
        queuembed.set_footer(text = f'Requested by {interaction.user}', icon_url = interaction.user.avatar_url)
        await interaction.response.send_message(embed = queuembed)
    else:
      await interaction.response.send_message('You need to join in a voice channel first.')


  @app_commands.command(name = 'skip', description = 'Skips currently playing music and plays the next one.')
  async def skip(self, interaction: discord.Interaction):
    if interaction.user.voice:
      if interaction.guild.voice_client:
        if interaction.guild.voice_client.is_playing():
          global queue
          global for_queue
          interaction.guild.voice_client.stop()
          await interaction.response.send_message('⏭️')
          while len(queue) > 0:
            try:
              await asyncio.sleep(2)
              pass
            except AttributeError:
              pass
            try:
              player = await YTDLSource.from_url(queue[0], loop = self.client.loop, stream=True)
              interaction.guild.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
              queue.pop(0)
              tit, req = for_queue[0].split('|')
              for_queue.pop(0)
              embed = discord.Embed(
                title = 'Started Playing:',
                description = f'{player.title}\n\nAll your votes inspire us. [Vote Here](https://top.gg/bot/920757063599132683/vote)',
                color = discord.Colour.greyple()
                )
              embed.set_image(url = player.thumbnail)
              await interaction.channel.send(embed = embed)
            except:
              break
        else:
          await interaction.response.send_message('Nothing is being played right now.')
      else:
        await interaction.response.send_message('I am not even in a voice channel :woozy_face:')
    else:
      await interaction.response.send_message('Join in a voice channel to run this command.')
  

  @app_commands.command(name = 'stop', description = 'Stops playing music.')
  async def stop(self, interaction: discord.Interaction):
    if interaction.user.voice:
      if interaction.guild.voice_client:
        if interaction.guild.voice_client.is_playing():
          interaction.guild.voice_client.stop()
          await interaction.response.send_message('🛑')
        else:
          await interaction.response.send_message('There is nothing to stop.')
      else:
        await interaction.response.send_message('I am not even in a voice channel :woozy_face:')
    else:
      await interaction.response.send_message('Join in a voice channel to run this command.')

  @app_commands.command(name = 'pause', description = 'Pauses currently playing music.')
  async def pause(self, interaction: discord.Interaction):
    if interaction.user.voice:
      if interaction.guild.voice_client:
        if interaction.guild.voice_client.is_playing():
          interaction.guild.voice_client.pause()
          await interaction.response.send_message('⏸')
        else:
          await interaction.response.send_message('There is nothing to pause.')
      else:
        await interaction.response.send_message('I am not even in a voice channel :woozy_face:')
    else:
      await interaction.response.send_message('Join in a voice channel to run this command.')

  @app_commands.command(name = 'resume', description = 'Resumes recently paused music.')
  async def resume(self, interaction: discord.Interaction):
    if interaction.user.voice:
      if interaction.guild.voice_client:
        if interaction.guild.voice_client.is_paused():
          interaction.guild.voice_client.resume()
          await interaction.response.send_message('▶')
        else:
          await interaction.response.send_message('There is nothing to resume.')
      else:
        await interaction.response.send_message('I am not even in a voice channel :woozy_face:')
    else:
      await interaction.response.send_message('Join in a voice channel to run this command.')


async def setup(client):
  await client.add_cog(Music(client))