import discord
from discord.ext import commands
from yt_dlp import YoutubeDL

from logger import MyLogger
from global_variables import client, GUILD_ID


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot._pending_application_commands = []

        self.is_playing = False
        self.is_loop = False
        self.music_queue = []
        self.last_request_channel_id = None

        self.YDL_OPTIONS = {
            'format': 'bestaudio',
            'noplaylist': 'True',
            'logger': MyLogger()
        }

        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        self.vc = None

        self.help_message = """
```
General commands:
/help - displays all the available commands
/play <keywords> - finds the song on youtube and plays it in your current channel
/queue - displays the current music queue
/skip - skips the current song being played
/clear - Stops the music and clears the queue
/leave - Disconnected the bot from the voice channel
/loop <on/off/check> - turn on / off or check loop mode status
/remove <song_index> - removes song with specified number in the queue 
```
        """

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception:
                return False

        return {'source': info['url'], 'title': info['title']}

    def print_current(self, song_title):
        channel = client.get_channel(self.last_request_channel)
        client.loop.create_task(channel.send(f'Currently playing: "{song_title}"'))

    def play_next(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            # get the first url
            m_url = self.music_queue[0][0]['source']
            m_name = self.music_queue[0][0]['title']

            self.print_current(m_name)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                         after=lambda e: (self.delete_current(), self.play_next(ctx)))
        else:
            self.is_playing = False

    def delete_current(self, *, force=False):
        if (not self.is_loop and not force) or (self.is_loop and force):
            self.music_queue.pop(0)

    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            m_name = self.music_queue[0][0]['title']

            # try to connect to voice channel if you are not already connected
            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                # in case we fail to connect
                if self.vc == None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])

            self.print_current(m_name)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                         after=lambda e: (self.delete_current(), self.play_next(ctx)))
        else:
            self.is_playing = False

    @client.slash_command(name="play", guild_ids=GUILD_ID,
                          description="Plays a selected song from youtube")
    async def play(self, ctx, query: str):
        await ctx.defer()
        self.last_request_channel = ctx.channel.id
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            # you need to be connected so that the bot knows where to go
            await ctx.followup.respond("Connect to a voice channel!")
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.followup.respond(
                    "Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.")
            else:
                await ctx.followup.send(f'Song "{song["title"]}" added to the queue')
                self.music_queue.append([song, voice_channel])

                if self.is_playing == False:
                    await self.play_music(ctx)

    @client.slash_command(name="skip", guild_ids=GUILD_ID,
                          description="Skips the current song being played")
    async def skip(self, ctx):
        if self.vc != None and self.vc:
            await ctx.respond(f'Song skipped')

            self.delete_current(force=True)
            self.vc.stop()

    @client.slash_command(name='loop', guild_ids=GUILD_ID,
                          description='Turn on/off looping of current track')
    async def loop(self, ctx, mode):
        if mode == 'on':
            self.is_loop = True
        elif mode == 'off':
            self.is_loop = False
        elif mode != 'check':
            return
        await ctx.respond(f'Current loop status: {self.is_loop}')

    @client.slash_command(name="queue", guild_ids=GUILD_ID,
                          description="Displays the current songs in queue")
    async def queue(self, ctx):
        songs_queue = ''
        retval = ""

        if len(self.music_queue) > 0:
            cur = f'Current: \n{self.music_queue[0][0]["title"]} \n'
            songs_queue += cur

        for i in range(1, len(self.music_queue)):
            retval += f"{i}) {self.music_queue[i][0]['title']}\n"

        if retval != "":
            songs_queue += 'Queue: \n' + retval
        else:
            songs_queue += "No music in queue"

        await ctx.respond(songs_queue)

    @client.slash_command(name='remove', guild_ids=GUILD_ID,
                          description='removes song with specified number in the queue')
    async def remove(self, ctx, ind: int):
        if 0 <= ind - 1 <= len(self.music_queue) - 1:
            deleted = self.music_queue.pop(ind)
            await ctx.respond(f'Song "{deleted[0]["title"]}" removed from queue')
        else:
            await ctx.respond('Invalid index')

    @client.slash_command(name="clear", guild_ids=GUILD_ID,
                          description="Stops the music and clears the queue")
    async def clear(self, ctx):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []

        await ctx.respond(f'Music queue cleared')

    @client.slash_command(name="leave", guild_ids=GUILD_ID, description="Kick the bot from VC")
    async def leave(self, ctx):
        await self.vc.disconnect()

        self.is_playing = False
        self.is_loop = False
        self.vc = None
        self.music_queue = []

        await ctx.respond(f'Bot disconnected')

    @client.slash_command(name="help", guild_ids=GUILD_ID,
                          description="Displays all the available commands")
    async def help(self, ctx):
        await ctx.respond(self.help_message)


def setup(bot):
    bot.add_cog(MusicCog(bot))
