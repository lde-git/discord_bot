import discord
from discord.ext import commands
import os
import random
import asyncio
from dotenv import load_dotenv
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re

# --- Initial Setup ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# Define bot intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True

# Create a bot instance and remove the default help command
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Initialize Spotify client
try:
    spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                                                   client_secret=SPOTIPY_CLIENT_SECRET))
except Exception as e:
    spotify = None
    print(f"Could not initialize Spotify client. Check credentials. Error: {e}")


# Global dictionary to store song queues for each server
song_queues = {}
names_to_pity = ['Lukas', 'Alex', 'Kally']

# --- YouTube & FFmpeg Configuration ---
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

# --- Helper Functions ---
def play_next_song(ctx):
    guild_id = ctx.guild.id
    if guild_id in song_queues and song_queues[guild_id]:
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_connected():
            song = song_queues[guild_id].pop(0)
            source = discord.FFmpegPCMAudio(song['url'], **FFMPEG_OPTIONS)
            voice_client.play(source, after=lambda e: play_next_song(ctx))
    else:
        asyncio.run_coroutine_threadsafe(disconnect_after_delay(ctx), bot.loop)

async def disconnect_after_delay(ctx):
    await asyncio.sleep(120)
    voice_client = ctx.voice_client
    if voice_client and not voice_client.is_playing() and not voice_client.is_paused():
        await voice_client.disconnect()

# --- Bot Events ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    if spotify is None:
        print("Warning: Spotify client failed to initialize. Spotify links will not work.")
    else:
        print("Spotify client initialized successfully.")
    print('Bot is ready to be used!')
    print('-------------------------')

# --- Music Commands ---
@bot.command(name='play', aliases=['p'], help="Plays a song from YouTube or Spotify.")
async def play(ctx, *, query: str):
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to use this command!")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    if voice_client is None:
        voice_client = await channel.connect()
    elif voice_client.channel != channel:
        await voice_client.move_to(channel)

    guild_id = ctx.guild.id
    if guild_id not in song_queues:
        song_queues[guild_id] = []

    songs_to_add = []
    
    async with ctx.typing():
        # Check for Spotify URL
        if "spotify.com" in query and spotify:
            if "track" in query:
                try:
                    track = spotify.track(query)
                    search_query = f"{track['name']} {track['artists'][0]['name']} audio"
                    songs_to_add.append({'query': search_query, 'source': 'spotify'})
                except Exception as e:
                    await ctx.send(f"Couldn't process the Spotify song link. Error: {e}")
                    return
            elif "playlist" in query:
                try:
                    results = spotify.playlist_tracks(query)
                    for item in results['items']:
                        track = item['track']
                        search_query = f"{track['name']} {track['artists'][0]['name']} audio"
                        songs_to_add.append({'query': search_query, 'source': 'spotify'})
                    await ctx.send(f"Adding {len(songs_to_add)} songs from the playlist to the queue...")
                except Exception as e:
                    await ctx.send(f"Couldn't process the Spotify playlist link. Error: {e}")
                    return
            else:
                 await ctx.send("That Spotify link type is not supported.")
                 return

        # Check for YouTube URL or plain search
        else:
            search_query = query if "youtube.com" in query or "youtu.be" in query else f"ytsearch:{query}"
            songs_to_add.append({'query': search_query, 'source': 'youtube'})

        # Process all songs found
        for song_info in songs_to_add:
            try:
                with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                    info = ydl.extract_info(song_info['query'], download=False)
                    if 'entries' in info:
                        info = info['entries'][0]
                    
                    song = {'url': info['url'], 'title': info['title']}
                    song_queues[guild_id].append(song)
                    
                    if len(songs_to_add) == 1:
                        await ctx.send(f"✅ Added to queue: **{song['title']}**")

            except Exception as e:
                print(f"Error processing {song_info['query']}: {e}")
                if len(songs_to_add) == 1:
                    await ctx.send("Sorry, I couldn't process that request.")

    if not voice_client.is_playing() and not voice_client.is_paused():
        play_next_song(ctx)


@bot.command(name='queue', aliases=['q'], help="Shows the current song queue.")
async def queue(ctx):
    guild_id = ctx.guild.id
    if guild_id not in song_queues or not song_queues[guild_id]:
        await ctx.send("The queue is currently empty.")
        return

    embed = discord.Embed(title="🎵 Song Queue 🎵", color=discord.Color.blue())
    queue_list = ""
    for i, song in enumerate(song_queues[guild_id]):
        queue_list += f"`{i+1}.` {song['title']}\n"
    
    embed.description = queue_list
    await ctx.send(embed=embed)

# --- Soundboard Commands & New Helper ---

async def play_sound_effect(ctx, sound_path: str, volume: float = 0.4):
    """
    A smart helper function to play a sound effect.
    It connects if not connected, and interrupts music if it's playing.
    """
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to use this command!")
        return
    
    if not os.path.exists(sound_path):
        await ctx.send(f"Oops, I couldn't find the sound file: `{sound_path}`")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    # Connect or move to the user's channel if necessary
    if voice_client is None:
        voice_client = await channel.connect()
    elif voice_client.channel != channel:
        await voice_client.move_to(channel)

    sound_source = discord.FFmpegPCMAudio(sound_path)
    volume_source = discord.PCMVolumeTransformer(sound_source, volume=volume)

    # If music is playing, stop it. The sound will play, and the 'after' will resume the queue.
    if voice_client.is_playing():
        voice_client.stop()
        voice_client.play(volume_source, after=lambda e: play_next_song(ctx))
    else:
        # If not playing anything, play the sound and then start the disconnect timer.
        voice_client.play(volume_source, after=lambda e: asyncio.run_coroutine_threadsafe(disconnect_after_delay(ctx), bot.loop))


