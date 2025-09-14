import os
import json
import secrets

CONFIG_FILE = os.path.expanduser("~/.asciichat.json")

def load_or_create_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        print(f"[INFO] Loaded config for handle: {config['handle']}")
        return config
    else:
        print("[INFO] No config found. Let's set up your handle.")
        handle = input("Enter your unique handle (e.g., jd421_5211): ").strip()
        secret = secrets.token_hex(16)
        config = {"handle": handle, "secret": secret}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        print(f"[INFO] Registered handle: {handle}")
        return config

if __name__ == "__main__":
    config = load_or_create_config()
    print(f"Your handle: {config['handle']}")
    print(f"Your secret: {config['secret']}")
    print(f"Config saved to {CONFIG_FILE}")
