import json
import os

# Updated to look in the same directory as the script
PROFILES_FILE = os.path.join(os.path.dirname(__file__), "connections.json")

def load_profiles() -> dict:
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_profile(name: str, data: dict):
    profiles = load_profiles()
    profiles[name] = data
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)

def delete_profile(name: str):
    profiles = load_profiles()
    profiles.pop(name, None)
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)