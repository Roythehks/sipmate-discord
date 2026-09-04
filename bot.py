import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import os
from datetime import datetime, timezone
from utils import STATUS_MESSAGES # For the initial status set
import data_manager

# Try to load environment variables using python-dotenv
try:
    from dotenv import load_dotenv
    # Try to load from various possible env files
    env_files = ['config.env', '.env']
    loaded_env = False
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"✅ Loaded environment from {env_file}")
            loaded_env = True
            break
    
    if not loaded_env:
        print("⚠️ No env file found, trying default .env")
        load_dotenv()  # Try to load from default .env
except ImportError:
    print("⚠️ python-dotenv not installed, using manual loading")
    # Manual environment loading fallback
    if os.path.exists('config.env'):
        with open('config.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ Manually loaded config.env")

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Set up data files and load data
data_manager.setup_data_files()
bot.reminder_channels = data_manager.load_reminder_channels()
bot.user_reset_times = data_manager.load_user_reset_times()

@bot.event
async def on_ready():
    print(f'{bot.user} (SipMate) has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} servers')
    
    # Set initial bot status
    status_message = random.choice(STATUS_MESSAGES)
    try:
        activity = discord.Game(name=status_message)
        await bot.change_presence(status=discord.Status.online, activity=activity)
        print(f"✅ Initial status set to: Playing {status_message}")
    except Exception as e:
        print(f"❌ Error setting initial status: {e}")
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    
    # Auto-assign roles on startup
    for guild in bot.guilds:
        try:
            hydrated_role = discord.utils.get(guild.roles, name="💧 Hydrated")
            if hydrated_role and hydrated_role not in guild.me.roles:
                await guild.me.add_roles(hydrated_role, reason="SipMate bot auto-assignment on startup")
                print(f"✅ Auto-assigned '💧 Hydrated' role to bot in {guild.name}")
        except Exception as e:
            print(f"❌ Could not auto-assign role in {guild.name}: {e}")

@bot.event
async def on_guild_join(guild):
    """Create a hydration role when joining a new server"""
    try:
        light_blue = discord.Color(0x87CEEB)
        
        existing_role = discord.utils.get(guild.roles, name="💧 Hydrated")
        if existing_role:
            print(f"Role '💧 Hydrated' already exists in {guild.name}")
            if existing_role not in guild.me.roles:
                try:
                    await guild.me.add_roles(existing_role, reason="SipMate bot auto-assignment")
                    print(f"✅ Assigned existing '💧 Hydrated' role to bot in {guild.name}")
                except Exception as e:
                    print(f"❌ Could not assign existing role to bot in {guild.name}: {e}")
            return
        
        role = await guild.create_role(
            name="💧 Hydrated",
            color=light_blue,
            reason="SipMate hydration tracking role",
            mentionable=True
        )
        
        print(f"✅ Created '💧 Hydrated' role in {guild.name}")
        
        try:
            await guild.me.add_roles(role, reason="SipMate bot auto-assignment")
            print(f"✅ Assigned '💧 Hydrated' role to bot in {guild.name}")
        except Exception as e:
            print(f"❌ Could not assign role to bot in {guild.name}: {e}")
        
        channels = [ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages]
        
        if channels:
            welcome_channel = discord.utils.get(channels, name='general') or \
                              discord.utils.get(channels, name='welcome') or \
                              channels[0]
            
            embed = discord.Embed(
                title="💧 SipMate has joined the server!",
                description="🌊 Your personal hydration assistant! Track water intake, get reminders, see beautiful progress bars, and stay healthy. Custom schedules, automatic notifications, and personalized stats. Drink up! 💧",
                color=light_blue,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="🚀 Get Started", value="`/water` - Check your hydration progress\n`/reset` - Set your personal schedule\n`/help` - See all commands", inline=True)
            embed.add_field(name="🎯 Features", value="• Personal progress tracking\n• Beautiful progress bars\n• Custom daily schedules\n• Automatic reminders", inline=True)
            embed.add_field(name="🏷️ Role Created", value=f"I've created the {role.mention} role for hydration enthusiasts!\n✅ I've also assigned it to myself!", inline=False)
            embed.set_footer(text="SipMate • Your hydration companion")
            
            try:
                await welcome_channel.send(embed=embed)
                print(f"✅ Sent welcome message to #{welcome_channel.name} in {guild.name}")
            except Exception as e:
                print(f"❌ Could not send welcome message in {guild.name}: {e}")
                
    except Exception as e:
        print(f"❌ Error creating role in {guild.name}: {e}")

# Error handling for slash commands
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(f"Command error: {error}")
    
    if interaction.response.is_done():
        return
    
    try:
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(title="❌ Permission Error", description="You don't have permission to use this command.", color=0xFF6B6B)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, app_commands.CommandOnCooldown):
            embed = discord.Embed(title="⏰ Cooldown", description=f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.", color=0xFFFF00)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="❌ Error", description="An unexpected error occurred. Please try again later.", color=0xFF6B6B)
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"Error in error handler: {e}")

# Load cogs
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load cog {filename}: {e}")

# Main entry point
async def main():
    async with bot:
        await load_cogs()
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            print("❌ Error: DISCORD_BOT_TOKEN environment variable not found!")
            print("Please set your Discord bot token as an environment variable.")
            print("Example: set DISCORD_BOT_TOKEN=your_token_here")
        else:
            try:
                await bot.start(token)
            except discord.LoginFailure:
                print("❌ Error: Invalid Discord bot token!")
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n gracefully shutting down") 