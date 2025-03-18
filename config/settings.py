import os
import json
import sys

def get_config_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.join(os.getenv("APPDATA"), "CoffeeYTDownloader")
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    return os.path.join(base_path, "config.json")

def load_config():
    config_path = get_config_path()
    default_config = {
        "download_folder": os.path.expanduser("~/Downloads"),
        "format_choice": "Best",
        "language": "English"
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding config.json: {e}. Using default config.")
            return default_config
    return default_config

def update_config(config):
    """Lưu config vào file"""
    config_path = get_config_path()
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print(f"Config saved to: {config_path}")
    except Exception as e:
        print(f"Error updating config.json: {e}")