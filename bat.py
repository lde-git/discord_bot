import discord
from discord.ext import commands
import os
import random
import asyncio
from dotenv import load_dotenv

# Load the bot token from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True 

# Create a bot instance with a command prefix and the defined intents
bot = commands.Bot(command_prefix='!', intents=intents)

names_to_pity = ['Lukas', 'Alex', 'Kally']

# arena_pity_texts = [
#     "Wir zünden eine Kerze für **{name}** an. Nicht, weil er krank ist, sondern weil er freiwillig im digitalen Elend der League of Legends Arena schmort. Und das auch noch alleine. Man stelle sich das Bild vor: **{name}**, wie er mit einem zufälligen, 14-jährigen Teamkollegen, der nur 'git gud' in den Chat spammt, versucht, gegen eine unbesiegbare Taric-Master-Yi-Kombo zu bestehen. Es ist ein Trauerspiel. 🕯️",
#     "Man hat uns berichtet, dass **{name}** jetzt seine Abende alleine in der Arena verbringt. Alleine! In einem 2v2v2v2 Modus! Das ist so, als würde man freiwillig mit verbundenen Augen und einem Bein auf dem Rücken an einem Tanzwettbewerb teilnehmen. Jeder Sieg ist ein reiner Glücksfall, jede Niederlage eine bittere Bestätigung seiner selbstgewählten Isolation.",
#     "Erinnerst du dich, als **{name}** noch Hobbys hatte? Als er noch das Sonnenlicht sah? Jetzt hat er sich für die Arena entschieden. Alleine. Sein einziger sozialer Kontakt besteht darin, von einem Duo mit perfekt abgestimmten Namen und Skins gedemütigt zu werden, während sein eigener Partner versucht, mit Anvil-Augments auf einem AD-Carry zu 'skalieren'. Ruhe in Frieden, Sozialleben von **{name}**. 🕊️",
#     "Wir haben eine Theorie: **{name}** spielt nicht wirklich alleine. Er hat sich mit dem AFK-Bot angefreundet, den er in jedem zweiten Spiel als Partner bekommt. Sie haben eine besondere Verbindung. Der Bot läuft in die Flammenwand, und **{name}** schreit seinen Monitor an. Eine moderne Liebesgeschichte. Es ist fast schon poetisch, wie tief man sinken kann.",
#     "'**{name}** spielt Arena nur zum Spaß', sagen sie. Ja, sicher. Und ich gehe zum Zahnarzt für eine Wurzelbehandlung, weil ich die Bohrgeräusche so entspannend finde. Der 'Spaß' in der Solo-Arena besteht darin, zu sehen, ob man durch pures Glück ein spielbares Augment bekommt oder ob man wieder mit 'Erdbeben' auf Janna endet. Wir bedauern zutiefst diese verzweifelte Suche nach Freude am falschen Ort.",
#     "Ein Ornithologe kann einen Vogel an seinem Ruf erkennen. Wir können **{name}** an den Geräuschen erkennen, die aus seiner Wohnung dringen: ein leises Wimmern, gefolgt von einem lauten 'WARUM ICH?!', wenn der Gegner mit dem 'Goliath'-Augment und 8000 Lebenspunkten auf ihn zurollt. Sein Verstand ist so gebrochen wie die Spielbalance dieses Modus.",
#     "Vielleicht haben wir **{name}** falsch eingeschätzt. Vielleicht ist er kein Opfer, sondern ein Täter. Der Typ, der alleine in die Arena geht, um der Partner von jemand anderem zu sein und dessen Spielerlebnis aktiv zu ruinieren. Er wählt Heimerdinger, stellt seine Türme in die Ecke und schaut Netflix. In diesem Fall... ist unser Bedauern noch größer, denn wer so etwas tut wie **{name}**, hat die Kontrolle über sein Leben endgültig verloren.",
#     "Rein statistisch gesehen ist die Wahrscheinlichkeit, in der Solo-Arena einen kompetenten, nicht-toxischen Partner zu bekommen, geringer als von einem Blitz getroffen zu werden, während man im Lotto gewinnt. Und **{name}** versucht dieses Glücksspiel jeden Abend aufs Neue. Das ist kein Hobby mehr, das ist eine ausgewachsene Sucht nach Bestrafung. Wir hoffen, er findet bald Hilfe.",
#     "**{name}** schreibt 'gl hf' in den Chat. Niemand antwortet. Er pingt, dass er angreifen will. Sein Partner farmt die Pflanze in der Mitte. Er stirbt einen heldenhaften Tod. Sein Partner tanzt. Die Arena ist ein Spiegel seiner Seele: eine kalte, leere Fläche, in der seine Schreie ungehört verhallen. Tiefes, tiefes Mitleid.",
#     "Am Ende kämpft **{name}** nicht gegen die sieben anderen Teams. Er kämpft nicht einmal gegen die unausgewogenen Champions oder die zufälligen Augments. Er kämpft gegen die erdrückende Gewissheit, dass er diesen digitalen Tiefpunkt ganz alleine erreicht hat. Und während der Feuerring sich um ihn schließt, erkennt er: Der wahre Schmerz ist nicht das Ausscheiden, sondern das Wissen, dass er danach wieder alleine in der Warteschlange sitzt. Ein Teufelskreis. F."
# ]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('Bot is ready to be used!')

