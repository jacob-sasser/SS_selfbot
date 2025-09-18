import discord
import asyncio
from discord.ext import commands,tasks
from typing import Optional
import random
import redis 
import json
import os
TOKEN='MTI4MTA0NDAwMTEwNDg1OTI3MA.Gt_89-.Okg2fErCJYRj36uylN8rAvLo12UeIJ0BEFG9Is'
SERVER_ID='1412870974524887042'
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
class main_bot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channels=[]
        self.bots=[]
        self.inactive_bots=[]
        self.active_channels=[]
        self.human_role=None
        self.waiting_channel=None
        self.guild_id=SERVER_ID

        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.get_inactive_bots.start()

    def get_role_members(role:discord.Role):
        return role.members

    

    @tasks.loop(seconds=2)
    async def get_inactive_bots(self):
        '''
        Gets the current bots not watching a screenshare
        params: 
        afk_channel: the waiting channel for the bots
        bots: a list of discord.Members that have a bot role
        returns: list[discord.Member]
        '''
        if not self.waiting_channel:
            print("no waiting channel")
            return
        
        bots_in_channel=self.waiting_channel.members
        
        self.inactive_bots = [bot for bot in bots_in_channel]


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
        await ctx.send(f'Initialzed channel {vc.name}')
        return self.channels

    @commands.command()
    async def set_waiting_channel(self,ctx,vc:discord.VoiceChannel):
        self.waiting_channel=vc
        await ctx.send(f"waiting channel is set to {vc.name}")

    @commands.command()
    async def init_bot(self,ctx,bot:discord.Member,bot_role:discord.Role):
        '''
        initialized a new bot, giving them roles and server muting & deafning them
        potentially also gives them nickname IDK yet
        returns: void
        '''
        
        await bot.add_roles(bot_role)
        await ctx.send(f"Initialized {bot}")
        self.bots.append({
                "discord": bot,          # discord.Member object
                "slave_id": f"{len(self.bots)+1}"  # or pulled from env/config
            })

            
        
    @commands.command()
    async def set_human_role(self,ctx,role:discord.Role):
        self.human_role=role
        await ctx.send(f"initialized human role {role.name}")
    
    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        """
        Detects when someone with human_role starts/stops a stream in a watched channel.
        - Start: move a bot + send "watch"
        - Stop: return bot + send "stop"
        """

        # Must be in a watched channel
        if not after.channel and not before.channel:
            return

        # Must have the human role
        if self.human_role not in member.roles:
            return

        # Streaming state changed
        if before.self_stream != after.self_stream:
            if after.self_stream:  # just started
                if not self.inactive_bots:
                    print("No inactive bots available.")
                    return

                chosen = random.choice(self.bots)
                chosen_bot = chosen["discord"]
                chosen_id = chosen["slave_id"]



                try:
                    await chosen_bot.move_to(after.channel)

                    # Tell the slave bot to start recording
                    self.r.rpush(f"tasks:{chosen_id}", json.dumps({"action": "click_channel",
                                                                   "server": after.channel.guild.name,
                                                                   "channel":after.channel.name
                                                                   }))

                    self.inactive_bots.remove(chosen_bot)
                    print(f"Moved {chosen_bot.display_name} into {after.channel.name}")
                except discord.Forbidden:
                    print("Missing permissions to move the bot.")
                except discord.HTTPException as e:
                    print(f"Failed to move bot: {e}")

            elif before.self_stream and not after.self_stream:  # just stopped
                # Find bots in the same channel
                for voice_member in before.channel.members:
                    if voice_member in self.bots:
                        try:
                            if self.waiting_channel:
                                await voice_member.move_to(self.waiting_channel)
                            # Tell the slave bot to stop recording
                            self.r.rpush(f"tasks:{voice_member['slave_id']}", json.dumps({"action": "record_stop"}))

                            self.inactive_bots.append(voice_member)
                            print(f"Moved {voice_member.display_name} back to waiting channel")
                        except discord.Forbidden:
                            print("Missing permissions to move the bot.")
                        except discord.HTTPException as e:
                            print(f"Failed to move bot: {e}")





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
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), description='test')

@bot.event
async def on_ready():
    print(f'logged in as {bot.user}')

async def setup(bot):
    await bot.add_cog(main_bot(bot))
    
    

async def main():
    await setup(bot)
    await bot.start(TOKEN)

asyncio.run(main())


        