import discord
from discord.ext import commands,tasks
import os
from dotenv import load_dotenv
import yt_dlp as youtube_dl

load_dotenv()

# Get the API token from the .env file.
DISCORD_TOKEN = os.getenv("discord_token")

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!',intents=intents)

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
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

bot.queue = []

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.url = data.get('webpage_url')
        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        print(self.title)

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return data

@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")

@bot.command(name='play', help='To play song')
async def play(ctx,url):
    await ctx.invoke(bot.get_command('join'))
    bot.queue.append(url)
    try :
        server = ctx.message.guild
        voice_channel = server.voice_client

        async with ctx.typing():
            data = await YTDLSource.from_url(url, loop=bot.loop)
            filename = data['title']
            uploader = data['uploader']
            thumb = data['thumbnail']
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg/ffmpeg.exe", source=filename))
        embed=discord.Embed(title="Now Playing", url=url, color=0xff0000)
        embed.set_thumbnail(url=thumb)
        embed.add_field(name=filename, value=uploader, inline=False)
        await ctx.send(embed=embed)
        await ctx.send(bot.queue)
    except:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
        await ctx.send("Paused song")
    else:
        await ctx.send("The bot is not playing anything at the moment.")
    
@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
        await ctx.send("Resumed song")
    else:
        await ctx.send("The bot was not playing anything before this. Use play command")

@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
        await ctx.send("Stopped song")
    else:
        await ctx.send("The bot is not playing anything at the moment.")

bot.run(DISCORD_TOKEN)