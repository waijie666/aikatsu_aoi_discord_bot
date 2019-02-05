from discord.ext import commands
import sys, traceback
from io import BytesIO
import discord
from PIL import Image
import asyncio
import aiohttp

class TestCog:
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
                filename = attachment.filename
                if filename.casefold().endswith("jpg") or filename.casefold().endswith("jpeg"):
                    format = "JPEG"
                elif filename.casefold().endswith("png"):
                    format = "PNG"
                elif filename.casefold().endswith("gif"):
                    format = "GIF"
                image = Image.open(file_object)
                width, height = image.size
                resized_image = image.resize((int(width*1.5),int(height*1.5)), Image.LANCZOS)
                file_object2 = BytesIO()
                resized_image.save(file_object2, format, optimize=True)
                file_object2.seek(0)
                discord_file = discord.File(file_object2, filename)
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
                

def setup(bot):
    bot.add_cog(TestCog(bot))
