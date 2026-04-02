import discord
from discord.ext import commands
import asyncio
import yt_dlp
import re
from collections import deque

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
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
        if "spotify.com" in query or "apple.com" in query:
            query = f"ytsearch:{query}"
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class MusicConfigModal(discord.ui.Modal, title='Music Configuration'):
    authorized_text = discord.ui.TextInput(label='Restricted Text Channel ID (Blank = Any)', placeholder='e.g. 123456789', required=False)
    authorized_voice = discord.ui.TextInput(label='Restricted Voice Channel ID (Blank = Any)', placeholder='e.g. 987654321', required=False)
    max_queue = discord.ui.TextInput(label='Queue Cap (Max Songs for Standard Users)', placeholder='e.g. 20', default="20", required=True)
    max_duration = discord.ui.TextInput(label='Max Duration in Minutes (Standard Users)', placeholder='e.g. 180', default="180", required=True)

    def __init__(self, cog, guild_id, defaults):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id
        
        if defaults:
            self.authorized_text.default = defaults.get("auth_text", "")
            self.authorized_voice.default = defaults.get("auth_voice", "")
            self.max_queue.default = defaults.get("max_queue", "20")
            self.max_duration.default = defaults.get("max_duration", "180")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Validate numeric inputs if provided
            if self.authorized_text.value.strip(): int(self.authorized_text.value.strip())
            if self.authorized_voice.value.strip(): int(self.authorized_voice.value.strip())
            int(self.max_queue.value.strip())
            int(self.max_duration.value.strip())
            
        except ValueError:
            return await interaction.response.send_message("❌ Configuration Error: All fields must be raw numerical IDs or values.", ephemeral=True)
            
        await self.cog.bot.db.hset(f"music_cfg:{self.guild_id}", "auth_text", self.authorized_text.value.strip())
        await self.cog.bot.db.hset(f"music_cfg:{self.guild_id}", "auth_voice", self.authorized_voice.value.strip())
        await self.cog.bot.db.hset(f"music_cfg:{self.guild_id}", "max_queue", self.max_queue.value.strip())
        await self.cog.bot.db.hset(f"music_cfg:{self.guild_id}", "max_duration", self.max_duration.value.strip())
        
        await interaction.response.send_message("✅ Music Administration settings successfully updated and saved synchronously across the cluster!", ephemeral=True)


class PlayModal(discord.ui.Modal, title='Add to Queue'):
    query = discord.ui.TextInput(
        label='Song Name or URL',
        placeholder='e.g. https://youtube.com/watch... or "LoFi Radio"',
        required=True,
        max_length=500
    )

    def __init__(self, cog, guild): 
        super().__init__()
        self.cog = cog
        self.guild = guild

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        query = self.query.value
        is_admin = interaction.user.guild_permissions.administrator
        
        # Load constraints
        cfg = await self.cog.bot.db.hgetall(f"music_cfg:{self.guild.id}") or {}
        max_q = int(cfg.get("max_queue", 100))
        max_mins = int(cfg.get("max_duration", 180))
        
        queue = self.cog.queues.get(self.guild.id, deque())
        if not is_admin and len(queue) >= max_q:
            return await interaction.followup.send(f"❌ Queue Cap Reached: Standard users are restricted to **{max_q}** items at a time.", ephemeral=True)

        try:
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

            max_secs = max_mins * 60
            if not is_admin and not is_live and duration and duration > max_secs:
                return await interaction.followup.send(f"❌ **{title}** is {duration/60:.1f} minutes long. The admin restrict limit is currently set to **{max_mins} minutes**.")

            if self.guild.id not in self.cog.queues:
                self.cog.queues[self.guild.id] = deque()
            
            self.cog.queues[self.guild.id].append(query)
            await interaction.followup.send(f"✅ Picked up **{title}** and added it to the queue!")

            voice_client = self.guild.voice_client
            if not voice_client:
                try:
                    voice_client = await interaction.user.voice.channel.connect()
                except discord.ClientException:
                    voice_client = self.guild.voice_client
                    
            if voice_client and not voice_client.is_playing() and not voice_client.is_paused():
                await self.cog.play_next(interaction)
                
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred while fetching that song: `{e}`")

