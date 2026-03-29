import discord
from discord.ext import commands
import asyncio
import yt_dlp

# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ''

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
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
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

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Karaoke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def karaoke(self, ctx, *, search: str = None):
        """Streams a song perfectly synced into the Voice Channel."""
        if not search:
            return await ctx.send("❌ Usage: `!karaoke <Song Name or URL>`\nExample: `!karaoke Bohemian Rhapsody Lyrics`")

        if not ctx.author.voice:
            return await ctx.send("❌ You are not connected to a voice channel.")

        channel = ctx.author.voice.channel

        # Indicate loading
        msg = await ctx.send(f"🔍 Searching and verifying: `{search}`...")

        try:
            # Connect or move to the author's voice channel
            if ctx.voice_client is None:
                await channel.connect()
            else:
                await ctx.voice_client.move_to(channel)

            # Build the audio source object (streaming to save disk space)
            # We append 'lyrics' if it's a raw search to help them get a lyric video audio
            if not search.startswith("http"):
                search = f"ytsearch1:{search} lyrics"

            player = await YTDLSource.from_url(search, loop=self.bot.loop, stream=True)
            
            # Play it
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
                
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

            embed = discord.Embed(
                title="🎤 Karaoke Started!",
                description=f"Now playing **{player.title}** directly into the voice channel.\n\n*(Since this is direct audio streaming, there are no screen-sync issues or YouTube blocks!)*",
                color=discord.Color.purple()
            )
            await msg.edit(content=None, embed=embed)

        except Exception as e:
            await msg.edit(content=f"❌ An error occurred bridging the audio stream:\n```py\n{str(e)[:150]}\n```")

    @commands.command()
    async def stop(self, ctx):
        """Stops the audio and leaves the voice channel."""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("🛑 Stopped the Karaoke session.")
        else:
            await ctx.send("I am not currently in a voice channel.")

async def setup(bot):
    await bot.add_cog(Karaoke(bot))
