import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp as youtube_dl
import datetime
import sys
import traceback


youtube_dl.utils.bug_reports_message = lambda *args, **kwargs: ''
FFMPEG_OPTIONS = {
   'options': '-vn',
   'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}


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

      ydl_opts = {
          'format': 'bestaudio/best',
          'restrictfilenames': True,
          'noplaylist': True,
          'nocheckcertificate': True,
          'ignoreerrors': False,
          'logtostderr': False,
          'quiet': True,
          'no_warnings': True,
          'default_search': 'scsearch',
          'source_address': '0.0.0.0',
          'extract_flat': False,
          'skip_download': True,
          # 'cookiefile': 'cookies.txt',
          # 'extractor_args': {
          #    'youtube': {
          #       'player_client': ['web_safari,web_embedded,-tv_downgraded']
          #    }
          # }
      }

      def _extract_data(*args, **kwargs):
         with youtube_dl.YoutubeDL(ydl_opts) as ydl:
           return ydl.extract_info(url, download = not stream)

      data = await loop.run_in_executor(None, _extract_data)

      if 'entries' in data:
         data = data['entries'][0] if isinstance(data['entries'], list) else data['entries']

      before_opts = FFMPEG_OPTIONS['before_options']
      user_agent = data.get('http_headers', {}).get('User-Agent')
      if user_agent:
         before_opts += f' -user_agent "{user_agent}"'

      ffmpeg_opts = {
         'before_options': before_opts,
         'options': FFMPEG_OPTIONS['options']
      }
      
      filename = data['url'] if stream else data.get('filename')
      return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_opts), data=data)


class Music(commands.Cog):
  def __init__(self, client):
    self.client = client

  async def play_next(self, interaction: discord.Interaction):
    if len(self.queue) == 0:
       return
    
    voice_client = interaction.guild.voice_client
    if not voice_client or not voice_client.is_connected():
        return

    try:
        query = self.queue.pop(0)
        self.for_queue.pop(0)

        print(f"[MUSIC] Fetching audio for: {query}", flush=True)
        player = await YTDLSource.from_url(query, loop=self.client.loop, stream=True)

        def after_playing(error):
            if error:
               print(f"[MUSIC ERROR] Playback error: {error}", flush=True)
            fut = asyncio.run_coroutine_threadsafe(self.play_next(interaction), self.client.loop)
            try:
               fut.result()
            except Exception as ex:
               print(f"[MUSIC ERROR] Queue transition error: {ex}", flush=True)

        voice_client.play(player, after=after_playing)
        print(f"[MUSIC] Now playing: {player.title}", flush=True)
        
        embed = discord.Embed(
            title='Started Playing:',
            description=f'{player.title}\n\nAll your votes inspire us. [Vote Here](https://top.gg/bot/920757063599132683/vote)',
            color=discord.Colour.greyple()
        )
        if hasattr(player, 'thumbnail') and player.thumbnail:
            embed.set_thumbnail(url=player.thumbnail)
            
        await interaction.channel.send(embed=embed)
    except Exception as e:
        print(f"[MUSIC ERROR] Failed in play_next: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()

  @app_commands.command(name = 'join', description = 'Connects to your voice channel.')
  async def join(self, interaction: discord.Interaction):
      await interaction.response.defer()
      if interaction.user.voice:
          if not interaction.guild.voice_client:
              user_channel = interaction.user.voice.channel
              await user_channel.connect(self_deaf = True)
              await interaction.followup.send('Successfully joined the voice channel.')
          else:
              await interaction.followup.send('I am already in a voice channel.')
      else:
          await interaction.followup.send('You need to join in a voice channel first.')


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

      await interaction.response.defer()

      if not interaction.guild.voice_client:
          channel = interaction.user.voice.channel
          await channel.connect(self_deaf = True)

      self.queue.append(query)
      self.for_queue.append(f'{query} | `Requested by: {interaction.user}`')
      await interaction.followup.send(f'Track added to queue: **{query}**')
          
      if not interaction.guild.voice_client.is_playing() and not interaction.guild.voice_client.is_paused():
        self.play_next(interaction)

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
        queuembed.set_author(name = interaction.guild.name, icon_url = interaction.guild.icon.url)
        queuembed.set_footer(text = f'Requested by {interaction.user}', icon_url = interaction.user.avatar.url)
        await interaction.response.send_message(embed = queuembed)
    else:
      await interaction.response.send_message('You need to join in a voice channel first.')


  @app_commands.command(name = 'skip', description = 'Skips currently playing music and plays the next one.')
  async def skip(self, interaction: discord.Interaction):
    if interaction.user.voice:
      if interaction.guild.voice_client:
        if interaction.guild.voice_client.is_playing():
          interaction.guild.voice_client.stop()
          await interaction.response.send_message('⏭️')
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