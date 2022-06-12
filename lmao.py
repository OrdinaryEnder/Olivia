import discord
import os
from discord.ext import commands
import json
from botmod import bypass
import youtube_dl
import asyncio
import utilities
import requests


owner = '796915832617828352'

bot = commands.Bot(command_prefix='-')

intents = discord.Intents.default()
intents.members = True

@bot.event
async def on_ready():
 print("Runnin")

bot.event
async def on_message_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send("Unknown command")
    
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send("Argument Missing")

@bot.command(name='lvbypass', description='Bypass Linkvertise using bypass.vip api')
async def _lvbypass(ctx, url):
      link = bypass(url)
      loadlink = json.dumps(link)
      result = json.loads(loadlink)
      await ctx.send("Result:")
      await ctx.send(result)

@bot.command()
@commands.is_owner()
async def shutdown(ctx):
     await ctx.send("CTRL+ALT+DEL PRESSED")
     await ctx.send("Bye :(")
     await ctx.bot.logout()

@bot.command(name='kick', description='Kick Dumbass from Your Holy Server')
@commands.has_permissions(kick_members=True)
async def _kick(self, ctx, Member: discord.Member):
        if ctx.author.top_role < user.top_role:
                return await ctx.send("**You don't have enough permission**")
        if ctx.author.top_role > user.top_role:
                return await bot.kick(Member)
                return await ctx.send(f"{user} Successfully Banned by {ctx.author.mention}")


@bot.command(name='ban', description='Ban dumbass from your Holy Server')
@commands.has_permissions(ban_members=True)
async def _ban(ctx, user: discord.Member, *, reason=None):
	if reason == None:
		reason = f"{user} banned by {ctx.author}"
	if ctx.author.top_role < user.top_role:
		return await ctx.send("**You don't have enough permission**")
	if ctx.author.top_role > user.top_role:
		return await ctx.guild.ban(user, reason=reason)
		return await ctx.send(f"{user} Successfully Banned by {ctx.author.mention}")

@bot.command(name='unban', description='Unban people who have repented')
@commands.has_permissions(ban_members=True)
async def _unban(ctx, id: int):
    user = await bot.fetch_user(id)
    await ctx.guild.unban(user)

@bot.command(name='mute', description='Mute Whos Keep Spamming on ur Holy Server', pass_context = True)
@commands.has_permissions(manage_messages=True)
async def _mute(ctx, member: discord.Member, mute_time : int):
        if not member:
         await ctx.send("Who do you want me to mute?")
        return
        role = discord.utils.get(member.server.roles, name='Muted')
        time_convert = {"s":1, "m":60, "h":3600,"d":86400}
        tempmute= int(time[0]) * time_convert[mute_time[-1]]
        await ctx.add_roles(member, role)
        embed=discord.Embed(title="User Muted!", description="**{0}** was muted by **{1}**!".format(member, ctx.message.author), color=0xff00f6)
        await ctx.send(embed=embed)
        
        await asyncio.sleep(tempmute)
        await member.remove_roles(role)


@bot.command(name='unmute', description='Unmute')
@commands.has_permissions(manage_messages=True)
async def unmute(ctx, member: discord.Member):
   mutedRole = discord.utils.get(ctx.guild.roles, name="Muted")

   await member.remove_roles(mutedRole)
   await member.send(f" you have unmutedd from: - {ctx.guild.name}")
   embed = discord.Embed(title="Unmuted", description=f" unmuted-{member.mention}",colour=discord.Colour.light_gray())
   await ctx.send(embed=embed)

# YouTube is a bitch and tries to disconnect our bot from its servers. Use this to reconnect instantly
# (Because of this disconnect/reconnect cycle, sometimes you will listen a sudden and brief stop)
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

# List with all the sessions currently active.
# TODO: Terminate season after X minutes have passed without interaction.
sessions = []


def check_session(ctx):
    """
    Checks if there is a session with the same characteristics (guild and channel) as ctx param.

    :param ctx: discord.ext.commands.Context

    :return: session()
    """
    if len(sessions) > 0:
        for i in sessions:
            if i.guild == ctx.guild and i.channel == ctx.author.voice.channel:
                return i
        session = utilities.Session(
            ctx.guild, ctx.author.voice.channel, id=len(sessions))
        sessions.append(session)
        return session
    else:
        session = utilities.Session(ctx.guild, ctx.author.voice.channel, id=0)
        sessions.append(session)
        return session


