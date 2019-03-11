from discord.ext import commands
from discord.ext.commands import HelpFormatter
import sys, traceback
from io import BytesIO
import discord
from PIL import Image
import asyncio
import aiohttp
import re

class CustomHelpFormatter(HelpFormatter):
    async def filter_command_list(self):
        """Returns a filtered list of commands based on the two attributes
        provided, :attr:`show_check_failure` and :attr:`show_hidden`. Also
        filters based on if :meth:`is_cog` is valid.
        Returns
        --------
        iterable
            An iterable with the filter being applied. The resulting value is
            a (key, value) tuple of the command name and the command itself.
        """
        def predicate(tuple):
            cmd = tuple[1]
            if self.is_cog():
                # filter commands that don't exist to this cog.
                if cmd.instance is not self.command:
                    return False

            if cmd.hidden and not self.show_hidden:
                return False

            if self.show_check_failure:
                # we don't wanna bother doing the checks if the user does not
                # care about them, so just return true.
                return True

            try:
                return cmd.can_run(self.context) and self.context.bot.can_run(self.context)
            except CommandError:
                return False

        #Custom iterator to display subcommands
        if not self.is_cog():
            iterator = {i.qualified_name: i for i in self.command.walk_commands()}.items()
        else:
            iterator = {i.qualified_name: i for i in self.context.bot.walk_commands()}.items()
        return filter(predicate, iterator)   

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
    async def admin_help(self, ctx, *commands : str):
        """Shows this message."""
        _mentions_transforms = {
            '@everyone': '@\u200beveryone',
            '@here': '@\u200bhere'
        }
        
        _mention_pattern = re.compile('|'.join(_mentions_transforms.keys()))

        admin_custom_help_formatter = CustomHelpFormatter(show_hidden=True, show_check_failure=True)
        bot = ctx.bot
        destination = ctx.message.author if bot.pm_help else ctx.message.channel

        def repl(obj):
            return _mentions_transforms.get(obj.group(0), '')

        # help by itself just lists our own commands.
        if len(commands) == 0:
            pages = await admin_custom_help_formatter.format_help_for(ctx, bot)
        elif len(commands) == 1:
            # try to see if it is a cog name
            name = _mention_pattern.sub(repl, commands[0])
            command = None
            if name in bot.cogs:
                command = bot.cogs[name]
            else:
                command = bot.all_commands.get(name)
                if command is None:
                    await destination.send(bot.command_not_found.format(name))
                    return

            pages = await admin_custom_help_formatter.format_help_for(ctx, command)
        else:
            name = _mention_pattern.sub(repl, commands[0])
            command = bot.all_commands.get(name)
            if command is None:
                await destination.send(bot.command_not_found.format(name))
                return

            for key in commands[1:]:
                try:
                    key = _mention_pattern.sub(repl, key)
                    command = command.all_commands.get(key)
                    if command is None:
                        await destination.send(bot.command_not_found.format(key))
                        return
                except AttributeError:
                    await destination.send(bot.command_has_no_subcommands.format(command, key))
                    return

            pages = await admin_custom_help_formatter.format_help_for(ctx, command)

        if bot.pm_help is None:
            characters = sum(map(len, pages))
            # modify destination based on length of pages.
            if characters > 1000:
                destination = ctx.message.author

        for page in pages:
            await destination.send(page)    

    @commands.command()
    async def help(self, ctx, *commands : str):
        """Shows this message."""
        _mentions_transforms = {
            '@everyone': '@\u200beveryone',
            '@here': '@\u200bhere'
        }
        
        _mention_pattern = re.compile('|'.join(_mentions_transforms.keys()))

        bot = ctx.bot
        bot.formatter = CustomHelpFormatter()
        destination = ctx.message.author if bot.pm_help else ctx.message.channel
    
        def repl(obj):
            return _mentions_transforms.get(obj.group(0), '')
    
        # help by itself just lists our own commands.
        if len(commands) == 0:
            pages = await bot.formatter.format_help_for(ctx, bot)
        elif len(commands) == 1:
            # try to see if it is a cog name
            name = _mention_pattern.sub(repl, commands[0])
            command = None
            if name in bot.cogs:
                command = bot.cogs[name]
            else:
                command = bot.all_commands.get(name)
                if command is None:
                    await destination.send(bot.command_not_found.format(name))
                    return
    
            pages = await bot.formatter.format_help_for(ctx, command)
        else:
            name = _mention_pattern.sub(repl, commands[0])
            command = bot.all_commands.get(name)
            if command is None:
                await destination.send(bot.command_not_found.format(name))
                return
    
            for key in commands[1:]:
                try:
                    key = _mention_pattern.sub(repl, key)
                    command = command.all_commands.get(key)
                    if command is None:
                        await destination.send(bot.command_not_found.format(key))
                        return
                except AttributeError:
                    await destination.send(bot.command_has_no_subcommands.format(command, key))
                    return
    
            pages = await bot.formatter.format_help_for(ctx, command)
    
        if bot.pm_help is None:
            characters = sum(map(len, pages))
            # modify destination based on length of pages.
            if characters > 1000:
                destination = ctx.message.author
    
        for page in pages:
            await destination.send(page)                

def setup(bot):
    bot.remove_command("help")
    bot.add_cog(TestCog(bot))
