import random
from datetime import datetime
import hashlib
from data_manager import get_user_progress as get_user_progress_data

# Water tracking constants
DAILY_GOAL_CUPS = 8  # Standard recommendation
ML_PER_CUP = 240     # Standard cup size in ml
DAILY_GOAL_ML = DAILY_GOAL_CUPS * ML_PER_CUP  # 1920ml

# Water reminder messages with progress tracking
WATER_REMINDERS = [
    "💧 **Hydration Check!** Time to drink some water! Your body will thank you! 🌊",
    "🚰 **Water Break!** Remember to stay hydrated throughout the day! 💙",
    "💦 **Drink up!** Your brain is 75% water - keep it topped up! 🧠",
    "🌊 **Hydration Station!** Time for a refreshing glass of water! ✨",
    "💧 **Water Reminder!** Every sip counts toward your daily hydration goal! 🎯",
    "🥤 **Thirsty?** Even if you're not, your body could use some water right now! 😊",
    "💦 **H2O Time!** Stay healthy, stay hydrated! Your skin will glow! ✨",
    "🌊 **Water Break!** Take a moment to hydrate and refresh yourself! 🌿",
    "💧 **Drink Water!** Your kidneys are working hard - give them some help! 💪",
    "🚰 **Hydration Alert!** Remember: if you're thirsty, you're already dehydrated! 📢"
]

HYDRATION_TIPS = [
    "💡 **Tip:** Add lemon or cucumber to your water for extra flavor!",
    "💡 **Tip:** Keep a water bottle at your desk as a visual reminder!",
    "💡 **Tip:** Drink a glass of water first thing in the morning!",
    "💡 **Tip:** Set hourly reminders on your phone to drink water!",
    "💡 **Tip:** Eat water-rich foods like watermelon and cucumber!",
    "💡 **Tip:** Drink water before, during, and after exercise!",
    "💡 **Tip:** Your urine should be light yellow - darker means drink more!",
    "💡 **Tip:** Room temperature water is absorbed faster than cold water!",
    "💡 **Tip:** Herbal teas count toward your daily water intake!",
    "💡 **Tip:** Aim for 8 glasses of water per day, more if you're active!"
]

# Status messages for the bot
STATUS_MESSAGES = [
    "💧 Drink water!",
    "🌊 Stay hydrated!",
    "💦 H2O reminder!",
    "🥤 Time for water!",
    "💙 Hydration matters!",
    "🌿 Water = life!",
    "⭐ Healthy hydration!",
    "🏆 8 cups daily!"
]

def get_water_progress(user_id):
    """Get water intake progress for a user."""
    cups_consumed = get_user_progress_data(user_id)
    ml_consumed = cups_consumed * ML_PER_CUP
    
    return cups_consumed, ml_consumed

def create_progress_bar(current, total, length=10):
    """Create a visual progress bar"""
    if total == 0:
        return "N/A", 0
    filled = int((current / total) * length)
    empty = length - filled
    
    bar = "🟦" * filled + "⬜" * empty
    percentage = (current / total) * 100
    
    return bar, percentage

def get_status_emoji(cups_consumed):
    """Get status emoji based on progress"""
    if cups_consumed >= DAILY_GOAL_CUPS:
        return "🏆"  # Trophy for completing goal
    elif cups_consumed >= DAILY_GOAL_CUPS * 0.75:
        return "🌟"  # Star for good progress
    elif cups_consumed >= DAILY_GOAL_CUPS * 0.5:
        return "⚡"  # Lightning for halfway
    else:
        return "🌱"  # Seedling for starting out 