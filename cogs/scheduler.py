from discord.ext import commands
import discord
import random
import sys, traceback


class SchedulerCog:
    def __init__(self, bot):
        self.bot = bot
        bot.apscheduler.add_job(
            self.change_client_presence,
            trigger="cron",
            minute="*/5",
            id="change_client_presence",
            replace_existing=True,
        )

    async def change_client_presence(self):
        client_presence_list = ["Aikatsu Friends", "Aikatsu Stars", "Aikatsu"]
        client_presence_choice = random.choice(client_presence_list)
        await self.bot.change_presence(
            activity=discord.Game(name=client_presence_choice)
        )

    async def message_send(self, channel, message):
        await channel.send(message)

    # Hidden means it won't show up on the default help.
    @commands.command(name="listjob", hidden=True)
    @commands.is_owner()
    async def listjob(self, ctx):
        for job in self.bot.apscheduler.get_jobs():
            await ctx.send(
                "name: %s, trigger: %s, next run: %s"
                % (job.name, job.trigger, job.next_run_time)
            )

    @commands.command(name="schedule_message", hidden=True)
    @commands.is_owner()
    async def schedule_message(
        self, ctx, channel: discord.TextChannel, datetime: str, message: str
    ):
        self.bot.apscheduler.add_job(
            self.message_send,
            trigger="date",
            run_date=datetime,
            kwargs={"channel": channel, "message": message},
        )


def setup(bot):
    bot.add_cog(SchedulerCog(bot))
