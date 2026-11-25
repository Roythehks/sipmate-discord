import json
import os

DATA_DIR = 'data'
MIMIC_EMOJIS_FILE = os.path.join(DATA_DIR, 'mimic_emojis.json')

def setup_data_files():
    """Ensure data directory and files exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(MIMIC_EMOJIS_FILE):
        with open(MIMIC_EMOJIS_FILE, 'w') as f:
            json.dump({}, f)

def load_data(file_path):
    """Load data from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_data(file_path, data):
    """Save data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def load_mimic_emojis():
    """Load per-guild trigger emoji. Missing guilds use the default at the call site."""
    return load_data(MIMIC_EMOJIS_FILE)

def save_mimic_emojis(data):
    """Save per-guild trigger emoji."""
    save_data(MIMIC_EMOJIS_FILE, data)
