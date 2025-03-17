import json
import os
 
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def load_config():
    default_config = {
        "download_folder": os.path.expanduser("~/Downloads"),
        "format_choice": "Best",
        "language": "English"
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding config.json: {e}. Using default config.")
            return default_config
    return default_config

def update_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error updating config.json: {e}")