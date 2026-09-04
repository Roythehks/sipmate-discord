import discord
from discord.ext import commands
from discord import app_commands, ui
from datetime import datetime, timezone
import random
from utils import (
    get_water_progress, create_progress_bar, get_status_emoji, WATER_REMINDERS,
    HYDRATION_TIPS, DAILY_GOAL_CUPS, DAILY_GOAL_ML, ML_PER_CUP
)
from data_manager import save_user_reset_times, log_user_progress

class WaterLogView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300) # 5-minute timeout
        self.user_id = user_id

    @ui.button(label="Log 1 Cup", style=discord.ButtonStyle.primary, emoji="💧")
    async def log_one_cup(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return

        total_cups = log_user_progress(self.user_id, 1)
        await interaction.response.send_message(f"💧 Great job! You've logged 1 cup. Your total today is {total_cups} cups!", ephemeral=True)

    @ui.button(label="Log 1 Glass (2 cups)", style=discord.ButtonStyle.secondary, emoji="🥤")
    async def log_two_cups(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
            
        total_cups = log_user_progress(self.user_id, 2)
        await interaction.response.send_message(f"🥤 Cheers! You've logged a glass ({2} cups). Your total today is {total_cups} cups!", ephemeral=True)

class MenuView(ui.View):
    def __init__(self, user_id, cog):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.cog = cog

    @ui.button(label="Check Progress", style=discord.ButtonStyle.primary, emoji="💧")
    async def check_progress_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await self.cog.water_reminder(interaction)

    @ui.button(label="Log Water", style=discord.ButtonStyle.success, emoji="📝")
    async def log_water_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
        await interaction.response.send_message("Use the `/log <cups>` command to log your water intake!", ephemeral=True)

    @ui.button(label="View Stats", style=discord.ButtonStyle.secondary, emoji="📊")
    async def view_stats_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await self.cog.hydration_stats(interaction)

    @ui.button(label="Get a Tip", style=discord.ButtonStyle.secondary, emoji="💡")
    async def get_tip_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await self.cog.hydration_tip(interaction)

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='log', description='Log your water intake.')
    @app_commands.describe(cups='How many cups of water you drank.')
    async def log(self, interaction: discord.Interaction, cups: app_commands.Range[int, 1, 20]):
        """Log water intake."""
        total_cups = log_user_progress(interaction.user.id, cups)
        
        embed = discord.Embed(
            title="💧 Water Logged!",
            description=f"You've successfully logged **{cups}** cups of water.",
            color=0x00BFFF,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Today's Total", value=f"You have now had **{total_cups}** cups today!")
        embed.set_footer(text="Keep it up! • SipMate")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='reset', description='Reset your daily hydration tracking to start fresh!')
    async def reset_hydration(self, interaction: discord.Interaction):
        """Reset user's daily hydration tracking"""
        user_id = str(interaction.user.id)
        reset_time = datetime.now()
        self.bot.user_reset_times[user_id] = reset_time
        save_user_reset_times(self.bot.user_reset_times)
        
        embed = discord.Embed(
            title="🔄 Hydration Reset Complete!",
            description="Your daily hydration tracking has been reset. Starting fresh!",
            color=0x00FF7F,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="🕐 Reset Time",
            value=f"{reset_time.strftime('%I:%M %p')} - Your personal day starts now!",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Daily Goal",
            value=f"**{DAILY_GOAL_CUPS} cups** ({DAILY_GOAL_ML}ml)",
            inline=True
        )
        
        embed.add_field(
            name="💡 How it works",
            value="Your progress will now be calculated from this reset time instead of midnight. Perfect for different schedules!",
            inline=False
        )
        
        embed.set_footer(text="Use /water to check your progress! • SipMate 💧")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='water', description='Get an instant water reminder with progress tracking!')
    async def water_reminder(self, interaction: discord.Interaction):
        """Send an immediate water reminder with progress"""
        cups_consumed, ml_consumed = get_water_progress(interaction.user.id)
        progress_bar, percentage = create_progress_bar(cups_consumed, DAILY_GOAL_CUPS)
        status_emoji = get_status_emoji(cups_consumed)
        
        embed = discord.Embed(
            title=f"{status_emoji} Time to Drink Water! {status_emoji}",
            description=random.choice(WATER_REMINDERS),
            color=0x00BFFF,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="🥤 Daily Progress",
            value=f"**{cups_consumed}/{DAILY_GOAL_CUPS} cups** of water!\n"
                  f"**{ml_consumed}ml/{DAILY_GOAL_ML}ml** finished!",
            inline=True
        )
        
        embed.add_field(
            name="📊 Progress Bar",
            value=f"{progress_bar}\n{percentage:.1f}% Complete",
            inline=True
        )
        
        if str(interaction.user.id) in self.bot.user_reset_times:
            reset_time = self.bot.user_reset_times[str(interaction.user.id)]
            time_diff = datetime.now() - reset_time
            hours_since_reset = min(time_diff.total_seconds() / 3600, 24.0)
            embed.add_field(
                name="🕐 Your Timeline",
                value=f"**{hours_since_reset:.1f} hours** since your reset at {reset_time.strftime('%I:%M %p')}",
                inline=False
            )
        else:
            embed.add_field(
                name="🕐 Default Timeline",
                value=f"Progress is tracked for the current day (since midnight). Use `/reset` for a custom schedule.",
                inline=False
            )
        
        if cups_consumed < DAILY_GOAL_CUPS:
            next_ml = (cups_consumed + 1) * ML_PER_CUP
            embed.add_field(
                name="🎯 Next Goal",
                value=f"Drink 1 more cup to reach {next_ml}ml!",
                inline=False
            )
        else:
            embed.add_field(
                name="🏆 Congratulations!",
                value="You've reached your daily hydration goal!",
                inline=False
            )
        
        embed.set_footer(text="Stay hydrated! Drink up! • SipMate 💧")
        view = WaterLogView(interaction.user.id)
        
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name='tip', description='Get a hydration tip!')
    async def hydration_tip(self, interaction: discord.Interaction):
        """Send a random hydration tip"""
        tip = random.choice(HYDRATION_TIPS)
        embed = discord.Embed(
            title="🌊 Hydration Tip",
            description=tip,
            color=0x00CED1,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="💧 Daily Goal Reminder",
            value=f"Aim for **{DAILY_GOAL_CUPS} cups** ({DAILY_GOAL_ML}ml) per day!",
            inline=False
        )
        
        embed.set_footer(text="Knowledge is power! • SipMate 🧠💪")
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name='hydrate', description='Remind someone to drink water!')
    @app_commands.describe(user='The user to remind about drinking water')
    async def hydrate_user(self, interaction: discord.Interaction, user: discord.Member):
        """Remind a specific user to drink water"""
        cups_consumed, ml_consumed = get_water_progress(user.id)
        progress_bar, percentage = create_progress_bar(cups_consumed, DAILY_GOAL_CUPS)
        status_emoji = get_status_emoji(cups_consumed)
        
        embed = discord.Embed(
            title=f"💧 Personal Hydration Reminder {status_emoji}",
            description=f"{user.mention} {random.choice(WATER_REMINDERS)}",
            color=0x1E90FF,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name=f"🥤 {user.display_name}'s Progress",
            value=f"**{cups_consumed}/{DAILY_GOAL_CUPS} cups** completed!\n"
                  f"**{ml_consumed}ml/{DAILY_GOAL_ML}ml** finished!\n"
                  f"{progress_bar} {percentage:.1f}%",
            inline=False
        )
        
        embed.set_footer(text=f"Reminder sent by {interaction.user.display_name} • SipMate 💙")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='stats', description='Show your detailed hydration stats!')
    async def hydration_stats(self, interaction: discord.Interaction):
        """Show detailed hydration stats with progress tracking"""
        cups_consumed, ml_consumed = get_water_progress(interaction.user.id)
        progress_bar, percentage = create_progress_bar(cups_consumed, DAILY_GOAL_CUPS)
        status_emoji = get_status_emoji(cups_consumed)
        
        embed = discord.Embed(
            title=f"💧 {interaction.user.display_name}'s Hydration Dashboard {status_emoji}",
            color=0x00BFFF,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="🥤 Cups Progress",
            value=f"**{cups_consumed}/{DAILY_GOAL_CUPS} cups**\n{ML_PER_CUP}ml per cup",
            inline=True
        )
        
        embed.add_field(
            name="💧 Volume Progress", 
            value=f"**{ml_consumed}ml/{DAILY_GOAL_ML}ml**\n{percentage:.1f}% Complete",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Status",
            value="🏆 Goal Achieved!" if cups_consumed >= DAILY_GOAL_CUPS else f"Keep going! {DAILY_GOAL_CUPS - cups_consumed} cups to go!",
            inline=True
        )
        
        embed.add_field(
            name="📊 Visual Progress",
            value=f"{progress_bar}\n{percentage:.1f}% of daily goal",
            inline=False
        )
        
        if str(interaction.user.id) in self.bot.user_reset_times:
            reset_time = self.bot.user_reset_times[str(interaction.user.id)]
            time_diff = datetime.now() - reset_time
            hours_since_reset = min(time_diff.total_seconds() / 3600, 24.0)
            embed.add_field(
                name="🕐 Your Personal Timeline",
                value=f"**{hours_since_reset:.1f} hours** since your reset at {reset_time.strftime('%I:%M %p')}\n"
                      f"Reset date: {reset_time.strftime('%Y-%m-%d')}",
                inline=False
            )
        else:
            embed.add_field(
                name="🕐 Default Timeline",
                value="Progress is tracked for the current day (since midnight).\n"
                      f"💡 Use `/reset` to set a custom schedule!",
                inline=False
            )
        
        if cups_consumed < DAILY_GOAL_CUPS:
            remaining_cups = DAILY_GOAL_CUPS - cups_consumed
            remaining_ml = remaining_cups * ML_PER_CUP
            embed.add_field(
                name="🔄 Remaining Today",
                value=f"**{remaining_cups} cups** ({remaining_ml}ml) left to reach your goal!",
                inline=False
            )
        
        embed.add_field(
            name="💪 Health Benefits",
            value="✨ Better skin • 🧠 Improved focus • 💪 Better performance • 🫀 Heart health",
            inline=False
        )
        
        embed.set_footer(text="Keep up the excellent work! Every sip counts! • SipMate 💙")
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name='help', description='Show all hydration bot commands')
    async def help_hydration(self, interaction: discord.Interaction):
        """Custom help command for hydration features"""
        embed = discord.Embed(
            title="💧 SipMate Commands",
            description="🌊 Your personal hydration assistant! Track water intake, get reminders, see beautiful progress bars, and stay healthy. Custom schedules, automatic notifications, and personalized stats. Drink up! 💧",
            color=0x00BFFF,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="🚰 Basic Commands",
            value="`/water` - Get instant water reminder with progress\n"
                  "`/log <cups>` - Log how many cups of water you drank\n"
                  "`/tip` - Get a hydration tip\n"
                  "`/hydrate @user` - Remind someone to drink water\n"
                  "`/stats` - View detailed hydration dashboard\n"
                  "`/reset` - Reset your daily progress timeline\n"
                  "`/invite` - Get invite link to add bot to other servers\n"
                  "`/support` - Get help and support information\n"
                  "`/menu` - Show the interactive command menu",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Admin Commands",
            value="`/setchannel` - Set channel for auto reminders\n"
                  "`/removechannel` - Disable auto reminders",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Daily Goal",
            value=f"**{DAILY_GOAL_CUPS} cups** ({DAILY_GOAL_ML}ml) per day\n"
                  f"**{ML_PER_CUP}ml** per cup",
            inline=True
        )
        
        embed.add_field(
            name="ℹ️ Features",
            value="• Progress tracking in cups & ml\n"
                  "• Visual progress bars\n"
                  "• Personal timeline with `/reset`\n"
                  "• Auto reminders every hour at :30\n"
                  "• Personalized stats",
            inline=True
        )
        
        embed.set_footer(text="SipMate • Made with 💧 • Stay healthy!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='invite', description='Get an invite link to add SipMate to another server!')
    async def invite_bot(self, interaction: discord.Interaction):
        """Generate an invite link for the bot with proper permissions"""
        
        permissions = 2416279554
        client_id = self.bot.user.id
        
        invite_url = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&permissions={permissions}&scope=bot%20applications.commands"
        install_url = f"https://discord.com/oauth2/authorize?client_id={client_id}"
        
        embed = discord.Embed(
            title="🤖 Invite SipMate to Your Server!",
            description="Choose your preferred method to add SipMate to another Discord server!",
            color=0x00BFFF,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="🔗 Official Discord Install (Recommended)",
            value=f"[**Add to Server**]({install_url})\n*Uses default permissions from Discord Developer Portal*",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Manual Invite Link",
            value=f"[**Custom Install**]({invite_url})\n*Manually specified permissions*",
            inline=False
        )
        
        embed.add_field(
            name="✅ Required Permissions",
            value="• Send Messages\n• Manage Roles (for 💧 Hydrated role)\n• Use Slash Commands\n• Embed Links\n• Read Message History\n• Add Reactions\n• View Channels\n• Mention Everyone",
            inline=False
        )
        
        embed.add_field(
            name="🎯 What SipMate Does",
            value="• Hydration tracking & reminders\n• Beautiful progress bars\n• Custom daily schedules\n• Automatic role management\n• Health tips & motivation",
            inline=False
        )
        
        embed.set_footer(text="SipMate • Spread the hydration love! 💧")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='support', description='Get help and support for SipMate!')
    async def support_command(self, interaction: discord.Interaction):
        """Provide support information and links"""
        
        embed = discord.Embed(
            title="🛠️ SipMate Support & Help",
            description="Need help with SipMate? We're here to assist you with hydration tracking!",
            color=0x00BFFF,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="🏠 Official Support Server",
            value="[**Join SipMate Support**](https://discord.gg/YOUR-INVITE-CODE)\n*Get help, report bugs, and suggest features!*",
            inline=False
        )
        
        embed.add_field(
            name="📋 Quick Help",
            value="`/help` - View all commands\n"
                  "`/water` - Check hydration progress\n"
                  "`/reset` - Set personal schedule\n"
                  "`/stats` - View detailed stats\n"
                  "`/tip` - Get hydration tips",
            inline=True
        )
        
        embed.add_field(
            name="🐛 Common Issues",
            value="• **Permissions**: Make sure bot can send messages\n"
                  "• **Slash Commands**: May take time to sync\n"
                  "• **Progress**: Use `/reset` for custom schedule\n"
                  "• **Reminders**: Admin can set with `/setchannel`",
            inline=True
        )
        
        embed.add_field(
            name="🔗 Quick Links",
            value=f"• [Add to Server](https://discord.com/oauth2/authorize?client_id={self.bot.user.id})\n"
                  "• [Support Server](https://discord.gg/YOUR-INVITE-CODE)\n"
                  "• [Terms of Service](YOUR-TOS-LINK)\n"
                  "• [Privacy Policy](YOUR-PRIVACY-LINK)\n"
                  "• [Bot Commands](/help)",
            inline=False
        )
        
        embed.add_field(
            name="💡 Tips",
            value="✨ Set up auto-reminders with `/setchannel`\n"
                  "🎯 Track progress with `/water` and `/stats`\n"
                  "🔄 Use `/reset` to match your schedule\n"
                  "💧 Remind friends with `/hydrate @user`",
            inline=False
        )
        
        embed.set_footer(text="SipMate Support • We're here to help! 💙")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='menu', description='Displays an interactive menu of commands.')
    async def menu(self, interaction: discord.Interaction):
        """Displays an interactive menu."""
        embed = discord.Embed(
            title="💧 SipMate Command Menu",
            description="Welcome to your hydration assistant! Here are the main commands you can use. Click the buttons below for quick access.",
            color=0x00BFFF,
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(
            name="`/water` - 💧 Check Progress",
            value="Get an instant summary of your daily water intake, including a progress bar and how much you have left to drink.",
            inline=False
        )
        embed.add_field(
            name="`/log <cups>` - 📝 Log Water",
            value="Record the amount of water you've drunk. You can log any number of cups to keep your progress updated.",
            inline=False
        )
        embed.add_field(
            name="`/stats` - 📊 View Stats",
            value="See a detailed dashboard of your hydration statistics, including your progress, personal timeline, and health benefits.",
            inline=False
        )
        embed.add_field(
            name="`/tip` - 💡 Get a Tip",
            value="Receive a random, helpful tip about staying hydrated and healthy.",
            inline=False
        )
        embed.add_field(
            name="`/reset` - 🔄 Reset Timeline",
            value="Start a new day of tracking at any time. This is perfect if your schedule doesn't follow a standard midnight-to-midnight day.",
            inline=False
        )

        embed.set_footer(text="SipMate • Your hydration companion")
        view = MenuView(interaction.user.id, self)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot)) 