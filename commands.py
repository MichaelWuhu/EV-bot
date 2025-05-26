import discord
from discord.ext import commands
from data.prizepicks import fetch_prizepicks_props
from data.golgg import get_player_id_from_name, fetch_player_last10_avg_from_golgg

def setup_commands(bot):
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
            player_id = get_player_id_from_name(player_name)
            stats = fetch_player_last10_avg_from_golgg(player_id)
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        print(f"(COMMANDS): Fetched stats for {player_name}: {stats}")

        embed = discord.Embed(
            title=f"📊 Last 10 Games — {player_name}",
            description="Based on Spring 2025 Split",
            color=0x2ecc71
        )
        embed.add_field(name="Avg Kills", value=str(stats['avg_kills']), inline=True)
        embed.add_field(name="Avg Assists", value=str(stats['avg_assists']), inline=True)
        embed.add_field(name="Winrate", value=f"{stats['winrate']}%", inline=True)

        await ctx.send(embed=embed)
