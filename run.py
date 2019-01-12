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

load_dotenv(find_dotenv())
API_KEY = os.environ.get("API_KEY")

command_prefix = "!!!"
bot = commands.Bot(command_prefix=command_prefix, case_insensitive=True)
bot.first_startup = False
scheduler = AsyncIOScheduler(event_loop=bot.loop, timezone=pytz.timezone("Asia/Tokyo"))

cogs_dir = "cogs"


async def change_client_presence():
    client_presence_list = ["Aikatsu Friends", "Aikatsu Stars", "Aikatsu"]
    client_presence_choice = random.choice(client_presence_list)
    await bot.change_presence(activity=discord.Game(name=client_presence_choice))


@bot.event
async def on_ready():
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")
    await change_client_presence()
    if bot.first_startup is False:
        bot.clientsession = aiohttp.ClientSession()
        scheduler.start()
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


scheduler.add_job(change_client_presence, trigger="cron", minute="*/5")

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
