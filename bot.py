import os
from dotenv import load_dotenv

import json
import sqlite3
import db_helpers.db_functions as db

import discord

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN') or ""

with open('loc.json' , encoding='utf-8') as loc_data:
    loc = json.load(loc_data)

con = sqlite3.connect("storage.db")

intents = discord.Intents.default()
intents.guild_messages = True
intents.guild_reactions = True
intents.messages= True
intents.message_content= True
intents.members= True

bot = discord.Bot(intents=intents, activity=discord.Game("Watching reactions 🧐"))

podiums: dict[int, list[dict[str,int | None]]] = {}
podium_location: dict[int, discord.Message] = {}

# Helper
async def load_guild_in_memory(guild_id: int):
    podium: list[dict[str,int | None]] = []
    for place in db.get_guild_podium(guild_id):
        podium.append({"message_id": place[0], "channel_id": place[1], "reaction_nbr": place[2]})
    podiums[guild_id] = podium

    message_id, channel_id = db.get_guild_podium_location(guild_id) or (None, None)
    guild = bot.get_guild(guild_id)
    if not guild or not channel_id or not message_id:
        return
    
    channel = guild.get_channel(channel_id)
    if not channel or not isinstance(channel, discord.TextChannel):
        return
    
    podium_location[guild_id] = await channel.fetch_message(message_id)

async def fetch_message(guild_id: int, channel_id: int, message_id: int) -> discord.Message | None:
    guild = bot.get_guild(guild_id)
    if not guild:
        return
    
    channel = guild.get_channel(channel_id)
    if not channel or not isinstance(channel, discord.TextChannel):
        return
    
    message = await channel.fetch_message(message_id)

    return message

async def process_raw_reaction(reaction: discord.RawReactionActionEvent):
    if not reaction.guild_id: # Private message
        return
    
    message = await fetch_message(reaction.guild_id, reaction.channel_id, reaction.message_id)

    if not message:
        return
    
    if reaction.guild_id not in podiums:
        await load_guild_in_memory(reaction.guild_id)

    if not podiums[reaction.guild_id]:
        return
    
    await check_podium(reaction.guild_id, message)

    if podium_location[reaction.guild_id]:
        await update_podium_message(reaction.guild_id, podium_location[reaction.guild_id])

async def compute_unique_reactions(message: discord.Message) -> int:
    reacted: dict[int, bool] = {}
    for reaction in message.reactions:
        async for user in reaction.users():
            reacted[user.id] = True

    return len(reacted)

def save_all_podium(guild_id: int):
    db.save_guild_podium(guild_id, podiums[guild_id])

def save_podium_place(guild_id: int, message: discord.Message, rank: int, reaction_nbr: int):
    if rank >= len(podiums[guild_id]): #Not in podium
        return
    
    podiums[guild_id].insert(rank, {"message_id": message.id, "channel_id": message.channel.id, "reaction_nbr": reaction_nbr})
    podiums[guild_id].pop()

    for i in range(rank, len(podiums[guild_id])):
        place = podiums[guild_id][i]
        db.save_guild_podium_rank(guild_id, place["channel_id"], place["message_id"], i, place["reaction_nbr"])

async def check_podium(guild_id: int, message: discord.Message):
    reaction_nbr = await compute_unique_reactions(message)
    podium = podiums[guild_id]

    for place in podium:
        if place["message_id"] == message.id:
            if reaction_nbr == 0:
                place["message_id"], place["channel_id"], place["reaction_nbr"] = None, None, None
            else:
                place["reaction_nbr"] = reaction_nbr
            podium.sort(key=lambda place: place["reaction_nbr"] or 0, reverse=True)
            podiums[guild_id] = podium
            save_all_podium(guild_id)
            return
    
    for i in range(len(podium)-1,-1,-1):
        i_reaction_number =  podium[i]["reaction_nbr"]
        if i_reaction_number is None:
            continue
        if i_reaction_number >= reaction_nbr:
            save_podium_place(guild_id, message, i+1, reaction_nbr)
            return
    
    save_podium_place(guild_id, message, 0, reaction_nbr) 

async def create_podium_message(guild_id: int, channel_id: int, size: int) -> discord.Message | None:
    guild = bot.get_guild(guild_id)
    if not guild:
        return
    
    channel = guild.get_channel(channel_id)
    if not channel or not isinstance(channel, discord.TextChannel):
        return
    
    embed = discord.Embed(
        title=loc["podium"]["title"].get(guild.preferred_locale,loc["podium"]["title"]["en-US"]),
        description=loc["podium"]["description"].get(guild.preferred_locale,loc["podium"]["description"]["en-US"]),
        color=discord.Color.gold()
    )

    for i in range(1,size+1):
        name = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else str(i)
        embed.add_field(name=name,
                        value= loc["podium"]["empty"].get(guild.preferred_locale,loc["podium"]["empty"]["en-US"]))
    
    return await channel.send(embed=embed)

async def update_podium_message(guild_id: int, message: discord.Message):
    embed = message.embeds[0].to_dict()
    for i in range(len(podiums[guild_id])):
        place = podiums[guild_id][i]
        try:
            value = "No message"
            if  place["channel_id"] and  place["message_id"]:
                m = await fetch_message(guild_id, place["channel_id"], place["message_id"])
                if m:
                    value = m.content
            embed["fields"][i]["value"] = value
        except:
            pass

    embed = discord.Embed.from_dict(embed)
    await message.edit(embed=embed)
    


# Events
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_guild_remove(guild: discord.Guild):
    db.remove_guild(guild.id)

@bot.event
async def on_raw_reaction_add(reaction: discord.RawReactionActionEvent):
    await process_raw_reaction(reaction)

@bot.event
async def on_raw_reaction_remove(reaction: discord.RawReactionActionEvent):
    await process_raw_reaction(reaction)

# Commands
@bot.slash_command(name = "podium", description_localizations = loc["create_podium"]["description"])
@discord.option("size",name_localizations=loc["create_podium"]["option"]["name"],
                description_localizations=loc["create_podium"]["option"]["description"],
                min_value=1,max_value=10, default=3)
async def set_podium(ctx: discord.ApplicationContext, size: int):
    if not ctx.channel or not ctx.guild_id:
        return
    if isinstance(ctx.channel, discord.PartialMessageable):
        responses = loc["create_podium"]["channel_error"]
        await ctx.respond(responses.get(str(ctx.interaction.locale), responses["en-US"]))
        return
    
    await load_guild_in_memory(ctx.guild_id)
    if podiums[ctx.guild_id]:
        responses = loc["create_podium"]["already_exists"]
        actual_channel = podium_location[ctx.guild_id].channel
        if isinstance(actual_channel,discord.TextChannel):
            await ctx.respond(responses.get(str(ctx.interaction.locale), responses["en-US"])
                        .format(channel= actual_channel.mention))
        return


    db.add_guild(ctx.guild_id, size)
    message = await create_podium_message(ctx.guild_id, ctx.channel.id, size)
    if not message:
        return

    db.set_guild_podium_location(ctx.guild_id, ctx.channel.id, message.id)
    await load_guild_in_memory(ctx.guild_id)

    responses = loc["create_podium"]["success"]
    await ctx.respond(responses.get(str(ctx.interaction.locale), responses["en-US"])
                      .format(channel= ctx.channel.mention))


bot.run(TOKEN)