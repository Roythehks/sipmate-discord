import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, time, timedelta

REMINDER_TZ = timezone(timedelta(hours=8))
REMINDER_TIMES = [time(hour=h, minute=30, tzinfo=REMINDER_TZ) for h in range(24)]
import random
from utils import WATER_REMINDERS, DAILY_GOAL_CUPS, DAILY_GOAL_ML, STATUS_MESSAGES
from cogs.commands import WaterLogView

class TasksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.water_reminder_loop.start()
        self.status_update_loop.start()

    def cog_unload(self):
        self.water_reminder_loop.cancel()
        self.status_update_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("TasksCog is ready.")

    @tasks.loop(time=REMINDER_TIMES)
    async def water_reminder_loop(self):
        """Send automatic water reminders at :30 past every hour (UTC+8)"""
        for guild_id, channel_id in self.bot.reminder_channels.items():
            try:
                guild = self.bot.get_guild(int(guild_id))
                if not guild:
                    continue
                
                channel = self.bot.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title="⏰ Automatic Hydration Reminder 💧",
                        description=random.choice(WATER_REMINDERS),
                        color=0x00BFFF,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    embed.set_footer(text="Automatic reminder • SipMate 💙")
                    # We can't know which user this is for, so we can't personalize the view.
                    # A better approach might be to DM users who opt-in.
                    # For a channel-based reminder, we can't instantiate the view with a user_id.
                    # A simple message is better here.
                    await channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending reminder to guild {guild_id}: {e}")

    @water_reminder_loop.before_loop
    async def before_water_reminder(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=30)
    async def status_update_loop(self):
        """Update bot status with different water-themed messages"""
        try:
            status_message = random.choice(STATUS_MESSAGES)
            activity = discord.Game(name=status_message)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            print(f"🔄 Status updated to: Playing {status_message}")
        except Exception as e:
            print(f"❌ Error updating status: {e}")
            try:
                activity = discord.Activity(type=discord.ActivityType.custom, name=status_message)
                await self.bot.change_presence(activity=activity)
                print(f"🔄 Fallback status updated to: {status_message}")
            except Exception as e2:
                print(f"❌ Error updating fallback status: {e2}")

    @status_update_loop.before_loop
    async def before_status_update(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(TasksCog(bot)) 