class MusicControlView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None) 
        self.cog = cog

    @discord.ui.button(label="Play / Add", style=discord.ButtonStyle.green, emoji="🎵", custom_id="music_cmd_play")
    async def play_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = await self.cog.bot.db.hgetall(f"music_cfg:{interaction.guild.id}") or {}
        auth_text = cfg.get("auth_text", "")
        auth_voice = cfg.get("auth_voice", "")
        is_admin = interaction.user.guild_permissions.administrator
        
        # Check text channel lockdown
        if not is_admin and auth_text and str(interaction.channel_id) != auth_text:
            return await interaction.response.send_message(f"❌ You may only queue music in <#{auth_text}>.", ephemeral=True)
            
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ You must be in a Voice Channel to play music!", ephemeral=True)
            
        # Check voice channel lockdown
        if not is_admin and auth_voice and str(interaction.user.voice.channel.id) != auth_voice:
            return await interaction.response.send_message(f"❌ Standard users can only queue music from <#{auth_voice}>.", ephemeral=True)
            
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
            
        voice_client.stop()
        await interaction.response.send_message("⏭️ Skipped the current track.")

    @discord.ui.button(label="Queue", style=discord.ButtonStyle.secondary, emoji="📜", custom_id="music_cmd_queue")
    async def queue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        queue = self.cog.queues.get(interaction.guild.id)
        if not queue:
            return await interaction.response.send_message("📭 The queue is currently empty.", ephemeral=True)
            
        q_list = list(queue)
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
            if interaction.guild.id in self.cog.queues:
                self.cog.queues[interaction.guild.id].clear()
            await voice_client.disconnect()
            await interaction.response.send_message("🛑 Disconnected from the voice channel and cleared the queue.")
        else:
            await interaction.response.send_message("❌ I am not in a voice channel.", ephemeral=True)

class MusicAdminView(discord.ui.View):
    def __init__(self, cog, guild_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.button(label="Settings", style=discord.ButtonStyle.primary, emoji="⚙️")
    async def config_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        defaults = await self.cog.bot.db.hgetall(f"music_cfg:{self.guild_id}") or {}
        await interaction.response.send_modal(MusicConfigModal(self.cog, self.guild_id, defaults))

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {} 

    async def play_next(self, interaction_or_ctx):
        guild = interaction_or_ctx.guild
        voice_client = guild.voice_client
        
        if not voice_client: return
            
        queue = self.queues.get(guild.id)
        if not queue: return
            
        query = queue.popleft()
        try:
            player = await YTDLSource.create_source(query, loop=self.bot.loop, stream=True)
            def after_call(error):
                if error: print(f"Music Player Error: {error}")
                self.bot.loop.call_soon_threadsafe(lambda: self.bot.loop.create_task(self.play_next(interaction_or_ctx)))
            
            voice_client.play(player, after=after_call)
            channel = getattr(interaction_or_ctx, 'channel', None)
            if channel:
                asyncio.run_coroutine_threadsafe(channel.send(f"🎶 Now Playing: **{player.title}**"), self.bot.loop)
        except Exception as e:
            channel = getattr(interaction_or_ctx, 'channel', None)
            if channel:
                asyncio.run_coroutine_threadsafe(channel.send(f"❌ Failed to play next track: `{e}`"), self.bot.loop)
            asyncio.run_coroutine_threadsafe(self.play_next(interaction_or_ctx), self.bot.loop)

    @commands.command(name="music", aliases=["play"])
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
        embed.set_footer(text="Settings controlled strictly by Server Administrators")
        await ctx.send(embed=embed, view=MusicControlView(self))

    @commands.command(name="music_admin")
    @commands.has_permissions(administrator=True)
    async def music_admin(self, ctx):
        """[Admin Only] Central Music Configuration Dashboard."""
        embed = discord.Embed(
            title="⚙️ Music Administration",
            description="Use the button below to restrict bot usage to certain text/voice channels, or modify the bounds for queue lengths and duration blocks.",
            color=discord.Color.dark_magenta()
        )
        await ctx.send(embed=embed, view=MusicAdminView(self, ctx.guild.id))

async def setup(bot):
    await bot.add_cog(Music(bot))
