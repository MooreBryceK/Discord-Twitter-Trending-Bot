from datetime import datetime
from discord.ext import commands, tasks
import auth
import discord
import json
import tweepy
import woe

global ctx
global location
global woe_id

NAME = 'TestApp v1'
COMMAND_PREFIXES = ['tb ', 'tB ', 'Tb ', 'TB ']
CLEAR_COMMAND_ALIASES = ['clear', 'erase']
TREND_COMMAND_ALIASES = ['trend', 'trends', 'trending']
STOP_COMMAND_ALIASES = ['stop', 'break']

client = commands.Bot(command_prefix=COMMAND_PREFIXES, case_insensitive=True)
client.remove_command('help')


# Notifies user that the discord bot is online
@client.event
async def on_ready():
    print(f'{NAME} online')


# Clear a specified amount of messages from a channel
@client.command(aliases=CLEAR_COMMAND_ALIASES)
async def _clear(context, amount=5):
    await context.channel.purge(limit=amount)


# Custom help command
@client.command(aliases=['help', 'about'])
async def _help(context):
    embed = discord.Embed(
        title=f"{NAME} Help Menu",
        color=discord.Colour.orange()
    )
    embed.add_field(
        name='clear',
        value="Removes unwanted messages from the channel\n`tb clear <number of posts>`",
        inline=False
    )
    embed.add_field(name='help', value="Guide to use this bot\n`tb help`", inline=False)
    embed.add_field(
        name='trend',
        value="Displays trending hashtags from twitter api automatically\n"
              + "The amount of seconds specified will be the time between posts\n"
              + "`tb trend <location> <seconds>`\n\n"
              + "If the name of a city is in multiple countries or is the\n"
              + "same name as the country it is located in, try adding a hyphen\n"
              + "and the country's abbreviated name after the city's name\n"
              + "`tb trend barcelona_es 60`\n"
              + "`tb trend barcelona_ve 60`\n",
        inline=False
    )
    embed.add_field(name='stop', value="Stops automatic posting\n`tb stop`", inline=False)
    embed.set_footer(text=f"Created by: Leon De Montana")
    await context.send(embed=embed)


# Posts top 10 trending twitter hashtags for a specified location
@client.command(aliases=TREND_COMMAND_ALIASES)
async def _trend(context, *, option='United States 60'):
    try:
        global ctx
        global location
        global woe_id
        ctx = context
        options = option.lower().split(' ')
        location = '_'.join(options[:-1])
        get_woe_id_from_location(location)
        post_trending.change_interval(seconds=int(options[-1]))
        post_trending.start()
    except Exception as e:
        await context.send('Something went wrong. Check your command and try again.')


# Runs a background task that posts trending data at a specified time interval
@tasks.loop(seconds=10)
async def post_trending():
    global ctx
    global location
    trending = get_trending_twitter_data()
    embed = create_trend_embed(location.replace('_', ' ').title(), trending)
    await ctx.send(embed=embed)


# Stops the breaks the trend command's while loop
@client.command(aliases=STOP_COMMAND_ALIASES)
async def _stop(context):
    post_trending.cancel()
    await context.send(f'{NAME} will discontinue automatic posting')


# Returns top ten trending hashtags with urls using the twitter api
def get_trending_twitter_data():
    global woe_id
    oauth = tweepy.OAuthHandler(auth.TWITTER_API_KEY, auth.TWITTER_API_SECRET_KEY)
    oauth.set_access_token(auth.TWITTER_ACCESS_TOKEN, auth.TWITTER_ACCESS_TOKEN_SECRET)
    api = tweepy.API(oauth)

    woe_trends = api.trends_place(woe_id)
    trends = json.loads(json.dumps(woe_trends, indent=1))
    top_ten_list = trends[0]['trends'][:10]

    post = ''
    for hashtag in top_ten_list:
        post += f"[{hashtag['name']}]({hashtag['url']})\n"

    return post


# Returns a where on earth (woe) id for a specified location
def get_woe_id_from_location(loc):
    global woe_id
    loc = loc.lower().replace(' ', '_')
    woe_id = woe.IDS['united_states']

    if loc in woe.IDS:
        woe_id = woe.IDS[loc]


# Creates discord embed message to be sent
def create_trend_embed(country, post):
    global woe_id
    dt = datetime.now().strftime('%Y-%m-%d %I:%M %p').split(' ')
    embed = discord.Embed(
        title=f"Trends For {country}",
        description=post,
        color=discord.Colour.orange()
    )
    embed.set_footer(text=f"WOEID: {woe_id} • {dt[0]} at {dt[1]} {dt[2]}")
    return embed


client.run(auth.DISCORD_TOKEN)