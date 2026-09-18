import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
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
    self.webpage_url = data.get('webpage_url')
    self.uploader = data.get('uploader') or data.get('artist') or data.get('creator')
  
  _YDL_OPTS = {
      'format': 'bestaudio/best',
      'restrictfilenames': True,
      'noplaylist': True,
      'nocheckcertificate': True,
      'ignoreerrors': False,
      'logtostderr': False,
      'quiet': True,
      'no_warnings': True,
      'default_search': 'scsearch',
      'extractor_retries': 1,
      'source_address': '0.0.0.0',
      'skip_download': True,
  }

  @classmethod
  async def get_info(cls, query, *, loop=None):
      """Fetch track metadata and raise if the track is DRM-protected or geo-restricted."""
      loop = loop or asyncio.get_event_loop()
      ydl_opts = {**cls._YDL_OPTS, 'extract_flat': False}

      def _extract():
          with youtube_dl.YoutubeDL(ydl_opts) as ydl:
              return ydl.extract_info(query, download=False)

      data = await loop.run_in_executor(None, _extract)

      if 'entries' in data:
          data = data['entries'][0] if isinstance(data['entries'], list) else data['entries']

      # Geo-restricted / premium tracks on SoundCloud are served as 30-second previews
      if data.get('duration') == 30 and data.get('extractor', '').startswith('soundcloud'):
          raise Exception('Track is geo-restricted or premium-only (30-second preview).')

      return {
          'query': query,
          'title': data.get('title', query),
          'webpage_url': data.get('webpage_url') or data.get('url'),
          'uploader': data.get('uploader') or data.get('artist') or data.get('creator'),
          'thumbnail': data.get('thumbnail'),
      }

  @classmethod
  async def search(cls, query, *, loop=None, limit=10):
      """Search SoundCloud and return up to `limit` flat result dicts (fast, no audio stream)."""
      loop = loop or asyncio.get_event_loop()
      ydl_opts = {
          **cls._YDL_OPTS,
          'extract_flat': True,
          'default_search': 'auto',
          'ignoreerrors': True,
      }
      search_url = f'scsearch{limit}:{query}'

      def _extract():
          with youtube_dl.YoutubeDL(ydl_opts) as ydl:
              return ydl.extract_info(search_url, download=False)

      data = await loop.run_in_executor(None, _extract)

      results = []
      if data and 'entries' in data:
          for entry in data['entries']:
              if not entry:
                  continue
              dur = entry.get('duration')
              results.append({
                  'title':       entry.get('title', 'Unknown'),
                  'webpage_url': entry.get('url') or entry.get('webpage_url'),
                  'uploader':    entry.get('uploader') or entry.get('artist'),
                  'duration':    dur,
              })
              if len(results) >= limit:
                  break
      return results

  @classmethod
  async def from_url(cls, url, *, loop = None, stream = False):
      loop = loop or asyncio.get_event_loop()
      ydl_opts = {**cls._YDL_OPTS, 'extract_flat': False}

      def _extract_data(*args, **kwargs):
         with youtube_dl.YoutubeDL(ydl_opts) as ydl:
           return ydl.extract_info(url, download = not stream)

      data = await loop.run_in_executor(None, _extract_data)

      if 'entries' in data:
         data = data['entries'][0] if isinstance(data['entries'], list) else data['entries']

      if data.get('extractor') == 'soundcloud' and data.get('duration') == 30:
          raise Exception('Track is geo-restricted or premium-only (30-second preview).')

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


# ---------------------------------------------------------------------------
# Search results UI
# ---------------------------------------------------------------------------

