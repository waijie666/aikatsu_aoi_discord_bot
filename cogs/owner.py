from discord.ext import commands
import sys, traceback


class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Hidden means it won't show up on the default help.
    @commands.command(name="load", hidden=True)
    @commands.is_owner()
    async def load_extension(self, ctx, *, cog: str):
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
    async def unload_extension(self, ctx, *, cog: str):
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
    async def reload_extension(self, ctx, *, cog: str):
        """Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            #self.bot.unload_extension(cog)
            #self.bot.load_extension(cog)
            self.bot.reload_extension(cog)
        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
            traceback.print_exc(file=sys.stdout)
        else:
            await ctx.send("**`ODAYAKAJANAI`**")

    def cog_unload(self):
        pass

def setup(bot):
    bot.add_cog(OwnerCog(bot))
