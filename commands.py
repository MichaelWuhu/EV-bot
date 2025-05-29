import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import asyncio

from data.prizepicks import fetch_prizepicks_props  
from data.golgg import get_player_id_from_name, fetch_player_last10_avg_from_golgg
from helpers.LoL.lolhelpers import score_lol_chance, calculate_lol_hit_rate

load_dotenv()
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID")
seen_props = set()
bot_instance = None 

def setup_commands(bot):
    global bot_instance
    bot_instance = bot

    @bot.event
    async def on_ready():
        global bot_instance
        bot_instance = bot

        if not monitor_prizepicks.is_running():
            monitor_prizepicks.start()

        print(f"✅ Logged in as {bot.user} | Monitor running...")

        guild_count = 0

        for guild in bot.guilds:
            print(f"- {guild.id} (name: {guild.name})")
            guild_count += 1

        print("Bot is in " + str(guild_count) + " servers")

    @bot.command()
    async def prizepicks(ctx):
        props = await fetch_prizepicks_props()
        if not props:
            await ctx.send("❌ No League of Legends props found.")
            return

        max_fields = 10
        pages = [props[i:i+max_fields] for i in range(0, len(props), max_fields)]

        embeds = []
        for i, page in enumerate(pages):
            embed = discord.Embed(
                title=f"📊 PrizePicks LoL Props — Page {i+1}/{len(pages)}",
                color=0x1e90ff
            )
            for prop in page:
                embed.add_field(
                    name=prop['player'],
                    value=f"{prop['stat']}: **{prop['line']}**",
                    inline=False
                )
            embeds.append(embed)

        # Send first page
        message = await ctx.send(embed=embeds[0])
        if len(embeds) == 1:
            return  # Only one page, no need for reactions

        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")

        def check(reaction, user):
            return (
                user == ctx.author
                and str(reaction.emoji) in ["⬅️", "➡️"]
                and reaction.message.id == message.id
            )

        current_page = 0
        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
                if str(reaction.emoji) == "➡️":
                    current_page = (current_page + 1) % len(embeds)
                elif str(reaction.emoji) == "⬅️":
                    current_page = (current_page - 1) % len(embeds)

                await message.edit(embed=embeds[current_page])
                await message.remove_reaction(reaction.emoji, user)
            except Exception:
                break  # Timeout or error — stop listening

    @bot.command()
    async def stats(ctx, *, player_name: str):
        await ctx.send(f"🔍 Fetching stats for **{player_name}**...")

        try:
            player_id = await get_player_id_from_name(player_name)
            stats = await fetch_player_last10_avg_from_golgg(player_id)
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        # print(f"(COMMANDS): Fetched stats for {player_name}: {stats}")

        embed = discord.Embed(
            title=f"📊 Last 10 Games — {player_name}",
            description="Based on Spring 2025 Split",
            color=0x2ecc71
        )
        embed.add_field(name="Avg Kills", value=str(stats['avg_kills']), inline=True)
        embed.add_field(name="Avg Assists", value=str(stats['avg_assists']), inline=True)
        # embed.add_field(name="Winrate", value=f"{stats['winrate']}%", inline=True)

        await ctx.send(embed=embed)

    @bot.command()
    async def ev(ctx, player: str, stat_type: str, line: float):
        await ctx.send(f"🔍 Fetching stats for **{player}**...")

        try:
            player_id = await get_player_id_from_name(player)
            stats = await fetch_player_last10_avg_from_golgg(player_id)
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        matches = stats["matches"]
        avg = stats[f"avg_{stat_type}"]
        hit_rate = calculate_lol_hit_rate(matches, stat=stat_type, line=line)
        score = score_lol_chance(avg, line, hit_rate)

        direction = "Over" if score >= 1 else "Under"
        difference = round(abs((2*avg) - line), 1)
        confidence = f"🔥 Confidence Score: {score}/2"

        color = 0x00ff99 if score == 2 else (0xffff00 if score == 1 else 0xff4444)
        embed = discord.Embed(
            title=f"{player} {line} Maps 1-2 {stat_type.title()}",
            description=(
                f"{player} has cleared this line {hit_rate}% of the time in the last 10,\n"
                f"They average {avg} Maps 1-2 {stat_type.title()}, which is {difference} {'more' if direction == 'Over' else 'less'} than the line.\n\n"
                f"{confidence}"
            ),
            color=color
        )

        embed.set_footer(text="EV Bot | Based on recent match data")
        await ctx.send(embed=embed)

@tasks.loop(seconds=10800)
async def monitor_prizepicks():
    await bot_instance.wait_until_ready()

    channel_id_str = DISCORD_CHANNEL_ID
    if not channel_id_str or not channel_id_str.isdigit():
        print("❌ DISCORD_CHANNEL_ID not set or invalid")
        return

    channel = bot_instance.get_channel(int(channel_id_str))
    if channel is None:
        print("❌ Could not find channel with ID")
        return

    try:
        props = await fetch_prizepicks_props()
    except Exception as e:
        print(f"❌ Error fetching props: {e}")
        return
    
    counter = 0

    for prop in props:
        key = f"{prop['player']}-{prop['stat']}-{prop['line']}"
        if key not in seen_props:
            seen_props.add(key)

            stat_type = prop["stat"].split()[2].lower() 

            print(f"📬 Sending EV embed for {prop['player']} {stat_type} {prop['line']}")
            await evaluate_and_send_ev(channel, prop["player"], stat_type, float(prop["line"]))
            await asyncio.sleep(1.5)

async def evaluate_and_send_ev(channel, player: str, stat_type: str, line: float):
    try:
        player_id = await get_player_id_from_name(player)
        stats = await fetch_player_last10_avg_from_golgg(player_id)
    except Exception as e:
        await channel.send(f"❌ Error evaluating {player} {stat_type}: {e}")
        return

    matches = stats["matches"]
    avg = stats.get(f"avg_{stat_type}")
    if avg is None:
        return  # Skip unknown stat types

    hit_rate = calculate_lol_hit_rate(matches, stat=stat_type, line=line)
    score = score_lol_chance(avg, line, hit_rate)

    # if score == 0:
        # return  # Too weak to post

    direction = "Over" if score >= 1 else "Under"
    difference = round(abs((2 * avg) - line), 1)
    confidence = f"🔥 Confidence Score: {score}/2"

    color = 0x00ff99 if score == 2 else (0xffff00 if score == 1 else 0xff4444)
    embed = discord.Embed(
        title=f"{player} {line} Maps 1-2 {stat_type.title()}",
        description=(
            f"{player} has cleared this line **{hit_rate}%** of the time in the last 10.\n"
            f"They average **{avg}** Maps 1-2 {stat_type.title()}, which is **{difference}** {'more' if direction == 'Over' else 'less'} than the line.\n\n"
            f"{confidence}"
        ),
        color=color
    )
    embed.set_footer(text="EV Bot | Based on recent match data")
    await channel.send(embed=embed)
    # await channel.send("test")
