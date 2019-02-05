from discord.ext import commands
from discord.ext.commands import HelpFormatter
import sys, traceback


class OwnerCog:
    def __init__(self, bot):
        self.bot = bot

    # Hidden means it won't show up on the default help.
    @commands.command(name="load", hidden=True)
    @commands.is_owner()
    async def cog_load(self, ctx, *, cog: str):
        """Command which Loads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
        else:
            await ctx.send("**`ODAYAKAJANAI`**")

    @commands.command(name="unload", hidden=True)
    @commands.is_owner()
    async def cog_unload(self, ctx, *, cog: str):
        """Command which Unloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
        else:
            await ctx.send("**`ODAYAKAJANAI`**")

    @commands.command(name="reload", hidden=True)
    @commands.is_owner()
    async def cog_reload(self, ctx, *, cog: str):
        """Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
            traceback.print_exc(file=sys.stdout)
        else:
            await ctx.send("**`ODAYAKAJANAI`**")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def admin_help(self, ctx, *commands : str):
        custom_help_formatter = HelpFormatter(show_hidden=True, show_check_failure=True)
        """Shows this message."""
        bot = ctx.bot
        destination = ctx.message.author if bot.pm_help else ctx.message.channel
    
        def repl(obj):
            return _mentions_transforms.get(obj.group(0), '')
    
        # help by itself just lists our own commands.
        if len(commands) == 0:
            pages = await custom_help_formatter.format_help_for(ctx, bot)
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
    
            pages = await custom_help_formatter.format_help_for(ctx, command)
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
    
            pages = await custom_help_formatter.format_help_for(ctx, command)
    
        if bot.pm_help is None:
            characters = sum(map(len, pages))
            # modify destination based on length of pages.
            if characters > 1000:
                destination = ctx.message.author
    
        for page in pages:
            await destination.send(page)



def setup(bot):
    bot.add_cog(OwnerCog(bot))
