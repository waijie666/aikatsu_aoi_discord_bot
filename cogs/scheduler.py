from discord.ext import commands
import discord
import random
import sys, traceback


class SchedulerCog:
    def __init__(self, bot):
        self.bot = bot
        bot.apscheduler.add_job(self.change_client_presence, trigger="cron", minute="*/5", id="change_client_presence", replace_existing=True)
    
    async def change_client_presence(self):
        client_presence_list = ["Aikatsu Friends", "Aikatsu Stars", "Aikatsu"]
        client_presence_choice = random.choice(client_presence_list)
        await self.bot.change_presence(activity=discord.Game(name=client_presence_choice))

    # Hidden means it won't show up on the default help.
    @commands.command(name="add_job", hidden=True)
    @commands.is_owner()
    async def add_job(self, ctx, *, cog: str):
        """Command which Loads a Module.
        Remember to use dot path. e.g: cogs.owner"""
        pass



def setup(bot):
    bot.add_cog(SchedulerCog(bot))