@bot.command()
async def choose(ctx, *, options):
    """Chooses one option from a comma-separated list."""
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


@bot.command(name='heart', aliases=['broken_heart', '💔'])
async def heart_command(ctx):
    """Joins voice, plays sound(s), and sends a pity message.
    The '💔' alias plays an extra random sound."""
    
    # --- CHOOSE NAME AND PREPARE MESSAGES/SOUNDS ---
    chosen_name = random.choice(names_to_pity)
    pity_text = random.choice(arena_pity_texts)
    final_message = pity_text.format(name=chosen_name)
    name_sound_path = f"sounds/{chosen_name.lower()}.mp3"
    
    # --- VOICE CHANNEL LOGIC ---
    if ctx.author.voice:
        if not os.path.exists(name_sound_path):
            await ctx.send(f"Oops, I couldn't find the sound file for {chosen_name} (`{name_sound_path}`).")
        else:
            channel = ctx.author.voice.channel
            voice_client = None # Define voice_client to ensure it's available in the finally block
            try:
                # Connect to voice
                if ctx.voice_client is not None:
                    voice_client = await ctx.voice_client.move_to(channel)
                else:
                    voice_client = await channel.connect()

                # 1. Play the first sound (the name)
                audio_source1 = discord.FFmpegPCMAudio(name_sound_path)
                voice_client.play(audio_source1)
                while voice_client.is_playing():
                    await asyncio.sleep(1)

                # 2. If the '💔' alias was used, play a second, random sound
                if ctx.invoked_with == '💔':
                    second_sound_name = random.choice(['oink.mp3', 'haha.mp3', 'obama.mp3', 'shit.mp3'])
                    second_sound_path = f"sounds/{second_sound_name}"
                    
                    if not os.path.exists(second_sound_path):
                         await ctx.send(f"I was supposed to play a second sound, but I couldn't find `{second_sound_path}`.")
                    else:
                        audio_source2 = discord.FFmpegPCMAudio(second_sound_path)
                        voice_client.play(audio_source2)
                        while voice_client.is_playing():
                            await asyncio.sleep(1)

            except Exception as e:
                print(f"Error during voice playback: {e}")
            finally:
                # Disconnect after all sounds are finished or if an error occurred
                if voice_client and voice_client.is_connected():
                    await voice_client.disconnect()
    #else:
    #    await ctx.send("You're not in a voice channel, so I can't play any sounds, but here's your message:")

    # --- SEND TEXT MESSAGE ---
    #await ctx.send(final_message)


@bot.command(name='hot_face', aliases=["🥵"])
async def hot_face(ctx):
    # Check if the person who sent the command is in a voice channel
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        
        # Connect to the voice channel
        voice_client = await channel.connect()
        
        # Define the audio source
        audio_source = discord.FFmpegPCMAudio('sounds/bust.mp3')
        
        volume_adjusted_source = discord.PCMVolumeTransformer(audio_source, volume=0.4)
        
        # Play the sound and disconnect when finished
        voice_client.play(volume_adjusted_source, after=lambda e: print(f'Finished playing, error: {e}'))
        
        while voice_client.is_playing():
            await asyncio.sleep(1) # Wait until the sound is done
        
        await voice_client.disconnect()

    else:
        await ctx.send("You need to be in a voice channel to use this command!")

# Run the bot with your token
bot.run(TOKEN)