import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from data_manager import save_reminder_channels

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='setchannel', description='Set the current channel for automatic water reminders (Admin only)')
    @app_commands.default_permissions(administrator=True)
    async def set_reminder_channel(self, interaction: discord.Interaction):
        """Set the current channel for automatic reminders"""
        try:
            self.bot.reminder_channels[str(interaction.guild.id)] = interaction.channel.id
            save_reminder_channels(self.bot.reminder_channels)
            embed = discord.Embed(
                title="✅ Channel Set!",
                description=f"Automatic water reminders will be sent to {interaction.channel.mention}",
                color=0x00FF00,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(
                name="⏰ Reminder Schedule",
                value="Automatic reminders every hour at :30 (UTC+8) with progress tracking!",
                inline=False
            )
            embed.set_footer(text="SipMate • Hydration Assistant")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"Error in setchannel: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred while setting the channel.", ephemeral=True)

    @app_commands.command(name='removechannel', description='Remove automatic water reminders from this server (Admin only)')
    @app_commands.default_permissions(administrator=True)
    async def remove_reminder_channel(self, interaction: discord.Interaction):
        """Remove automatic reminders for this server"""
        try:
            guild_id_str = str(interaction.guild.id)
            if guild_id_str in self.bot.reminder_channels:
                del self.bot.reminder_channels[guild_id_str]
                save_reminder_channels(self.bot.reminder_channels)
                embed = discord.Embed(
                    title="🚫 Reminders Disabled",
                    description="Automatic water reminders have been disabled for this server.",
                    color=0xFF6B6B,
                    timestamp=datetime.now(timezone.utc)
                )
            else:
                embed = discord.Embed(
                    title="❌ No Active Reminders",
                    description="This server doesn't have automatic reminders enabled.",
                    color=0xFF6B6B,
                    timestamp=datetime.now(timezone.utc)
                )
            embed.set_footer(text="SipMate • Hydration Assistant")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"Error in removechannel: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred while removing the channel.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot)) 