import os
from dotenv import load_dotenv, find_dotenv
import random
import json
import discord
import aiohttp
import logging
import logging.handlers
import pytz
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from os import listdir
from os.path import isfile, join
import sys, traceback
import concurrent.futures

# Logging config

def init_logger(debug=False):
    if not os.path.isdir("logs"):
        os.mkdir("logs")

    script_name = os.path.basename(__file__)
    logpath = f"logs/{script_name}.log"
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(formatter)
    
    rotatingFileHandler = logging.handlers.TimedRotatingFileHandler(filename=logpath, when='midnight', backupCount=30)
    rotatingFileHandler.suffix = "%Y%m%d"
    rotatingFileHandler.setFormatter(formatter)

    handlers = [consoleHandler,rotatingFileHandler]
    
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level=log_level, handlers=handlers)

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
init_logger()
logger = logging.getLogger(__name__)
bot.logger = logger

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

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

"""
bot.apscheduler.add_job(
    change_client_presence,
    trigger="cron",
    minute="*/5",
    replace_existing=True,
    jobstore="default",
)
"""


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
    logger.info("Logged in as")
    logger.info(bot.user.name)
    logger.info(bot.user.id)
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

@bot.event
async def on_command_error(ctx, error):
    logger.error(f"Failed command: {ctx.message}")
    logger.error(f"{ctx.message.content}")
    tb_str = "".join(traceback.format_exception(etype=type(error), value=error, tb=error.__traceback__))
    logger.error(tb_str)

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
            logger.info(f"Loaded cogs {cogs_dir}.{extension}")
        except (discord.ClientException, ModuleNotFoundError) as e:
            logger.exception(f"Failed to load extension {extension}.")

    bot.run(API_KEY)
