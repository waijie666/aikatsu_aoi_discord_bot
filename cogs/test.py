from discord.ext import commands
import sys, traceback
from io import BytesIO
import discord
from PIL import Image
import asyncio
import aiohttp
import re
from discord.ext.commands import DefaultHelpCommand
import itertools
import concurrent.futures
from datetime import datetime
from collections import Counter
import json

class HelpCommandWithSubcommands(DefaultHelpCommand):

    def __init__(self):
        attrs = {'aliases': ['admin_help']}
        super().__init__(command_attrs=attrs)

    async def prepare_help_command(self, ctx, command):
        await super().prepare_help_command(ctx, command)
        if ctx.invoked_with == 'admin_help' and ctx.message.author.id == ctx.bot.owner_id: 
            self.show_hidden = True
            self.verify_checks = False
        else:
            self.show_hidden = False
            self.verify_checks = True

    def add_indented_commands(self, commands, *, heading, max_size=None):
        """Indents a list of commands after the specified heading.
        The formatting is added to the :attr:`paginator`.
        The default implementation is the command name indented by
        :attr:`indent` spaces, padded to ``max_size`` followed by
        the command's :attr:`Command.short_doc` and then shortened
        to fit into the :attr:`width`.
        Parameters
        -----------
        commands: Sequence[:class:`Command`]
            A list of commands to indent for output.
        heading: :class:`str`
            The heading to add to the output. This is only added
            if the list of commands is greater than 0.
        max_size: Optional[:class:`int`]
            The max size to use for the gap between indents.
            If unspecified, calls :meth:`get_max_size` on the
            commands parameter.
        """

        if not commands:
            return

        self.paginator.add_line(heading)
        max_size = max_size or self.get_max_size(commands)

        get_width = discord.utils._string_width
        for command in commands:
            name = command.qualified_name
            width = max_size - (get_width(name) - len(name))
            entry = '{0}{1:<{width}} {2}'.format(self.indent * ' ', name, command.short_doc, width=width)
            self.paginator.add_line(self.shorten_text(entry))

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            # <description> portion
            self.paginator.add_line(bot.description, empty=True)

        no_category = '\u200b{0.no_category}:'.format(self)
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name + ':' if cog is not None else no_category

        filtered = await self.filter_commands(set(bot.walk_commands()), sort=True, key=get_category)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)

        # Now we can add the commands to the page.
        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.qualified_name) if self.sort_commands else list(commands)
            self.add_indented_commands(commands, heading=category, max_size=max_size)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()