@bot.command(name='heart', aliases=['broken_heart', '💔'])
async def heart_command(ctx):
    chosen_name = random.choice(names_to_pity)
    name_sound_path = f"sounds/{chosen_name.lower()}.mp3"
    # This command is special and should not be interruptible in the same way
    await play_sound_effect(ctx, name_sound_path, volume=1.0) 

    if ctx.invoked_with == '💔':
        await asyncio.sleep(0.5) 
        second_sound_name = random.choice(['oink.mp3', 'haha.mp3', 'obama.mp3', 'shit.mp3'])
        second_sound_path = f"sounds/{second_sound_name}"
        await play_sound_effect(ctx, second_sound_path)

@bot.command(name='hot_face', aliases=["🥵"])
async def hot_face(ctx):
    await play_sound_effect(ctx, 'sounds/bust.mp3')

@bot.command(name='obama')
async def obama(ctx):
    await play_sound_effect(ctx, 'sounds/obama.mp3')

@bot.command(name='oink')
async def oink(ctx):
    await play_sound_effect(ctx, 'sounds/oink.mp3')

# --- Other Commands ---
# (Unchanged commands are here for completeness)
@bot.command(name='remove', help="Removes a song from the queue by its number.")
async def remove(ctx, number: int):
    guild_id = ctx.guild.id
    if guild_id in song_queues and song_queues[guild_id]:
        if 1 <= number <= len(song_queues[guild_id]):
            removed_song = song_queues[guild_id].pop(number - 1)
            await ctx.send(f"🗑️ Removed **{removed_song['title']}** from the queue.")
        else:
            await ctx.send("Invalid number. Use `!queue` to see the song numbers.")
    else:
        await ctx.send("The queue is empty.")

@bot.command(name='skip', help="Skips the current song.")
async def skip(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Skipped to the next song. ⏭️")
    else:
        await ctx.send("I'm not playing anything right now.")

@bot.command(name='skipto', help="Skips to a specific song in the queue.")
async def skipto(ctx, number: int):
    guild_id = ctx.guild.id
    voice_client = ctx.voice_client

    if guild_id in song_queues and song_queues[guild_id]:
        if 1 <= number <= len(song_queues[guild_id]):
            song_queues[guild_id] = song_queues[guild_id][number-1:]
            if voice_client and voice_client.is_playing():
                voice_client.stop()
                await ctx.send(f"Skipped to **{song_queues[guild_id][0]['title']}**.")
            else:
                 await ctx.send("Queue has been updated.")
        else:
            await ctx.send("Invalid number. Use `!queue` to see song numbers.")
    else:
        await ctx.send("The queue is empty.")

@bot.command(name='pause', help="Pauses the current song.")
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Paused. ⏸️")

@bot.command(name='resume', help="Resumes the paused song.")
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Resumed. ▶️")

@bot.command(name='stop', aliases=['disconnect', 'leave'], help="Stops playback and disconnects the bot.")
async def stop(ctx):
    guild_id = ctx.guild.id
    if guild_id in song_queues:
        song_queues[guild_id] = [] # Clear the queue
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Stopped and disconnected. ⏹️")

@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(
        title="Bot Commands",
        description="Here is a list of all available commands.",
        color=discord.Color.purple()
    )
    embed.add_field(
        name="🎵 Music Commands",
        value="`!play <search/URL>`: Plays or adds a song/playlist to the queue.\n"
              "`!queue`: Shows the current song queue.\n"
              "`!skip`: Skips the current song.\n"
              "`!skipto <number>`: Skips to a song number in the queue.\n"
              "`!remove <number>`: Removes a song from the queue.\n"
              "`!pause`: Pauses the music.\n"
              "`!resume`: Resumes the music.\n"
              "`!stop`: Stops music and disconnects the bot.",
        inline=False
    )
    embed.add_field(
        name="🔊 Soundboard Commands",
        value="`!heart` or `!💔`: Plays a... special sound.\n"
              "`!hot_face` or `!🥵`: Plays another... special sound.\n"
              "`!oink`: Plays an oink sound.\n"
              "`!obama`: Plays an obama sound.",
        inline=False
    )
    embed.add_field(
        name="🛠️ Utility Commands",
        value="`!choose <opt1, opt2, ...>`: Chooses from a list of options.\n"
              "`!help`: Shows this message.",
        inline=False
    )
    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name='choose', help="Chooses from a list of options.")
async def choose(ctx, *, options):
    option_list = [opt.strip() for opt in options.split(',')]
    if len(option_list) < 2:
        await ctx.send("Please provide at least two options, separated by commas.")
        return
    choice = random.choice(option_list)
    await ctx.send(f"I choose: **{choice}**")

@choose.error
async def choose_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You need to give me some options to choose from! \nExample: `!choose heads, tails`")

# --- Run the Bot ---
bot.run(TOKEN)