def prepare_continue_queue(ctx):
    """
    Used to call next song in queue.

    Because lambda functions cannot call async functions, I found this workaround in discord's api documentation
    to let me continue playing the queue when the current song ends.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    fut = asyncio.run_coroutine_threadsafe(continue_queue(ctx), bot.loop)
    try:
        fut.result()
    except Exception as e:
        print(e)


async def continue_queue(ctx):
    """
    Check if there is a next in queue then proceeds to play the next song in queue.

    As you can see, in this method we create a recursive loop using the prepare_continue_queue to make sure we pass
    through all songs in queue without any mistakes or interaction.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    session = check_session(ctx)
    if not session.q.theres_next():
        await ctx.send("Queue is over homie")
        return

    session.q.next()

    voice = discord.utils.get(bot.voice_clients, guild=session.guild)
    source = await discord.FFmpegOpusAudio.from_probe(session.q.current_music.url, **FFMPEG_OPTIONS)

    if voice.is_playing():
        voice.stop()

    voice.play(source, after=lambda e: prepare_continue_queue(ctx))
    await ctx.send(session.q.current_music.thumb)
    await ctx.send(f"Playing now: {session.q.current_music.title}")


@bot.command(name='play')
async def play(ctx, *, arg):
    """
    Checks where the command's author is, searches for the music required, joins the same channel as the command's
    author and then plays the audio directly from YouTube.

    :param ctx: discord.ext.commands.Context
    :param arg: str
        arg can be url to video on YouTube or just as you would search it normally.
    :return: None
    """
    try:
        voice_channel = ctx.author.voice.channel

    # If command's author isn't connected, return.
    except AttributeError as e:
        print(e)
        await ctx.send("You're not connected to a voice channel homie, Connect first")
        return

    # Finds author's session.
    session = check_session(ctx)

    # Searches for the video
    with youtube_dl.YoutubeDL({'format': 'bestaudio', 'noplaylist': 'True'}) as ydl:
        try:
            requests.get(arg)
        except Exception as e:
            print(e)
            info = ydl.extract_info(f"ytsearch:{arg}", download=False)[
                'entries'][0]
        else:
            info = ydl.extract_info(arg, download=False)

    url = info['formats'][0]['url']
    thumb = info['thumbnails'][0]['url']
    title = info['title']

    session.q.enqueue(title, url, thumb)

    # Finds an available voice client for the bot.
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice:
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    # If it is already playing something, adds to the queue
    if voice.is_playing():
        await ctx.send(thumb)
        await ctx.send(f"Added to queue: {title}")
        return
    else:
        await ctx.send(thumb)
        await ctx.send(f"Playing now: {title}")

        # Guarantees that the requested music is the current music.
        session.q.set_last_as_current()

        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        voice.play(source, after=lambda ee: prepare_continue_queue(ctx))


@bot.command(name='next', aliases=['skip'])
async def skip(ctx):
    """
    Skips the current song, playing the next one in queue if there is one.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    # Finds author's session.
    session = check_session(ctx)
    # If there isn't any song to be played next, return.
    if not session.q.theres_next():
        await ctx.send("There nothing in the queue, homie")
        return

    # Finds an available voice client for the bot.
    voice = discord.utils.get(bot.voice_clients, guild=session.guild)

    # If it is playing something, stops it. This works because of the "after" argument when calling voice.play as it is
    # a recursive loop and the current song is already going to play the next song when it stops.
    if voice.is_playing():
        voice.stop()
        return
    else:
        # If nothing is playing, finds the next song and starts playing it.
        session.q.next()
        source = await discord.FFmpegOpusAudio.from_probe(session.q.current_music.url, **FFMPEG_OPTIONS)
        voice.play(source, after=lambda e: prepare_continue_queue(ctx))
        return


@bot.command(name='print')
async def print_info(ctx):
    """
    A debug command to find session id, what is current playing and what is on the queue.
    :param ctx: discord.ext.commands.Context
    :return: None
    """
    session = check_session(ctx)
    await ctx.send(f"Session ID: {session.id}")
    await ctx.send(f"Current music: {session.q.current_music.title}")
    queue = [q[0] for q in session.q.queue]
    await ctx.send(f"Queue: {queue}")


@bot.command(name='leave')
async def leave(ctx):
    """
    If bot is connected to a voice channel, it leaves it.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_connected:
        check_session(ctx).q.clear_queue()
        await voice.disconnect()
    else:
        await ctx.send("Bot not connect, so it can't leave.")


@bot.command(name='pause')
async def pause(ctx):
    """
    If playing audio, pause it.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("It's not playing homie")


@bot.command(name='resume')
async def resume(ctx):
    """
    If audio is paused, resumes playing it.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_paused:
        voice.resume()
    else:
        await ctx.send("Already Paused, Play it Homie")


@bot.command(name='stop')
async def stop(ctx):
    """
    Stops playing audio and clears the session's queue.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    session = check_session(ctx)
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing:
        voice.stop()
        session.q.clear_queue()
    else:
        await ctx.send("There's nothing playing homie.")






bot.run('OTcyNDU5MjE3NTQ4MDk5NTg0.YnZXOA.Jix0nm_big4YbfGqTbRTE6aQUy4')