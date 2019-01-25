import os
from dotenv import load_dotenv, find_dotenv
import random
import json
import discord
import aiohttp
import logging
import pytz
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from os import listdir
from os.path import isfile, join
import sys, traceback
import concurrent.futures

# Logging config

format = "%(asctime)s:%(name)s.%(levelname)s:%(message)s"
logging.basicConfig(level=logging.INFO, format=format)


class NoRunningFilter(logging.Filter):
    def filter(self, record):
        if "change_client_presence" in record.getMessage():
            return False
        else:
            return True


my_filter = NoRunningFilter()
logging.getLogger("apscheduler.executors.default").addFilter(my_filter)

# Initial bot initialization

load_dotenv(find_dotenv())
API_KEY = os.environ.get("API_KEY")
cogs_dir = "cogs"
command_prefix = "!!!"
bot = commands.Bot(command_prefix=command_prefix, case_insensitive=True)
bot.first_startup = False

# Scheduler related intialization and functions


async def change_client_presence():
    client_presence_list = ["Aikatsu Friends", "Aikatsu Stars", "Aikatsu"]
    client_presence_choice = random.choice(client_presence_list)
    await bot.change_presence(activity=discord.Game(name=client_presence_choice))


bot.apscheduler = AsyncIOScheduler(
    event_loop=bot.loop, timezone=pytz.timezone("Asia/Tokyo")
)
bot.apscheduler.add_jobstore(
    "sqlalchemy", alias="sqlite", url="sqlite:///scheduler.sqlite"
)
bot.apscheduler.add_job(
    change_client_presence,
    trigger="cron",
    minute="*/5",
    replace_existing=True,
    jobstore="default",
)


async def message_send(channel_id, message):
    await bot.get_channel(channel_id).send(message)


@bot.command(name="list_job", hidden=True)
@commands.is_owner()
async def listjob(ctx):
    for job in bot.apscheduler.get_jobs():
        await ctx.send(
            "name: %s, trigger: %s, next run: %s"
            % (job.name, job.trigger, job.next_run_time)
        )


@bot.command(name="schedule_message", hidden=True)
@commands.is_owner()
async def schedule_message(
    ctx, channel: discord.TextChannel, datetime: str, message: str
):
    bot.apscheduler.add_job(
        message_send,
        trigger="date",
        run_date=datetime,
        kwargs={"channel_id": channel.id, "message": message},
        jobstore="sqlite",
    )


@bot.event
async def on_ready():
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")
    if bot.first_startup is False:
        bot.clientsession = aiohttp.ClientSession()
        bot.apscheduler.start()
        bot.first_startup = True


@bot.event
async def on_message(message):
    if bot.user in message.mentions:
        await message.channel.send(command_prefix + "help for help")
        return
    await bot.process_commands(message)


@bot.command(name="list_extension", hidden=True)
@commands.is_owner()
async def list_extension(ctx):
    await ctx.send([*bot.extensions])


if __name__ == "__main__":
    for extension in [
        f.replace(".py", "") for f in listdir(cogs_dir) if isfile(join(cogs_dir, f))
    ]:
        try:
            bot.load_extension(cogs_dir + "." + extension)
        except (discord.ClientException, ModuleNotFoundError):
            print(f"Failed to load extension {extension}.")
            traceback.print_exc()

bot.run(API_KEY)
