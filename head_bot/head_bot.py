import discord
import asyncio
from discord.ext import commands,tasks
from typing import Optional
import random
import redis 
import json
import os
import time
import signal
import sys
import atexit

TOKEN='MTI4MTA0NDAwMTEwNDg1OTI3MA.Gt_89-.Okg2fErCJYRj36uylN8rAvLo12UeIJ0BEFG9Is'
SERVER_ID='170438817256308738'
REDIS_HOST = "localhost"
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))


class main_bot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channels=[]
        self.bots=[]
        self.inactive_bots=[]
        self.active_channels=set()
        self.human_role=None
        self.waiting_channel=None
        self.guild_id=SERVER_ID
        self.bot_role=None
        
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.get_inactive_bots.start()
        self.get_active_channels.start()
        self.check_voice_leaves.start()

    def get_role_members(role:discord.Role):
        return role.members

    def cleanup(self):
        print("[MASTER] Cleaning up Redis queues...")
        for bot in self.bots:
            slave_id = bot["user_id"]
            self.r.delete(f"tasks:{slave_id}")
            self.r.delete(f"acks:{slave_id}")
        print("[MASTER] Cleanup done.")

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
    async def get_active_channels(self):
        """
        Searches through the designated list of channels and updates
        self.active_channels with those that contain both:
        - at least one bot (bot_role)
        - at least one human (human_role)
        """

        active = []

        for channel in self.channels:
            members = channel.members
            has_bot = any(self.bot_role and self.bot_role.id in [r.id for r in m.roles] for m in members)
            has_human = any(self.human_role and self.human_role.id in [r.id for r in m.roles] for m in members)

            print(f"[DEBUG] Checking {channel.name} members: {[m.name for m in channel.members]}")
            if has_bot and has_human:
                active.append(channel)

        self.active_channels = active

        # Debugging
        if active:
            print("[MASTER] Active channels:", [c.name for c in active])
        else:
            print("[MASTER] No active channels")
                
                

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
    async def init_bot(self, ctx, bot: discord.Member, bot_role: discord.Role):
        """
        Initializes a new bot by using its Discord user ID as the unique identifier.
        """
        self.bot_role = bot_role
        await bot.add_roles(bot_role)

        user_id = str(bot.id)  

        
        if not self.r.exists(f"bot:{user_id}"):
            self.r.set(f"bot:{user_id}:discord_id", bot.id)
            await ctx.send(f"Initialized {bot} with ID {user_id}")
        else:
            await ctx.send(f"Reattached existing bot {bot} with ID {user_id}")

        # Add to local cache
        entry = {"discord": bot, "user_id": user_id}
        if entry not in self.bots:
            self.bots.append(entry)

        print(f"[MASTER] Registered {bot.name} with ID {user_id}")


    def load_bots(self, role: discord.Role):
        """
        Loads all members with the bot_role and registers them using their Discord user IDs.
        """
        for bot in role.members:
            user_id = str(bot.id)
            # Only add if not already in local cache
            if not any(b["user_id"] == user_id for b in self.bots):
                self.bots.append({"discord": bot, "user_id": user_id})
                print(f"[MASTER] Loaded bot {bot.name} with ID {user_id}")



        
    
    
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
        
        if after.channel == self.waiting_channel or before.channel==self.waiting_channel:
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
                chosen_id = chosen["user_id"]



                try:
                    await chosen_bot.move_to(after.channel)

                    # Tell the slave bot to start recording
                    self.r.rpush(f"tasks:{chosen_id}", json.dumps({"action": "click_channel",
                                                                   "server": after.channel.guild.name,
                                                                   "channel":after.channel.name
                                                                   }))
                    

                    self.inactive_bots.remove(chosen_bot)
                    try:
                        ack=self.r.blpop(f"acks{chosen_id}",timeout=10)
                        if ack:
                            print(f"[MASTER] Bot {chosen_id} acknowledged: {ack[1]}")
                        else: print(f"[MASTER] No ACK from bot {chosen_id}")

                    except Exception as e:
                        print(f"[MASTER] Error waiting for ack: {e}")

                    print(f"Moved {chosen_bot.display_name} into {after.channel.name}")
                except discord.Forbidden:
                    print("Missing permissions to move the bot.")
                except discord.HTTPException as e:
                    print(f"Failed to move bot: {e}")

    @tasks.loop(seconds=2)
    async def check_voice_leaves(self):

        """
        Periodically checks if any tracked voice channels in self.active_channels
        are now inactive, and moves all bots with self.bot_role back to waiting_channel.
        """

        before_channels = list(self.active_channels)
        await asyncio.sleep(1.1)
        after_channels = list(self.active_channels)

        for vc in self.channels:
            if len(vc.members)==1 and self.bot_role in vc.members[0].roles:
                member=vc.members[0]
                bot_entry = next(b for b in self.bots if b["discord"].id == member.id)
                slave_id = bot_entry["user_id"]
                self.r.rpush(
                                f"tasks:{slave_id}",
                                json.dumps({"action": "record_stop"})
                            )
                await member.move_to(self.waiting_channel)
                
        for before_vc in before_channels:
            if before_vc not in after_channels:
                print(f"[MASTER] {before_vc} is no longer active, returning bots...")

                for member in before_vc.members:
                    if self.bot_role in member.roles:
                        try:
                            if self.waiting_channel:
                                await member.move_to(self.waiting_channel)
                                print(f"[MASTER] Moved {member.display_name} to waiting channel")

                            # Always safe since every bot with bot_role is tracked in self.bots
                            bot_entry = next(b for b in self.bots if b["discord"].id == member.id)
                            slave_id = bot_entry["slave_id"]

                            # Tell slave to stop recording
                            self.r.rpush(
                                f"tasks:{slave_id}",
                                json.dumps({"action": "record_stop"})
                            )

                            if bot_entry not in self.inactive_bots:
                                self.inactive_bots.append(bot_entry)

                        except Exception as e:
                            print(f"[MASTER] Failed to move {member.display_name}: {e}")






    @commands.command()
    async def watch(self,ctx,channel:discord.VoiceChannel,force: Optional[bool]): 
        if force and len(self.inactive_bots)==0:
            chosen_bot=random.choice(self.bots)
            await ctx.send(f"force moving bot to {channel.name}")
            await chosen_bot.edit(voice_channel=channel)
        elif len(self.inactive_bots)==0:
            await ctx.send("no bots available")
            return
        else:
            chosen_bot=random.choice(self.inactive_bots)
        
            await chosen_bot.edit(voice_channel=channel)

owner_ids=[117475726260830213]


bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), description='test',owner_ids=owner_ids)

@bot.event
async def on_ready():
    print(f'logged in as {bot.user}')

async def setup_bot():
    cog = main_bot(bot)
    await bot.add_cog(cog)
    
    # Register cleanup before run loop
    atexit.register(cog.cleanup)
    return cog

async def main():
    await setup_bot()
    await bot.start(TOKEN)

if __name__ == "__main__":
    # Ensure signals exit cleanly
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))

    asyncio.run(main())


        