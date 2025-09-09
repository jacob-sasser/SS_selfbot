import discord
import asyncio
from discord.ext import commands,tasks
from typing import Optional
import random

TOKEN=''

class main_bot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channels=[]
        self.bots=[]
        self.inactive_bots=[]
        self.active_channels=[]
        self.human_role=None
        self.waiting_channel=None

    def get_role_members(role:discord.Role):
        return role.members


    @tasks.loop(seconds=2)
    async def get_inactive_bots(self,ctx,afk_channel:discord.VoiceChannel):
        '''
        Gets the current bots not watching a screenshare
        params: 
        afk_channel: the waiting channel for the bots
        bots: a list of discord.Members that have a bot role
        returns: list[discord.Member]
        '''
        bots_in_channel=afk_channel.members
        for bot in bots_in_channel:
            self.inactive_bots.append(bot)

    @tasks.loop(seconds=1)
    async def get_active_channels(self,ctx,channel_list:list[discord.VoiceChannel],bot_role:discord.Role,human_role:discord.Role):
        '''
        searches through the designated list of channels and returns the channels with a (non-bot) user and a bot-user in them

        '''
        
        for channel in channel_list:
            has_bot=False
            has_member=False
            members=channel.members
            for member in members:
                if bot_role in member.roles:
                    has_bot=True
                elif human_role in member.roles:
                    has_member=True
            if has_member and has_bot:
                self.active_channels.append(channel)
            
            

    @commands.command()
    async def init_category(self,ctx,category:discord.CategoryChannel):
        '''
        initializes every channel under a certain category
        
        '''
        for vc in category.voice_channels:
            self.channels.append(vc)
        return self.channels

    @commands.command()
    async def init_channel(self,ctx,vc:discord.VoiceChannel):
        '''
        init_channel
        initializes a new channel that people and bots will be joining
        params: channel_name
        '''
        self.channels.append(vc)
        return self.channels


    @commands.command()
    async def init_bot(self,ctx,bot:discord.Member,bot_role:discord.Role):
        '''
        initialized a new bot, giving them roles and server muting & deafning them
        potentially also gives them nickname IDK yet
        returns: void
        '''
        if(bot):
            await bot.edit(role=bot_role,mute=True,deafen=True)
            await ctx.send(f"Initialized {bot}")
            self.bots.append(bot)
            
        else:
            await ctx.send("User does not exist")

    
  
    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        """
        Whenever someone joins a watched channel:
        - If they have the human_role
        - Move a random inactive bot into the same channel
        """
        
        # Did the user join a channel?
        if after.channel in self.channels and self.human_role in member.roles:
            # Does the user have the target role?
            if not self.inactive_bots:
                    print(" No inactive bots available.")
                    return

            chosen_bot = random.choice(self.inactive_bots)
            try:
                await chosen_bot.move_to(after.channel)
                self.inactive_bots.remove(chosen_bot)
                print(f"Moved {chosen_bot.display_name} into {after.channel.name}")
            except discord.Forbidden:
                print(" Missing permissions to move the bot.")
            except discord.HTTPException as e:
                print(f"Failed to move bot: {e}")

    @commands.Cog.listener()
    async def on_voice_leave(self,member:discord.Member,before:discord.VoiceState,after:discord.VoiceState):\
            #need to add an actual self.waiting_channel, currently set to None
            if after.channel != before.channel and self.human_role in member.roles:
                for voice_member in after.channel.members:
                    if voice_member in self.bots:
                        await voice_member.edit(voice_channel=self.waiting_channel)



    @commands.command()
    async def watch(self,ctx,channel:discord.VoiceChannel,force: Optional[bool]): 
        if force and len(self.inactive_bots)==0:
            chosen_bot=random.choice(self.bots)
            await ctx.send(f"force moving bot to {channel.name}")
            await chosen_bot.edit(voice_channel=channel)
        elif len(self.inactive_bots==0):
            await ctx.send("no bots available")
            return
        else:
            chosen_bot=random.choice(self.inactive_bots)
        
            await chosen_bot.edit(voice_channel=channel)

    


        