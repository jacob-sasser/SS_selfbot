import discord
import asyncio
from discord.ext import commands,tasks
from typing import Optional

TOKEN=''

class main_bot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    

    def get_role_members(role:discord.Role):
        return role.members


    @tasks.loop(seconds=5)
    async def get_inactive_bots(self,ctx,afk_channel:discord.VoiceChannel):
        '''
        Gets the current bots not watching a screenshare
        params: 
        afk_channel: the waiting channel for the bots
        bots: a list of discord.Members that have a bot role
        returns: list[discord.Member]
        '''
        bots_in_channel=afk_channel.members
        return bots_in_channel

    @tasks.loop(seconds=1)
    async def get_active_channels(self,ctx,channel_list:list[discord.VoiceChannel],bot_role:discord.Role,human_role:discord.Role):
        '''
        searches through the designated list of channels and returns the channels with a (non-bot) user and a bot-user in them
        
        '''
        active_channel=[]
        
        for channel in channel_list:
            has_bot=False
            has_member=False
            members=channel.members
            for member in members:
                if bot_role in member.roles:
                    has_bot=True
                elif human_role in member.roles:
                    has_member=True
            if has_member == True & has_bot==True:
                active_channel.append(channel)
            
        return active_channel

        
        

    @commands.command()
    async def init_bot(self,ctx,bot:discord.Member,bot_role:discord.Role):
        '''
        initialized a new slave bot, giving them roles and server muting & deafning them
        potentially also gives them nickname IDK yet
        
        returns: void
        '''
        if(bot):
            bot.edit(role=bot_role,mute=True,deafen=True)
            ctx.send(f"Initialized {bot}")
            
        else:
            ctx.send("User does not exist")
        


    @commands.Cog.listener()
    def move_bot(self,ctx,bot:discord.Member,*,channel:discord.VoiceChannel):
        pass

    @commands.command()
    async def watch(self,ctx):
        pass