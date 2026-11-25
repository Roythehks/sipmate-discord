import discord
from discord.ext import commands, tasks

from utils import BOT_STATUS

class TasksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_update_loop.start()

    def cog_unload(self):
        self.status_update_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("TasksCog is ready.")

    @tasks.loop(minutes=30)
    async def status_update_loop(self):
        """Keep the bot presence on the fixed custom status."""
        try:
            activity = discord.CustomActivity(name=BOT_STATUS)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            print(f"🔄 Status updated to: {BOT_STATUS}")
        except Exception as e:
            print(f"❌ Error updating status: {e}")

    @status_update_loop.before_loop
    async def before_status_update(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(TasksCog(bot))
