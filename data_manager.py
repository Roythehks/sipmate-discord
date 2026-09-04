import json
import os
from datetime import datetime

DATA_DIR = 'data'
REMINDER_CHANNELS_FILE = os.path.join(DATA_DIR, 'reminder_channels.json')
USER_RESET_TIMES_FILE = os.path.join(DATA_DIR, 'user_reset_times.json')
USER_PROGRESS_FILE = os.path.join(DATA_DIR, 'user_progress.json')

def setup_data_files():
    """Ensure data directory and files exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    for file_path in [REMINDER_CHANNELS_FILE, USER_RESET_TIMES_FILE, USER_PROGRESS_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f)

def load_data(file_path):
    """Load data from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_data(file_path, data):
    """Save data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def load_reminder_channels():
    """Load reminder channels data."""
    return load_data(REMINDER_CHANNELS_FILE)

def save_reminder_channels(data):
    """Save reminder channels data."""
    save_data(REMINDER_CHANNELS_FILE, data)

def load_user_reset_times():
    """Load user reset times, converting string back to datetime object."""
    raw_data = load_data(USER_RESET_TIMES_FILE)
    processed_data = {}
    for user_id, time_str in raw_data.items():
        processed_data[user_id] = datetime.fromisoformat(time_str)
    return processed_data

def save_user_reset_times(data):
    """Save user reset times, converting datetime object to string."""
    processed_data = {}
    for user_id, time_obj in data.items():
        processed_data[user_id] = time_obj.isoformat()
    save_data(USER_RESET_TIMES_FILE, processed_data)

def load_user_progress():
    """Load user progress data."""
    return load_data(USER_PROGRESS_FILE)

def save_user_progress(data):
    """Save user progress data."""
    save_data(USER_PROGRESS_FILE, data)

def get_user_progress(user_id):
    """Get a user's progress for today."""
    progress_data = load_user_progress()
    today = datetime.now().date().isoformat()
    
    user_id_str = str(user_id)

    if user_id_str not in progress_data:
        return 0 # No progress logged yet

    if today not in progress_data[user_id_str]:
        return 0 # No progress logged today

    return progress_data[user_id_str][today].get('cups', 0)

def log_user_progress(user_id, cups_to_add):
    """Log water intake for a user."""
    progress_data = load_user_progress()
    today = datetime.now().date().isoformat()
    
    user_id_str = str(user_id)

    if user_id_str not in progress_data:
        progress_data[user_id_str] = {}
    
    if today not in progress_data[user_id_str]:
        progress_data[user_id_str][today] = {'cups': 0}
        
    progress_data[user_id_str][today]['cups'] += cups_to_add
    
    save_user_progress(progress_data)
    return progress_data[user_id_str][today]['cups'] 