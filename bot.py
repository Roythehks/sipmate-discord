import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from utils import BOT_DESCRIPTION, BOT_DISPLAY_NAME, BOT_STATUS
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
intents.reactions = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Set up data files and load data
data_manager.setup_data_files()
bot.mimic_emojis = data_manager.load_mimic_emojis()

async def apply_bot_profile():
    """Set the Discord display name, application description, and custom status."""
    if bot.user is not None and bot.user.name != BOT_DISPLAY_NAME:
        try:
            await bot.user.edit(username=BOT_DISPLAY_NAME)
            print(f"✅ Bot name set to: {BOT_DISPLAY_NAME}")
        except discord.HTTPException as e:
            print(f"❌ Could not set bot username: {e}")
            try:
                await bot.http.edit_profile({"global_name": BOT_DISPLAY_NAME})
                print(f"✅ Display name set to: {BOT_DISPLAY_NAME}")
            except discord.HTTPException as name_error:
                print(f"❌ Could not set display name: {name_error}")

    try:
        application = await bot.application_info()
        if application.description != BOT_DESCRIPTION:
            await application.edit(description=BOT_DESCRIPTION)
            print(f"✅ Description set to: {BOT_DESCRIPTION}")
    except discord.HTTPException as e:
        print(f"❌ Could not set description: {e}")

    try:
        activity = discord.CustomActivity(name=BOT_STATUS)
        await bot.change_presence(status=discord.Status.online, activity=activity)
        print(f"✅ Status set to: {BOT_STATUS}")
    except discord.HTTPException as e:
        print(f"❌ Could not set status: {e}")

@bot.event
async def on_ready():
    print(f'{bot.user} ({BOT_DISPLAY_NAME}) has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} servers')

    await apply_bot_profile()
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

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