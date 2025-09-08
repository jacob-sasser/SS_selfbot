import discord
import asyncio
from discord.ext import commands,tasks
from typing import Optional

class main_bot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    

    def get_role_members(role:discord.Role):
        return role.members


    @tasks.loop(seconds=10)
    async def get_inactive_bots(self,ctx,channel_list:list[discord.VoiceChannel],bots:list[discord.Member]):
        '''
        Gets the current bots not watching a screenshare
        params: 
        channel_list: A list of discord.VoiceChannels that will be searched through
        bots: a list of discord.Members that have a bot role
        returns: list[discord.Member]
        '''
        inactive_bots=[]
        for bot in bots:
            if not bot.voice or bot.voice.channel not in channel_list:
                inactive_bots.append(bot)
        return inactive_bots


    @commands.command()
    async def init_bot(self,ctx,bot:discord.Member):
        pass

    @commands.Cog.listener()
    def move_bot(self,ctx,bot:discord.Member,*,channel:discord.VoiceChannel):
        pass

    @commands.command()
    async def watch(self,ctx):
        pass