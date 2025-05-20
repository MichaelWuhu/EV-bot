from prizepicks import fetch_prizepicks_props
from sportsbooks.draftkings import fetch_draftkings_props

def setup_commands(bot):
    @bot.command()
    async def test(ctx):
        await ctx.send("test")

    @bot.command()
    async def props(ctx):
        props = await fetch_prizepicks_props()
        if not props:
            await ctx.send("No props found.")
            return

        msg = "\n".join([f"{player} — {stat}: {line}" for player, stat, line in props[:5]])
        await ctx.send(f"📊 PrizePicks NBA Props:\n{msg}")

    @bot.command()
    async def dk(ctx):
        print("running command ev!dk")    
        props = await fetch_draftkings_props(
            event_group_id=100009502,         # LoL Event Group ID
            stat_category="player-props",     # Broadest category for LoL props
            sport="LoL"
        )
        # await ctx.send(f"📊 DraftKings NBA Points Props:\n{props}")
        await ctx.send(f"aaaaaa")
