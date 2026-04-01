import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
import re
import urllib.request
import urllib.parse
from collections import deque

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,  # Default to single tracks to prevent massive lockups
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.is_live = data.get('is_live')

    @classmethod
    async def create_source(cls, query, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()

        # Handle Apple Music / Spotify links by converting to ytsearch
        # (This avoids DRM locking the stream by grabbing the highest quality YT equivalent)
        if "spotify.com" in query or "apple.com" in query:
            # We enforce ytsearch if it's a known premium music link so yt-dlp 
            # uses its metadata scraper to search youtube instead of hitting DRM errors.
            query = f"ytsearch:{query}"

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=not stream))

        if 'entries' in data:
            # Take first item from a playlist / search result
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class PlayModal(discord.ui.Modal, title='Add to Queue'):
    query = discord.ui.TextInput(
        label='Song Name or URL',
        placeholder='e.g. https://youtube.com/watch... or "LoFi Radio"',
        required=True,
        max_length=500
    )

    def __init__(self, cog, guild): # Pass the cog and guild to the modal so it can interface with the music system
        super().__init__()
        self.cog = cog
        self.guild = guild

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        query = self.query.value
        
        # Enforce Smart Admin Queue Limits
        is_admin = interaction.user.guild_permissions.administrator
        queue = self.cog.queues.get(self.guild.id, deque())
        
        if not is_admin and len(queue) >= 100:
            return await interaction.followup.send("❌ Note: Standard users cannot queue more than 100 songs to prevent server bloat. Please wait for the queue to clear or ask an Administrator.", ephemeral=True)

        try:
            # Pre-flight check for duration without downloading everything
            await interaction.followup.send(f"🔍 Searching and loading: `{query}`...", ephemeral=True)
            
            loop = self.cog.bot.loop or asyncio.get_event_loop()
            
            def extract():
                search_query = query
                if "spotify.com" in query or "apple.com" in query:
                    search_query = f"ytsearch:{query}"
                return ytdl.extract_info(search_query, download=False)
                
            data = await loop.run_in_executor(None, extract)
            
            if 'entries' in data:
                data = data['entries'][0]

            duration = data.get('duration')
            is_live = data.get('is_live', False)
            title = data.get('title', 'Unknown Title')

            # Smart Admin Duration Limit (3 hours = 10800 seconds)
            if not is_admin and not is_live and duration and duration > 10800:
                return await interaction.followup.send(f"❌ **{title}** is {duration/3600:.1f} hours long. Standard users are restricted to videos under 3 hours to prevent resource lockups.\n*Note: 24/7 Live Radio streams are exempt from this limit!*")

            # All checks passed, add to queue!
            if self.guild.id not in self.cog.queues:
                self.cog.queues[self.guild.id] = deque()
            
            self.cog.queues[self.guild.id].append(query)
            await interaction.followup.send(f"✅ Picked up **{title}** and added it to the queue!")

            # If nothing is playing, start the player!
            voice_client = self.guild.voice_client
            if voice_client and not voice_client.is_playing() and not voice_client.is_paused():
                await self.cog.play_next(interaction)
                
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred while fetching that song: `{e}`")