class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = HelpCommandWithSubcommands()
        bot.help_command.cog = self
        self.bot.thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

    @commands.command()
    async def image_echo(self, ctx):
        if len(ctx.message.attachments) > 0 :
            for attachment in ctx.message.attachments  : 
                file_object = BytesIO()
                await attachment.save(file_object)
                filename = attachment.filename
                discord_file = discord.File(file_object, filename)
                await ctx.send(file=discord_file)

    @commands.command()
    async def image_echo_resize(self, ctx):
        if len(ctx.message.attachments) > 0 :
            for attachment in ctx.message.attachments  :
                file_object = BytesIO()
                await attachment.save(file_object)
                size = attachment.size 
                filename = attachment.filename
                if filename.casefold().endswith("jpg") or filename.casefold().endswith("jpeg"):
                    format = "JPEG"
                elif filename.casefold().endswith("png"):
                    format = "PNG"
                elif filename.casefold().endswith("gif"):
                    format = "GIF"
                image = Image.open(file_object)
                width, height = image.size
                resized_image = image.resize((int(width*2),int(height*2)), Image.LANCZOS)
                new_width, new_height = resized_image.size
                file_object2 = BytesIO()
                resized_image.save(file_object2, format, optimize=True)
                new_size = file_object2.tell()
                file_object2.seek(0)
                discord_file = discord.File(file_object2, filename)
                embed = discord.Embed(title="Image Info")
                embed.add_field(name="Filename", value=filename, inline=False)
                embed.add_field(name="Original Size", value=str(size))
                embed.add_field(name="Image Dimensions", value=f"{str(width)}x{str(height)}")
                embed.add_field(name="New Size", value=str(new_size))
                embed.add_field(name="New Image Dimensions", value=f"{str(new_width)}x{str(new_height)}")
                await ctx.send(embed=embed)
                await ctx.send(file=discord_file)

    @commands.command()
    async def bigemoji(self, ctx, emoji : discord.PartialEmoji ):
        async with aiohttp.ClientSession() as session:
            async with session.get(emoji.url) as r:
                if r.status == 200:
                    bytes = await r.read()
                    file_object = BytesIO(bytes)
                    image = Image.open(file_object)
                    width, height = image.size
                    resized_image = image.resize((int(width*4),int(height*4)), Image.LANCZOS)
                    file_object2 = BytesIO()
                    resized_image.save(file_object2, "PNG", optimize=True)
                    file_object2.seek(0)
                    discord_file = discord.File(file_object2, emoji.name+".png")
                    await ctx.send(file=discord_file)

    @bigemoji.error 
    async def bigemoji_error_handler(self, ctx, error):
        await ctx.send("Need valid Discord Custom Emoji")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def read_message(self, ctx, channel : discord.TextChannel ):
        start_time = datetime.now()
        emoji_counter = Counter()
        async for message in channel.history(limit=None, reverse=True):
            message_content=message.content
            emoji_list = list(set(re.findall(r'<:.*?:.*?>', message_content)))
            emoji_counter += Counter(emoji_list)
        end_time = datetime.now()
        await ctx.send(f"{channel.mention} processed in {str(end_time-start_time)}")
        await ctx.send(str(emoji_counter.most_common(30)))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def emoji_counter_all_channel(self, ctx):
        channel_list = [ channel for channel in ctx.guild.text_channels if channel.category_id not in [360581693549182986,406241715712950272]] 
        server_emoji_list = [ str(emoji) for emoji in ctx.guild.emojis ]
        all_start_time = datetime.now()
        all_emoji_counter = Counter()
        for channel in channel_list:
            self.emoji_counter_channel = channel
            start_time = datetime.now()
            emoji_counter = Counter()
            async for message in channel.history(limit=None, reverse=True):
                message_content=message.content
                self.emoji_counter_message = message
                emoji_list = [ emoji for emoji in set(re.findall(r'<:.*?:.*?>', message_content)) if emoji in server_emoji_list ]
                emoji_counter += Counter(emoji_list)
            end_time = datetime.now()
            await ctx.send(f"{ctx.author.mention} {channel.mention} processed in {str(end_time-start_time)}")
            await ctx.send(str(emoji_counter.most_common(30)))
            all_emoji_counter += emoji_counter
        all_end_time = datetime.now()
        self.bot.all_emoji_counter = all_emoji_counter
        await ctx.send(f"{ctx.author.mention} All channels processed in {str(all_end_time-all_start_time)}")
        await ctx.send(str(all_emoji_counter.most_common(30)))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def emoji_counter_all_channel_status(self, ctx):
        await ctx.send(f"{self.emoji_counter_channel.mention} {str(self.emoji_counter_message.created_at)}")

    @commands.command()
    async def emoji_counter_show(self, ctx):
        emoji_counter_sorted = self.bot.all_emoji_counter.most_common()
        await ctx.send(str(emoji_counter_sorted[:30])) 
        await ctx.send(str(emoji_counter_sorted[30:])) 

    @commands.command(hidden=True)
    @commands.is_owner()
    async def emoji_counter_dump(self, ctx):
        with open('emoji_counter.json','w+') as fp:
            json.dump(self.bot.all_emoji_counter, fp)   

    @commands.command(hidden=True)
    @commands.is_owner()
    async def list_channel(self, ctx):
        channel_list = [ channel for channel in ctx.guild.text_channels if channel.category_id not in [360581693549182986,406241715712950272]]
        channel_mentions = [ channel.mention for channel in channel_list ]
        channel_mentions_string = ' '.join(channel_mentions)
        await ctx.send(channel_mentions_string)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def list_emoji(self, ctx):
        emoji_list = [ str(emoji) for emoji in ctx.guild.emojis ] 
        await ctx.send(" ".join(emoji_list))




def setup(bot):
    #bot.remove_command("help")
    bot.add_cog(TestCog(bot))
