# SipMate

A Discord bot for hydration tracking and reminders. Built with discord.py 2.3+.

## Features

- **Hydration Tracking** — Log water intake with `/log` and track progress toward daily goals (8 cups / 1920ml)
- **Progress Visualization** — Visual progress bars and status emojis in rich embeds
- **Automatic Reminders** — Hourly hydration reminders in configured channels (UTC+8)
- **Custom Schedules** — `/reset` to set a personalized tracking timeline
- **User Stats** — `/stats` for detailed hydration dashboard
- **Role Management** — Auto-creates and assigns a "💧 Hydrated" role on server join

## Commands

| Command | Description | Permission |
|---------|-------------|------------|
| `/water` | View hydration progress with progress bar | Everyone |
| `/log <cups>` | Log water intake (1-20 cups) | Everyone |
| `/stats` | Detailed hydration dashboard | Everyone |
| `/tip` | Random hydration tip | Everyone |
| `/hydrate @user` | Send reminder to a specific user | Everyone |
| `/reset` | Reset daily tracking timeline | Everyone |
| `/menu` | Interactive command menu | Everyone |
| `/invite` | Get bot invite link | Everyone |
| `/support` | Support information | Everyone |
| `/setchannel` | Enable auto-reminders in current channel | Admin |
| `/removechannel` | Disable auto-reminders | Admin |

## Setup

### Prerequisites

- Python 3.8+
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))

### Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/dc2.git
cd dc2
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `config.env` and add your bot token:

```env
DISCORD_BOT_TOKEN=your_token_here
```

4. Run the bot:

```bash
python run.py
```

### Bot Permissions

When inviting the bot, grant these permissions:

- Send Messages
- Manage Roles
- Use Slash Commands
- Embed Links
- Read Message History
- Add Reactions
- View Channels

## Project Structure

```
dc2/
├── bot.py              # Main bot entry point and event handlers
├── run.py              # Runner script with environment loading
├── utils.py            # Utility functions and constants
├── data_manager.py     # JSON data persistence layer
├── config.env          # Environment variables (not committed)
├── requirements.txt    # Python dependencies
├── cogs/
│   ├── commands.py     # User-facing slash commands
│   ├── admin.py        # Admin-only commands
│   └── tasks.py        # Scheduled tasks and loops
└── data/
    ├── user_progress.json
    ├── user_reset_times.json
    └── reminder_channels.json
```

## Configuration

### Constants (`utils.py`)

| Constant | Default | Description |
|----------|---------|-------------|
| `DAILY_GOAL_CUPS` | 8 | Daily water intake goal |
| `ML_PER_CUP` | 240 | Milliliters per cup |
| `DAILY_GOAL_ML` | 1920 | Daily goal in ml (auto-calculated) |

### Reminder Schedule

Reminders send at :30 past every hour (UTC+8) to channels configured via `/setchannel`.

## Data Storage

User data is stored locally in JSON files under the `data/` directory:

- `user_progress.json` — Daily water intake logs per user
- `user_reset_times.json` — Custom reset timestamps
- `reminder_channels.json` — Server-to-channel mapping for auto-reminders

## License

This project is open source and available under the MIT License.
