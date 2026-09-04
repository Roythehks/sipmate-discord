#!/usr/bin/env python3
"""
Simple runner script for the Hydration Bot
Loads environment variables from config.env if it exists
"""

import asyncio
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

def load_env_file(file_path):
    """Load environment variables from a file"""
    if not os.path.exists(file_path):
        print(f"🔍 File {file_path} not found")
        return False
    
    print(f"📁 Found {file_path}, loading...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines_loaded = 0
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    os.environ[key] = value
                    lines_loaded += 1
                    
                    # Don't print the actual token value for security
                    if 'TOKEN' in key.upper():
                        print(f"   ✅ {key}=***hidden***")
                    else:
                        print(f"   ✅ {key}={value}")
            
            print(f"📊 Loaded {lines_loaded} environment variables from {file_path}")
            return lines_loaded > 0
            
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False

def main():
    print("🤖 Starting Hydration Bot...")
    print(f"📍 Current directory: {os.getcwd()}")
    
    # Try to load from config.env
    config_files = ['config.env', '.env']
    loaded = False
    
    for config_file in config_files:
        print(f"\n🔍 Checking for {config_file}...")
        if load_env_file(config_file):
            loaded = True
            break
    
    if not loaded:
        print("\n⚠️  No config file found or no variables loaded.")
        print("💡 Tip: Create a config.env file with your DISCORD_BOT_TOKEN")
    
    # Check if token is available
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("\n❌ Error: DISCORD_BOT_TOKEN not found!")
        print("\n📝 Setup Instructions:")
        print("1. Copy config.env.example to config.env")
        print("2. Add your Discord bot token to config.env")
        print("3. Or set the environment variable: set DISCORD_BOT_TOKEN=your_token")
        print("\n🔧 Debug info:")
        print(f"   Current working directory: {os.getcwd()}")
        print(f"   Files in directory: {list(os.listdir('.'))}")
        if os.path.exists('config.env'):
            print("   config.env exists!")
            with open('config.env', 'r') as f:
                content = f.read().strip()
                print(f"   config.env content length: {len(content)} characters")
                if 'DISCORD_BOT_TOKEN' in content:
                    print("   ✅ DISCORD_BOT_TOKEN found in file")
                else:
                    print("   ❌ DISCORD_BOT_TOKEN not found in file")
        sys.exit(1)
    else:
        print(f"✅ DISCORD_BOT_TOKEN found! (length: {len(token)} characters)")
    
    # Import and run the bot
    print("\n🚀 Starting Discord bot...")
    try:
        import bot
        asyncio.run(bot.main())
    except ImportError as e:
        print(f"❌ Error importing bot: {e}")
        print("💡 Make sure to install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped.")

if __name__ == "__main__":
    main() 