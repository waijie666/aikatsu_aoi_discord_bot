import discord
from discord.ext import commands
import random
import csv
from datetime import date, datetime, timedelta
import pytz
from collections import Counter
import asyncio
from os import listdir
from os.path import isfile, join
import concurrent.futures
import operator
import typing
from collections import defaultdict
import re

class LString:
    def __init__(self):
        self._total = 0
        self._successors = defaultdict(int)

    def put(self, word):
        self._successors[word] += 1
        self._total += 1

    def get_random(self):
        ran = random.randint(0, self._total - 1)
        for key, value in self._successors.items():
            if ran < value:
                return key
            else:
                ran -= value

class AikatsuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.airtime_datetime = None
        self.singing_already = False
        self.init_aikatsup()
        self.init_photokatsu()
        self.init_songs()
        self.init_aikatsu_idol()
        self.init_aikatsu_markov()
        try:
            self.init_aikatsu_stars_screenshots()
            self.init_aikatsu_screenshots()
        else:
            print("Screenshot initialization failed. Screenshots may not work in this environment")
        self.bot.process_executor = concurrent.futures.ProcessPoolExecutor(max_workers=3)

    def init_aikatsu_stars_screenshots(self):
        self.aistars_screenshot_dict = dict()
        
        with open("aistars_screenshot.txt","r") as f:
            fullstring = f.read()
            lines = fullstring.split("\n")
            for line in lines:
                episode_and_framenumber = line.split("screenshot")
                if len(episode_and_framenumber) < 2:
                    continue
                episode = str(int(episode_and_framenumber[0]))
                frame_number = int(episode_and_framenumber[1].split(".")[0])
                full_filename = "/screenshots/aistars/" + line
                if episode not in self.aistars_screenshot_dict:
                    self.aistars_screenshot_dict[episode] = list()
                self.aistars_screenshot_dict[episode].append({"full_filename":full_filename, "filename":line, "frame_number": frame_number})

    def init_aikatsu_screenshots(self):
        self.aikatsu_screenshot_dict = dict()

        with open("aikatsu_screenshot.txt","r") as f:
            fullstring = f.read()
            lines = fullstring.split("\n")
            for line in lines:
                episode_and_framenumber = line.split("screenshot")
                if len(episode_and_framenumber) < 2:
                    continue
                episode = str(int(episode_and_framenumber[0]))
                frame_number = int(episode_and_framenumber[1].split(".")[0])
                full_filename = "/backup/aikatsu_screenshot/" + line
                if episode not in self.aikatsu_screenshot_dict:
                    self.aikatsu_screenshot_dict[episode] = list()
                self.aikatsu_screenshot_dict[episode].append({"full_filename":full_filename, "filename":line, "frame_number": frame_number})

    def init_aikatsu_markov(self):
        self.couple_words = defaultdict(LString)
        self.uppercase_words_set = set()
        for file in [ "aikatsu_og_subs.txt", "aikatsu_stars_subs.txt" ] :
            with open(file, 'r') as f:
                for line in f:
                    self.add_message(line)

    def add_message(self, message):
        message = re.sub(r'\s[-\"]', '', message).strip()
        words_prefiltered = message.split()
        words = list()
        for word in words_prefiltered:
            try:
                float(word)
            except:
                words.append(word)
        if len(words) < 2:
            return
        for i in range(2, len(words)):
            self.couple_words[(words[i - 2], words[i - 1])].put(words[i])
            if words[i - 2][0].isupper():
                self.uppercase_words_set.add((words[i - 2], words[i - 1]))
        self.couple_words[(words[-2], words[-1])].put("")
        if words[-2][0].isupper():
            self.uppercase_words_set.add((words[-2], words[-1]))

    def init_aikatsu_idol(self):
        with open("aikatsu_idol.csv", "r") as csvfile:
            csvfile.readline()
            fieldnames = ["birthday","name","blood","height","school","type","series"]
            reader = csv.DictReader(csvfile, fieldnames=fieldnames)
            self.idol_dict_list = list(reader)
        self.bot.apscheduler.add_job(self.send_birthday_message, trigger="cron",minute="0",hour="0",replace_existing=True,id="birthday_post", jobstore="default")

    def init_songs(self):
        self.songs_dict = dict()
        songs_dir = "songs"
        for f in listdir(songs_dir):
            if isfile(join(songs_dir, f)) and "txt" in f:
                with open(join(songs_dir, f)) as songfile:
                    song_title = songfile.readline()
                    song_lyrics = songfile.read()
                    self.songs_dict[song_title] = song_lyrics

    def init_aikatsup(self):
        self.aikatsup_item_id = list()
        self.aikatsup_tags = list()
        self.cached_datetime = None

    def init_photokatsu(self):
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

    async def send_birthday_message(self):
        jp_timezone = pytz.timezone("Asia/Tokyo")
        current_time = datetime.now(jp_timezone)
        today = current_time.date()
        current_year = today.year

        for idol_dict in self.idol_dict_list:
            birthday_current_year = datetime.strptime(str(current_year) + idol_dict["birthday"],"%Y%B %d").date()
            if birthday_current_year < today :
                idol_dict["next_birthday"] = birthday_current_year.replace(year=current_year+1)
            else:
                idol_dict["next_birthday"] = birthday_current_year

        sorted_idol_dict_list = sorted(self.idol_dict_list, key=operator.itemgetter("next_birthday"))
        filtered_idol_dict_list  = [ idol_dict for idol_dict in sorted_idol_dict_list if idol_dict["next_birthday"] == today ]
        send_channel = self.bot.get_channel(326048564965015552)
        for idol_dict in filtered_idol_dict_list:
           await send_channel.send(f"Today **{idol_dict['birthday']}** is **{idol_dict['name']}**'s birthday :birthday: :birthday: :birthday:" )

    @staticmethod
    def chunks(l, n):
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
            subcommands_str_list = [ f"`{subcommands.name}`" for subcommands in ctx.command.walk_commands() ]
            await ctx.send("Invalid subcommands. Subcommands are " + " ".join(subcommands_str_list) )


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
            subcommands_str_list = [ f"`{subcommands.name}`" for subcommands in ctx.command.walk_commands() ]
            await ctx.send("Invalid subcommands. Subcommands are " + " ".join(subcommands_str_list) )

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

    @staticmethod
    def gacha_until_PR_worker(N_rate, PR_rate):
        gacha_rarity_list_try = list()
        gacha_rarity_dict = {"PR":0,"SR":0,"R":0}
        while "PR" not in gacha_rarity_list_try:
            gacha_rarity_list_try = random.choices(
                ["R", "SR", "PR"], [N_rate, 20, PR_rate]
            )
            gacha_rarity_dict[gacha_rarity_list_try[0]] += 1
        return gacha_rarity_dict
    
    @photokatsu.command()
    async def gacha_until_PR(self, ctx, rates: float = 2):
        if rates > 78:
            rates = 78
        elif rates < 0.00001:
            rates = 0.00001
        N_rate = 80 - rates
        PR_rate = rates
        async with ctx.typing():
            gacha_rarity_dict = await self.bot.loop.run_in_executor(self.bot.process_executor, self.gacha_until_PR_worker , N_rate, PR_rate)
        card_list = self.pick_cards(["PR"])
        rarity_counter = gacha_rarity_dict
        embed = discord.Embed(
            title="Photokatsu Gacha Results",
            description=f"Rates: PR {PR_rate}%, SR 20%, R {N_rate}%",
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

    @photokatsu.command()
    async def gacha_until(self, ctx, *, search_string):
        gacha_rarity_list_try = list()
        card_list = list()
        found = False
        gacha_rarity_dict = {"PR":0,"SR":0,"R":0} 
        search_count = 0
        await ctx.trigger_typing() 
        while found is False:
            search_count += 1 
            gacha_rarity_list_try = random.choices(
                ["R", "SR", "PR"], [78, 20, 2]
            )
            gacha_rarity_dict[gacha_rarity_list_try[0]] += 1
            card_list = self.pick_cards(gacha_rarity_list_try)
            if search_string.casefold() in card_list[0]["name"].casefold() :
                found = True
            if search_count > 200000:
                await ctx.send(search_string + " not found")
                return
        rarity_counter = gacha_rarity_dict
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
    async def next_birthday(self, ctx, days_or_string : typing.Union[int,str] = 30):
        jp_timezone = pytz.timezone("Asia/Tokyo")
        current_time = datetime.now(jp_timezone)
        today = current_time.date()
        current_year = today.year

        for idol_dict in self.idol_dict_list:
            birthday_current_year = datetime.strptime(str(current_year) + idol_dict["birthday"],"%Y%B %d").date()
            if birthday_current_year < today :
                idol_dict["next_birthday"] = birthday_current_year.replace(year=current_year+1)
            else:
                idol_dict["next_birthday"] = birthday_current_year

        sorted_idol_dict_list = sorted(self.idol_dict_list, key=operator.itemgetter("next_birthday"))
        if isinstance(days_or_string, int):
            filtered_idol_dict_list  = [ idol_dict for idol_dict in sorted_idol_dict_list if idol_dict["next_birthday"] < today + timedelta(days=days_or_string) ]
            embed = discord.Embed(title="Aikatsu Next Birthdays", description=f"Displaying next birthdays for the next {str(days_or_string)} days (max 25 idols)")
        elif isinstance(days_or_string, str):
            filtered_idol_dict_list  = [ idol_dict for idol_dict in sorted_idol_dict_list if days_or_string.casefold() in idol_dict["name"].casefold() ]
            embed = discord.Embed(title="Aikatsu Next Birthdays", description=f"Displaying next birthdays for search string: {str(days_or_string)} (max 25 idols)")
        for idol_dict in filtered_idol_dict_list:
            embed.add_field(name=idol_dict["name"], value=idol_dict["next_birthday"], inline=False)
        await ctx.send(embed=embed)


    @commands.command(hidden=True)
    @commands.is_owner()
    async def set_airtime(self, ctx, airtime: str):
        jp_timezone = pytz.timezone("Asia/Tokyo")
        self.airtime_datetime = datetime.fromisoformat(airtime + "+09:00").astimezone(
            jp_timezone
        )
    
    @commands.command()
    async def aikatsu_quote_generate(self, ctx, word_length : int = 15):
        if word_length > 200:
            word_length = 200
        if word_length < 5:
            word_length = 5
        final_result = []
        while len(final_result) < word_length :
            max_sentence_length = word_length - len(final_result)
            if max_sentence_length < 2 :
                max_sentence_length = 2
            if max_sentence_length > 15 :
                max_sentence_length = 15
            sentence_length = random.randint(2, max_sentence_length) 
            result = []
            while len(result) < sentence_length :
                result = []			
                s = random.choice(list(self.uppercase_words_set))
                result.extend(s)
                while result[-1] and len(result) < max_sentence_length + 50:
                    w = self.couple_words[(result[-2], result[-1])].get_random()
                    result.append(w)
            final_result.extend(result)
        await ctx.send(" ".join(final_result))

    async def detect_fall(self, message):
        if message.content.strip().casefold().startswith("!!!fall"):
           if self.falling is False:
               self.falling = True
               self.lastfallmessage = message
               
    @commands.command(
        description="Sings a random song. Use !!!fall to interrupt her singing"
    )
    async def singing(self, ctx):
        if self.singing_already is True:
            return
        else:
            self.singing_already = True
            self.falling = False
        song_name = random.choice([key for key, value in self.songs_dict.items()])
        full_song_string = self.songs_dict[song_name]
        song_string_list = full_song_string.splitlines()
        message = await ctx.send("Singing **" + song_name + "** \n")
        self.bot.add_listener(self.detect_fall, 'on_message')
        await asyncio.sleep(1)
        message_content = message.content
        for song_string in song_string_list:
            if self.falling is True:
                embed = discord.Embed()
                embed.set_image(url="https://i.imgur.com/sNqvjaE.png")
                await message.edit(content=message_content, embed=embed)
                await self.lastfallmessage.add_reaction(
                        self.bot.get_emoji(537234052080467968)
                )
                if random.choice([True, False]):
                    await asyncio.sleep(3)
                    await message.edit(content=message_content, embed=discord.Embed())
                    await self.lastfallmessage.add_reaction(
                        self.bot.get_emoji(485997782344138772)
                    )
                    self.falling = False
                else:
                    self.singing_already = False
                    return
            message_append_string = song_string.strip()
            if message_append_string == "":
                emoji = str(self.bot.get_emoji(537242527070158858))
                message_append_string = "\n" + (emoji + " ") * 5 + "\n"
            message_content = message_content + "\n" + message_append_string
            await message.edit(content=message_content)
            await asyncio.sleep(1)
        self.bot.remove_listener(self.detect_fall, 'on_message')
        embed = discord.Embed()
        embed.set_image(
            url="https://vignette.wikia.nocookie.net/aikatsu/images/f/f7/Dc161b80.jpg"
        )
        await message.edit(content=message_content, embed=embed)
        self.singing_already = False

    @singing.error
    async def singing_handler(self, ctx, error):
        self.singing_already = False
        print(error)
   
    @commands.command()
    async def aikatsu_stars_screenshot(self, ctx, episode: int=0):
        if episode == 0 or episode > 100:
            episode = str(random.randint(1,100))
        else:
            episode = str(episode)
        frame_number_index = random.randint(0, len(self.aistars_screenshot_dict[episode])-1)
        full_filename = self.aistars_screenshot_dict[episode][frame_number_index]["full_filename"] 
        filename = self.aistars_screenshot_dict[episode][frame_number_index]["filename"]
        embed = discord.Embed(title="Aikatsu Stars Screenshots")
        minutes, seconds = divmod(frame_number_index, 60)
        embed.add_field(name="Episode", value=episode)
        embed.add_field(name="Time", value=f"{minutes:02d}:{seconds:02d}")
        with open(full_filename, "rb") as f:
            jpg_data = f.read()
            discord_file = discord.File(jpg_data,filename)
            await ctx.send(file=discord_file)
            await ctx.send(embed=embed)

    @commands.command()
    async def aikatsu_screenshot(self, ctx, episode: int=0):
        if episode == 0 or episode > 178:
            episode = str(random.randint(1,178))
        else:
            episode = str(episode)
        frame_number_index = random.randint(0, len(self.aikatsu_screenshot_dict[episode])-1)
        full_filename = self.aikatsu_screenshot_dict[episode][frame_number_index]["full_filename"]
        filename = self.aikatsu_screenshot_dict[episode][frame_number_index]["filename"]
        embed = discord.Embed(title="Aikatsu Screenshots")
        minutes, seconds = divmod(frame_number_index*5, 60)
        embed.add_field(name="Episode", value=episode)
        embed.add_field(name="Time", value=f"{minutes:02d}:{seconds:02d}")
        with open(full_filename, "rb") as f:
            jpg_data = f.read()
            discord_file = discord.File(jpg_data,filename)
            await ctx.send(file=discord_file)
            await ctx.send(embed=embed)

# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case AikatsuCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(AikatsuCog(bot))

def teardown(bot):
    bot.process_executor.shutdown()
