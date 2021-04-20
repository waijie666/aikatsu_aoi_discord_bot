# aikatsu_aoi_discord_bot

## Requirement
* Python 3.7

## Setup

### Installation
Install pipenv with pip or Homebrew.
```
$ pip install pipenv
or
$ brew install pipenv
```
Run pipenv.
```
$ pipenv install
```
And then, edit `.env` to set your app token and s3 object storage configuration(for screenshots0)
```
API_KEY={YOUR_APP_TOKEN}
s3_endpoint_url = 
s3_access_key = 
s3_secret_key = 
```
See: [Creating a discord bot & getting a token](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token)

### Run 
```
$ pipenv shell
$ python run.py
```

### Run Nohup & Background Mode
```
$ sh ./run.sh
```

## Usage

Basically we have two major functions `!!!aikatsup` and `!!!photokatsu` 
`!!!aikatsup` is for anime screenshots
`!!!photokatsu` is for photokatsu cards
The commands can only be used with subcommands.

For `!!!aikatsup`, as the website is in Japanese, most parameters can be used only in Japanese

**1.** `!!!aikatsup info` 
Obtain a list of valid tags from aikatsup.com

**2.** `!!!aikatsup random`
Get a random screenshot from aikatsup.com

**3.** `!!!aikatsup tag`
Get a random screenshot from aikatsup.com using the tag provided. For example: `!!!aikatsup tag 星宮いちご`

**4.** `!!!aikatsup subs`
Get a random screenshot from aikatsup.com using the subtitle provided. For example: `!!!aikatsup subs 暑い`

----------

For `!!!photokatsu`, the card info are sourced from Aikatsu Wikia

**1.** `!!!photokatsu id` 
Get photokatsu card info based on ID. For example: `!!!photokatsu id 1234`

**2.** `!!!photokatsu random`
Get a random photokatsu card. For example: `!!!photokatsu random`
This can be used to search for random cards of specific rarity or search term too.
To search for rarity. For example: `!!!photokatsu random PR+`  
To search for search term. For example: `!!!photokatsu random ichigo`
To search for rarity and search term. For example: `!!!photokatsu random SR yume` 

**3.** `!!!photokatsu gacha`
Perform a photokatsu gacha. Default is an eleven roll. For example: `!!!photokatsu gacha`
Performing a single roll is also possible. For example: `!!!photokatsu gacha one`
