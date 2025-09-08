import discord
import asyncio
from discord.ext import commands
from typing import Optional,Union
#DELETE LATER.
TEST_TOKEN="MTI4MTA0NDAwMTEwNDg1OTI3MA.GwWmCd.Ya1IfRH0Qe5DH8FZvRvwXZiv2bo1h0Qblcz-Lk" #Documents/TEST_TOKEN.txt
TEST_SERVER_ID=1412870974524887042


class test_bot(commands.Cog):
    def __init__(self,
                 bot,
                 testing_guild_id: Optional[int]=None):
        
        self.bot=bot
        self.testing_guild_id = testing_guild_id

        
    
    def get_guilds(self):
        return self.bot.guilds


    @commands.command()
    async def join(self,ctx,*,channel:discord.VoiceChannel):
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()
    
    @commands.command()
    async def leave(self,ctx):
        await ctx.voice_client.disconnect()
    
    
    @commands.command()
    async def move_to(self, ctx, member: discord.Member, *, channel: discord.VoiceChannel):
        
        try:
            await member.edit(voice_channel=channel)
            await ctx.send(f"✅ Moved {member.mention} to **{channel.name}**")
        except discord.Forbidden:
            await ctx.send("❌ I don’t have permission to move that member.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to move: {e}")
       



bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), description='test')
@bot.event
async def on_ready():
    print(f'logged in as {bot.user}')

async def setup(bot):
    await bot.add_cog(test_bot(bot, testing_guild_id=TEST_SERVER_ID))

async def main():
    await setup(bot)
    await bot.start(TEST_TOKEN)

asyncio.run(main())