class MusicControlView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None) # Persistent view
        self.cog = cog

    @discord.ui.button(label="Play / Add", style=discord.ButtonStyle.green, emoji="🎵", custom_id="music_cmd_play")
    async def play_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ You must be in a Voice Channel to play music!", ephemeral=True)
            
        # Ensure bot is in the same channel or joins it
        voice_client = interaction.guild.voice_client
        if not voice_client:
            try:
                await interaction.user.voice.channel.connect()
            except discord.ClientException:
                pass
        
        await interaction.response.send_modal(PlayModal(self.cog, interaction.guild))

    @discord.ui.button(label="Pause/Resume", style=discord.ButtonStyle.blurple, emoji="⏯️", custom_id="music_cmd_pause")
    async def pause_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if not voice_client:
            return await interaction.response.send_message("❌ The bot is not connected to a voice channel.", ephemeral=True)

        if voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("▶️ Resumed the music.", ephemeral=False)
        elif voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("⏸️ Paused the music.", ephemeral=False)
        else:
            await interaction.response.send_message("❌ No music is currently playing.", ephemeral=True)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.gray, emoji="⏭️", custom_id="music_cmd_skip")
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_playing():
            return await interaction.response.send_message("❌ Nothing is playing to skip.", ephemeral=True)
            
        voice_client.stop() # Stopping triggers the 'after' callback, which plays the next song automatically
        await interaction.response.send_message("⏭️ Skipped the current track.")

    @discord.ui.button(label="Queue", style=discord.ButtonStyle.secondary, emoji="📜", custom_id="music_cmd_queue")
    async def queue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        queue = self.cog.queues.get(interaction.guild.id)
        if not queue:
            return await interaction.response.send_message("📭 The queue is currently empty.", ephemeral=True)
            
        q_list = list(queue)
        # Prevent massive queue from breaking discord embed limits
        display_list = q_list[:15] 
        msg = "**Current Queue:**\n"
        for i, q in enumerate(display_list):
            msg += f"`{i+1}.` {q}\n"
            
        if len(q_list) > 15:
            msg += f"\n*...and {len(q_list) - 15} more tracks.*"
            
        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="Disconnect", style=discord.ButtonStyle.red, emoji="🛑", custom_id="music_cmd_stop")
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client:
            # Clear the queue
            if interaction.guild.id in self.cog.queues:
                self.cog.queues[interaction.guild.id].clear()
            await voice_client.disconnect()
            await interaction.response.send_message("🛑 Disconnected from the voice channel and cleared the queue.")
        else:
            await interaction.response.send_message("❌ I am not in a voice channel.", ephemeral=True)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {} # Maps guild.id -> collections.deque

    async def play_next(self, interaction_or_ctx):
        guild = interaction_or_ctx.guild
        voice_client = guild.voice_client
        
        if not voice_client:
            return
            
        queue = self.queues.get(guild.id)
        if not queue:
            # Disconnect if nothing is left? Or just idle. We'll idle for now.
            return
            
        # Pop the next query
        query = queue.popleft()
        
        try:
            player = await YTDLSource.create_source(query, loop=self.bot.loop, stream=True)
            # The 'after' callback must be a normal function, not async.
            # We use a lambda to properly dispatch a new async task for the next song.
            def after_call(error):
                if error:
                    print(f"Music Player Error: {error}")
                # Dispatch the play_next function safely to the event loop without blocking the FFmpeg thread
                self.bot.loop.call_soon_threadsafe(lambda: self.bot.loop.create_task(self.play_next(interaction_or_ctx)))
            
            voice_client.play(player, after=after_call)
            
            # Optionally send a message to the channel declaring what is currently playing
            channel = getattr(interaction_or_ctx, 'channel', None)
            if channel:
                # Need to use an async dispatch to send the message since we might be inside a synchronous callback sometimes
                asyncio.run_coroutine_threadsafe(
                    channel.send(f"🎶 Now Playing: **{player.title}**"),
                    self.bot.loop
                )
                
        except Exception as e:
            channel = getattr(interaction_or_ctx, 'channel', None)
            if channel:
                asyncio.run_coroutine_threadsafe(
                    channel.send(f"❌ Failed to play next track: `{e}`"),
                    self.bot.loop
                )
            # Skip to the next instead of dying entirely
            asyncio.run_coroutine_threadsafe(
                self.play_next(interaction_or_ctx),
                self.bot.loop
            )

    @commands.command(name="music", aliases=["m", "play"])
    async def music_dashboard(self, ctx):
        """Summons the Music Dashboard. Allows playing and streaming audio with interactive buttons."""
        embed = discord.Embed(
            title="🎵 KingBot Audio Hub",
            description="Welcome to the high-performance Music Dashboard.\n\n"
                        "• **Multi-Source Support:** Works with YouTube, Apple Music, Spotify, Deezer, and Direct Links.\n"
                        "• **24/7 Radio:** Paste an `.m3u` or `.pls` internet radio link for infinite ambience.\n\n"
                        "Click **Play / Add** to open the Search Modal and start queueing songs!",
            color=discord.Color.brand_green()
        )
        embed.set_footer(text="Smart Admin Mode Enabled - Standard users limited to 3hr videos and 100 items.")
        
        # We spawn the persistent view that handles buttons and modals
        await ctx.send(embed=embed, view=MusicControlView(self))

async def setup(bot):
    await bot.add_cog(Music(bot))
