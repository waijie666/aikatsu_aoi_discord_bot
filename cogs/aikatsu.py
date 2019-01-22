import discord
from discord.ext import commands
import random
import csv
from datetime import datetime, timedelta
import pytz
from collections import Counter
import asyncio

class AikatsuCog:
    def __init__(self, bot):
        self.bot = bot
        self.aikatsup_item_id = list()
        self.aikatsup_tags = list()
        self.cached_datetime = None
        self.airtime_datetime = None
        self.singing_already =False

        with open("photokatsu.csv", "r") as csvfile:
            fieldnames = [
                "rarity",
                "id",
                "name",
                "image_url",
                "appeal",
                "skill",
                "preawakened",
            ]
            reader = csv.DictReader(csvfile, fieldnames=fieldnames)
            self.card_dict_list = list(reader)

        self.PR_dict_list = list()
        self.PRplus_dict_list = list()
        self.PRplus_preawakened_dict_list = list()
        self.SR_dict_list = list()
        self.SRplus_dict_list = list()
        self.SRplus_preawakened_dict_list = list()
        self.R_dict_list = list()
        self.Rplus_dict_list = list()
        self.N_dict_list = list()
        self.Nplus_dict_list = list()

        for card_dict in self.card_dict_list:
            if card_dict["rarity"] == "PR":
                self.PR_dict_list.append(card_dict)
            elif card_dict["rarity"] == "PR+" and card_dict["preawakened"] == "yes":
                self.PRplus_preawakened_dict_list.append(card_dict)
            elif card_dict["rarity"] == "PR+":
                self.PRplus_dict_list.append(card_dict)
            elif card_dict["rarity"] == "SR":
                self.SR_dict_list.append(card_dict)
            elif card_dict["rarity"] == "SR+" and card_dict["preawakened"] == "yes":
                self.SRplus_preawakened_dict_list.append(card_dict)
            elif card_dict["rarity"] == "SR+":
                self.SRplus_dict_list.append(card_dict)
            elif card_dict["rarity"] == "R":
                self.R_dict_list.append(card_dict)
            elif card_dict["rarity"] == "R+":
                self.Rplus_dict_list.append(card_dict)
            elif card_dict["rarity"] == "N":
                self.N_dict_list.append(card_dict)
            elif card_dict["rarity"] == "N+":
                self.Nplus_dict_list.append(card_dict)

    def chunks(self, l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i : i + n]

    async def aikatsup_info_cache(self):
        if (
            self.cached_datetime is None
            or (self.cached_datetime + timedelta(hours=1)) < datetime.now()
        ):
            async with self.bot.clientsession.get(
                "http://aikatsup.com/api/v1/info"
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    if "item_id" in data:
                        self.aikatsup_item_id = data["item_id"]
                    if "tags" in data:
                        self.aikatsup_tags = data["tags"]
                    if "all_items" in data:
                        self.aikatsup_all_items = data["all_items"]
                    if ("item_id" in data) and ("tags" in data):
                        self.cached_datetime = datetime.now()

    async def aikatsup_image_embed(self, ctx, dict, type="Image"):
        embed = discord.Embed(title=type)
        embed.set_image(url=dict["image"]["url"])
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.add_field(name="Requester", value=ctx.author.mention)
        if "words" in dict:
            embed.add_field(name="Subs", value=dict["words"])
        if "tags" in dict:
            embed.add_field(name="Tags", value=dict["tags"])
        embed.set_footer(text="Provider: aikatsup.com")
        await ctx.send(embed=embed)

    @commands.group(case_insensitive=True)
    async def aikatsup(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "Invalid subcommands. Subcommands are `info` `subs` `tag` `random`."
            )

    @aikatsup.command()
    async def info(self, ctx):
        await self.aikatsup_info_cache()
        embed = discord.Embed(title="Info")
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.add_field(name="Requester", value=ctx.author.mention)
        embed.add_field(name="Image Count", value=self.aikatsup_all_items, inline=False)
        long_tag_chunk = list()
        for index, tag in enumerate(self.aikatsup_tags):
            if len(tag) > 16:
                long_tag = self.aikatsup_tags.pop(index)
                long_tag_chunk.append(long_tag)
        tag_chunks = self.chunks(self.aikatsup_tags, 50)
        tag_chunks = list(tag_chunks)
        tag_chunks.append(long_tag_chunk)
        for chunk in tag_chunks:
            chunkstring = "\n".join(chunk)
            embed.add_field(name="Available Tags", value=chunkstring)
        embed.set_footer(text="Provider: aikatsup.com")
        await ctx.send(embed=embed)

    @aikatsup.command()
    async def subs(self, ctx, *, subtitle: str = ""):
        if subtitle == "":
            await ctx.send("No parameters entered")
            return
        async with self.bot.clientsession.get(
            "http://aikatsup.com/api/v1/search?", params={"words": subtitle}
        ) as r:
            if r.status == 200:
                data = await r.json()
                if "item" in data:
                    total = len(data["item"])
                    post_no = random.randint(0, total - 1)
                    await self.aikatsup_image_embed(ctx, data["item"][post_no])
                else:
                    await ctx.send("見つからないよー＞＜")

    @aikatsup.command()
    async def tag(self, ctx, *, tagstr: str = ""):
        if tagstr == "":
            await ctx.send("No parameters entered")
            return
        await self.aikatsup_info_cache()
        if tagstr not in self.aikatsup_tags:
            await ctx.send("Tag does not exist")
            return
        async with self.bot.clientsession.get(
            "http://aikatsup.com/api/v1/search?", params={"tags": tagstr}
        ) as r:
            if r.status == 200:
                data = await r.json()
                if "item" in data:
                    total = len(data["item"])
                    post_no = random.randint(0, total - 1)
                    await self.aikatsup_image_embed(ctx, data["item"][post_no])
                else:
                    await ctx.send("見つからないよー＞＜")

    @aikatsup.command()
    async def random(self, ctx):
        await self.aikatsup_info_cache()
        total = len(self.aikatsup_item_id)
        post_no = random.randint(0, total - 1)
        id = self.aikatsup_item_id[post_no]
        async with self.bot.clientsession.get(
            "http://aikatsup.com/api/v1/search?", params={"id": id}
        ) as r:
            if r.status == 200:
                data = await r.json()
                if "item" in data:
                    await self.aikatsup_image_embed(ctx, data["item"])
                else:
                    await ctx.channel.send("見つからないよー＞＜")

    async def photokatsu_image_embed(self, ctx, dict, total=None, title="Photokatsu"):
        embed = discord.Embed(title=title)
        embed.set_image(url=dict["image_url"])
        embed.set_thumbnail(
            url="https://pbs.twimg.com/profile_images/980686341498290176/WSTxLywV_400x400.jpg"
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.add_field(name="Requester", value=ctx.author.mention)
        embed.add_field(name="ID", value=dict["id"])
        embed.add_field(name="Name", value=dict["name"])
        embed.add_field(name="Rarity", value=dict["rarity"])
        embed.add_field(name="Special Appeal", value=dict["appeal"])
        embed.add_field(name="Skill", value=dict["skill"])
        if total is not None:
            embed.add_field(name="Total search results", value=str(total))
        embed.set_footer(text="Provider: Aikatsu Wikia")
        await ctx.send(embed=embed)

    def pick_cards(self, gacha_rarity_list):
        card_list = list()
        for rarity in gacha_rarity_list:
            if rarity == "R":
                card_list.append(random.choice(self.R_dict_list))
            elif rarity == "SR":
                card_list.append(
                    random.choice(self.SR_dict_list + self.SRplus_preawakened_dict_list)
                )
            elif rarity == "PR":
                card_list.append(
                    random.choice(self.PR_dict_list + self.PRplus_preawakened_dict_list)
                )
        return card_list

    @commands.group(case_insensitive=True)
    async def photokatsu(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommands. Subcommands are `random` `id` `gacha`")

    @photokatsu.command(
        name="random",
        description="Default no parameters needed. Search examples: !!!photokatsu random ichigo, !!!photokatsu random pr, !!!photokatsu random pr+",
    )
    async def photokatsu_random(self, ctx, *, search_string=None):
        if search_string == None:
            result_dict_list = self.card_dict_list[1:]
        else:
            rarity = None
            search_string_1 = None
            tokens = search_string.split(maxsplit=1)
            for rarity_test in ["PR", "PR+", "SR", "SR+", "R", "R+", "N", "N+"]:
                if tokens[0].casefold() == rarity_test.casefold():
                    rarity = rarity_test
                    break
            if rarity is not None and len(tokens) > 1:
                search_string_1 = tokens[1]
            elif rarity is None:
                search_string_1 = search_string

            if rarity is not None:
                if rarity == "PR":
                    search_dict_list = self.PR_dict_list
                elif rarity == "PR+":
                    search_dict_list = (
                        self.PRplus_dict_list + self.PRplus_preawakened_dict_list
                    )
                elif rarity == "SR":
                    search_dict_list = self.SR_dict_list
                elif rarity == "SR+":
                    search_dict_list = (
                        self.SRplus_dict_list + self.SRplus_preawakened_dict_list
                    )
                elif rarity == "R":
                    search_dict_list = self.R_dict_list
                elif rarity == "R+":
                    search_dict_list = self.Rplus_dict_list
                elif rarity == "N":
                    search_dict_list = self.N_dict_list
                elif rarity == "N+":
                    search_dict_list = self.Nplus_dict_list
                if search_string_1 is None:
                    result_dict_list = search_dict_list
                else:
                    result_dict_list = list()
                    for search_dict in search_dict_list:
                        if search_string_1.casefold() in search_dict["name"].casefold():
                            result_dict_list.append(search_dict)
            else:
                result_dict_list = list()
                for search_dict in self.card_dict_list[1:]:
                    if search_string_1.casefold() in search_dict["name"].casefold():
                        result_dict_list.append(search_dict)

        total = len(result_dict_list)
        if total == 0:
            await ctx.send("Results do not exist")
            return
        post_no = random.randint(0, total - 1)
        await self.photokatsu_image_embed(ctx, result_dict_list[post_no], total)

    @photokatsu.command(name="id")
    async def photokatsu_id(self, ctx, id: int):
        if id < 1 or id > len(self.card_dict_list) - 1:
            await ctx.send(
                f"ID Out of range. Please input 1-{str(len(self.card_dict_list)-1)}"
            )
        else:
            await self.photokatsu_image_embed(ctx, self.card_dict_list[id])

    @photokatsu.command(
        name="gacha",
        description="Default is eleven rolls. !!!photokatsu gacha one for single rolls.",
    )
    async def photokatsu_gacha(self, ctx, number: str = "eleven"):
        if number == "one" or number == "1":
            gacha_rarity_list = random.choices(["R", "SR", "PR"], [78, 20, 2])
        elif number == "eleven" or number == "11":
            gacha_rarity_list = random.choices(["R", "SR", "PR"], [78, 20, 2], k=10)
            gacha_rarity_list += random.choices(["SR", "PR"], [98, 2])
        else:
            return
        card_list = self.pick_cards(gacha_rarity_list)
        rarity_counter = Counter(gacha_rarity_list)
        embed = discord.Embed(
            title="Photokatsu Gacha Results", description="Rates: PR 2%, SR 20%, R 78%"
        )
        embed.set_thumbnail(
            url="https://pbs.twimg.com/profile_images/980686341498290176/WSTxLywV_400x400.jpg"
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.add_field(name="Requester", value=ctx.author.mention)
        embed.add_field(name="Counter", value=dict(rarity_counter))
        card_string_list = list()
        for card in card_list:
            if card["rarity"].startswith("PR"):
                card_string_list.append(
                    f'**{int(card["id"]):04}. {card["rarity"]:<4} {card["name"]}**'
                )
            else:
                card_string_list.append(
                    f'{int(card["id"]):04}. {card["rarity"]:<4} {card["name"]}'
                )
        embed.add_field(name="Card List", value="\n".join(card_string_list))
        if number == "one" or number == "1":
            embed.set_image(url=card_list[0]["image_url"])
            embed.add_field(name="ID", value=card_list[0]["id"])
            embed.add_field(name="Name", value=card_list[0]["name"])
            embed.add_field(name="Rarity", value=card_list[0]["rarity"])
            embed.add_field(name="Special Appeal", value=card_list[0]["appeal"])
            embed.add_field(name="Skill", value=card_list[0]["skill"])
        embed.set_footer(text="")
        await ctx.send(embed=embed)

    @photokatsu.command()
    async def gacha_until_PR(self, ctx):
        gacha_rarity_list_try = list()
        gacha_rarity_list = list()
        while "PR" not in gacha_rarity_list_try:
            gacha_rarity_list_try = random.choices(["R", "SR", "PR"], [78, 20, 2])
            gacha_rarity_list += gacha_rarity_list_try
        card_list = self.pick_cards(gacha_rarity_list_try)
        rarity_counter = Counter(gacha_rarity_list)
        embed = discord.Embed(
            title="Photokatsu Gacha Results", description="Rates: PR 2%, SR 20%, R 78%"
        )
        embed.set_thumbnail(
            url="https://pbs.twimg.com/profile_images/980686341498290176/WSTxLywV_400x400.jpg"
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.add_field(name="Requester", value=ctx.author.mention)
        embed.add_field(name="Counter", value=dict(rarity_counter))
        card_string_list = list()
        for card in card_list:
            if card["rarity"].startswith("PR"):
                card_string_list.append(
                    f'**{int(card["id"]):04}. {card["rarity"]:<4} {card["name"]}**'
                )
            else:
                card_string_list.append(
                    f'{int(card["id"]):04}. {card["rarity"]:<4} {card["name"]}'
                )
        embed.add_field(name="Card List", value="\n".join(card_string_list))
        embed.set_image(url=card_list[0]["image_url"])
        embed.add_field(name="ID", value=card_list[0]["id"])
        embed.add_field(name="Name", value=card_list[0]["name"])
        embed.add_field(name="Rarity", value=card_list[0]["rarity"])
        embed.add_field(name="Special Appeal", value=card_list[0]["appeal"])
        embed.add_field(name="Skill", value=card_list[0]["skill"])
        embed.set_footer(text="")
        await ctx.send(embed=embed)

    @commands.command()
    async def next_episode(self, ctx):
        jp_timezone = pytz.timezone("Asia/Tokyo")
        first_week_aikatsu_2019 = datetime.fromisoformat(
            "2019-01-03 18:25+09:00"
        ).astimezone(jp_timezone)
        current_time = datetime.now(jp_timezone)
        next_aikatsu_datetime = first_week_aikatsu_2019
        airing = False

        if self.airtime_datetime is not None:
            if self.airtime_datetime > current_time:
                next_aikatsu_datetime = self.airtime_datetime

        while next_aikatsu_datetime < current_time:
            if self.airtime_datetime is not None and (
                current_time - self.airtime_datetime
            ) < timedelta(minutes=30):
                current_aikatsu_datetime = self.airtime_datetime
            else:
                current_aikatsu_datetime = next_aikatsu_datetime
            next_aikatsu_datetime += timedelta(weeks=1)
            if (current_time - current_aikatsu_datetime) < timedelta(minutes=30):
                airing = True

        embed = discord.Embed(
            title="Aikatsu Next Episode", timestamp=next_aikatsu_datetime
        )
        fmt = "%Y-%m-%d %H:%M:%S %Z%z"
        embed.add_field(
            name="Next episode time",
            value=next_aikatsu_datetime.strftime(fmt),
            inline=False,
        )
        embed.add_field(
            name="Time til next episode", value=next_aikatsu_datetime - current_time
        )
        embed.add_field(name="Airing now", value=airing)
        embed.set_footer(text="Local time")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def set_airtime(self, ctx, airtime: str):
        jp_timezone = pytz.timezone("Asia/Tokyo")
        self.airtime_datetime = datetime.fromisoformat(airtime + "+09:00").astimezone(
            jp_timezone
        )

    @commands.command()
    async def singing(self, ctx):
        if self.singing_already is True:
            return
        else:
            self.singing_already = True
        prism_spiral_string = """恋はShoot, shoot
                            たまにCute, cute
                            いつもLove you
                            
                            ミラクルをよりどりみどり
                            カッコつけた星たち　キラリ
                            キュンとしてる真昼の月と
                            マワル　踊る
                            
                            舞い上がるロマンス
                            旅立つ瞬間
                            いくつものキラキラを
                            散りばめてMy friend
                            光れ!
                            
                            I love you
                            I want you
                            I need you, かなり
                            たどりついた夢のほとり
                            口びるにメロディーと
                            魔法かけたまま　どこまでも…
                            いろとりどりのloop
                            描いてた
                            
                            恋はShoot, shoot
                            たまにCute, cute
                            いつもLove you"""
        song_string_list = prism_spiral.splitlines()
        message = await ctx.send(song_string_list[0].strip())
        await asyncio.sleep(1)
        message_content = message.content
        for song_string in song_string_list[1:]:
           message_content = message_content + '\n' + song_string.strip()
           await message.edit(content=message_content)
           await asyncio.sleep(1) 
        self.singing_already = False

# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case AikatsuCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(AikatsuCog(bot))