class SearchResultsView(discord.ui.View):
    """Shows a Select menu so the user can pick one of the search results."""

    def __init__(self, results: list, music_cog, original_interaction: discord.Interaction):
        super().__init__(timeout=60)
        self.results = results
        self.music_cog = music_cog
        self.original_interaction = original_interaction
        self.message: Optional[discord.Message] = None

        options = []
        for i, track in enumerate(results):
            label = track['title'][:100]
            uploader = track.get('uploader') or 'Unknown Artist'
            description = f'by {uploader}'[:100]
            options.append(discord.SelectOption(label=label, description=description, value=str(i)))

        self.select = discord.ui.Select(
            placeholder='Choose a track to add to the queue…',
            options=options,
            min_values=1,
            max_values=1,
        )
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.original_interaction.user.id:
            return await interaction.response.send_message(
                'This search menu belongs to someone else.', ephemeral=True
            )

        idx = int(interaction.data['values'][0])
        chosen = self.results[idx]
        await interaction.response.defer()

        try:
            track = await YTDLSource.get_info(
                chosen['webpage_url'], loop=self.music_cog.client.loop
            )
        except Exception as e:
            print(f'[MUSIC] Search select metadata error: {e}', flush=True)
            track = {**chosen, 'query': chosen['webpage_url']}

        self.music_cog._get_queue(interaction.guild.id).append(track)
        track_url = track.get('webpage_url')
        title_display = (
            f'[{track["title"]}]({track_url})' if track_url else f'**{track["title"]}**'
        )
        self.music_cog._get_for_queue(interaction.guild.id).append(
            f'{title_display} | `Requested by: {interaction.user}`'
        )
        queue_embed = discord.Embed(
            description=f'🎵 Track added to queue: {title_display}',
            color=discord.Color.greyple()
        )
        await interaction.followup.send(embed=queue_embed)

        self.select.disabled = True
        self.stop()
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass
        
        vc = interaction.guild.voice_client
        if vc and not vc.is_playing() and not vc.is_paused():
            asyncio.create_task(
                self.music_cog.play_next(self.original_interaction)
            )

    async def on_timeout(self):
        self.select.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


class Music(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.queue    = {}  # guild_id -> list of track info dicts
    self.for_queue = {}  # guild_id -> list of formatted strings for /queue display

  def _get_queue(self, guild_id: int) -> list:
      """Return this guild's track queue, creating it if needed."""
      return self.queue.setdefault(guild_id, [])

  def _get_for_queue(self, guild_id: int) -> list:
      """Return this guild's display queue, creating it if needed."""
      return self.for_queue.setdefault(guild_id, [])

  async def play_next(self, interaction: discord.Interaction):
    if len(self._get_queue(interaction.guild.id)) == 0:
       return
    
    voice_client = interaction.guild.voice_client
    if not voice_client or not voice_client.is_connected():
        return

    try:
        guild_id = interaction.guild.id
        q = self._get_queue(guild_id)
        fq = self._get_for_queue(guild_id)

        track = q.pop(0)
        fq.pop(0)

        stream_url = track.get('webpage_url') or track.get('query')
        print(f"[MUSIC] Fetching audio for: {track['title']}", flush=True)
        player = await YTDLSource.from_url(stream_url, loop=self.client.loop, stream=True)

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

        track_url = player.webpage_url or track.get('webpage_url')
        title_text = f'[{player.title}]({track_url})' if track_url else player.title
        uploader = player.uploader or track.get('uploader')

        embed = discord.Embed(
            title='Started Playing:',
            description=f'{title_text}\n\nAll your votes inspire us. [Vote Here](https://top.gg/bot/920757063599132683/vote)',
            color=discord.Colour.greyple()
        )
        if uploader:
            embed.add_field(name='Artist', value=uploader, inline=True)
        if hasattr(player, 'thumbnail') and player.thumbnail:
            embed.set_thumbnail(url=player.thumbnail)
            
        await interaction.channel.send(embed=embed)
    except Exception as e:
        error_str = str(e)
        print(f"[MUSIC ERROR] Failed in play_next: {error_str}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        await self.play_next(interaction)

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

      track = None
      
      try:
          track = await YTDLSource.get_info(query, loop=self.client.loop)
      except Exception as e:
          print(f'[MUSIC] Direct query failed ({e}), trying top-5 candidates...', flush=True)
      
      if track is None:
          candidates = await YTDLSource.search(query, loop=self.client.loop, limit=5)
          for candidate in candidates:
              url = candidate.get('webpage_url')
              if not url:
                  continue
              try:
                  track = await YTDLSource.get_info(url, loop=self.client.loop)
                  break
              except Exception as e:
                  print(f'[MUSIC] Candidate "{candidate["title"]}" skipped: {e}', flush=True)

      if track is None:
          return await interaction.followup.send(
              f'❌ Could not find a playable track for **{query}**. '
              'The track may be geo-restricted or DRM-protected on SoundCloud.'
          )

      self._get_queue(interaction.guild.id).append(track)
      track_url = track.get('webpage_url')
      title_display = f'[{track["title"]}]({track_url})' if track_url else f'**{track["title"]}**'
      self._get_for_queue(interaction.guild.id).append(f'{title_display} | `Requested by: {interaction.user}`')
      queue_embed = discord.Embed(
          description=f'🎵 Track added to queue: {title_display}',
          color=discord.Color.greyple()
      )
      await interaction.followup.send(embed=queue_embed)

      if not interaction.guild.voice_client.is_playing() and not interaction.guild.voice_client.is_paused():
        asyncio.create_task(self.play_next(interaction))

  @app_commands.command(name='search', description='Search SoundCloud for a track and pick one to add to the queue.')
  @app_commands.describe(query='What to search for on SoundCloud')
  async def search(self, interaction: discord.Interaction, query: str):
      if not interaction.user.voice:
          return await interaction.response.send_message('You need to join a voice channel first.')

      await interaction.response.defer()

      if not interaction.guild.voice_client:
          channel = interaction.user.voice.channel
          await channel.connect(self_deaf=True)
      
      candidates = await YTDLSource.search(query, loop=self.client.loop, limit=15)
      if not candidates:
          return await interaction.followup.send('No results found for that query.')
    
      async def _validate(candidate):
          url = candidate.get('webpage_url')
          if not url:
              return None
          try:
              return await YTDLSource.get_info(url, loop=self.client.loop)
          except Exception:
              return None

      validated_tasks = await asyncio.gather(*[_validate(c) for c in candidates])
      results = [t for t in validated_tasks if t is not None][:10]

      if not results:
          return await interaction.followup.send(
              '❌ No playable results found. All matched tracks appear to be geo-restricted or DRM-protected.'
          )

      lines = []
      for i, track in enumerate(results, 1):
          title = track['title']
          url   = track.get('webpage_url')
          artist = track.get('uploader') or 'Unknown Artist'
          entry = f'`{i:02}.` [{title}]({url})' if url else f'`{i:02}.` **{title}**'
          entry += f' — {artist}'
          lines.append(entry)

      guild_icon = interaction.guild.icon.url if interaction.guild.icon else None
      user_avatar = interaction.user.display_avatar.url

      embed = discord.Embed(
          title=f'🔍 Search Results: {query}',
          description='\n'.join(lines),
          color=discord.Color.greyple(),
          timestamp=datetime.datetime.utcnow(),
      )
      embed.set_author(name=interaction.guild.name, icon_url=guild_icon)
      embed.set_footer(
          text=f'Searched by {interaction.user} • Select a track below to add it',
          icon_url=user_avatar,
      )

      view = SearchResultsView(results, self, interaction)
      msg = await interaction.followup.send(embed=embed, view=view)
      view.message = msg

  @app_commands.command(name = 'queue', description = 'Shows the music queue.')
  async def queue(self, interaction: discord.Interaction):
    if interaction.user.voice:
      fq = self._get_for_queue(interaction.guild.id)
      if len(fq) == 0:
        await interaction.response.send_message('Empty queue.')
      else:
        guild_icon = interaction.guild.icon.url if interaction.guild.icon else None
        user_avatar = interaction.user.display_avatar.url
        queuembed = discord.Embed(
          title = 'Queue',
          description = '\n'.join(fq),
          color = discord.Color.greyple(),
          timestamp = datetime.datetime.utcnow()
        )
        queuembed.set_author(name = interaction.guild.name, icon_url = guild_icon)
        queuembed.set_footer(text = f'Requested by {interaction.user}', icon_url = user_avatar)
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
          self._get_queue(interaction.guild.id).clear()
          self._get_for_queue(interaction.guild.id).clear()
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