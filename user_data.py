import json
import os
from datetime import datetime

# File to store user data
DATA_FILE = "user_profiles.json"

def save_user_profile(user_id, profile_data):
    """
    Save or update a user profile to the data file
    
    Args:
        user_id (int): Telegram user ID
        profile_data (dict): User profile information
    """
    # Load existing data
    profiles = load_all_profiles()
    
    # Add timestamp
    profile_data['last_updated'] = datetime.now().isoformat()
    
    # Update or add the profile
    profiles[str(user_id)] = profile_data
    
    # Save to file
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)
    
    return True

def load_user_profile(user_id):
    """
    Load a specific user profile
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        dict: User profile or None if not found
    """
    profiles = load_all_profiles()
    return profiles.get(str(user_id))

def load_all_profiles():
    """
    Load all user profiles
    
    Returns:
        dict: Dictionary of user profiles with user_id as keys
    """
    if not os.path.exists(DATA_FILE):
        return {}
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is empty or invalid, return empty dict
        return {}

def get_all_user_ids():
    """
    Get a list of all registered user IDs.

    Returns:
        list: List of user IDs (as strings).
    """
    profiles = load_all_profiles()
    return list(profiles.keys())

def get_profiles_by_criteria(criteria):
    """
    Filter profiles by specified criteria
    
    Args:
        criteria (dict): Key-value pairs to match in profiles
        
    Returns:
        list: List of matching profiles
    """
    profiles = load_all_profiles()
    results = []
    
    for user_id, profile in profiles.items():
        matches = True
        for key, value in criteria.items():
            if key not in profile or profile[key] != value:
                matches = False
                break
        
        if matches:
            # Add user_id to profile for reference
            profile_copy = profile.copy()
            profile_copy['user_id'] = user_id
            results.append(profile_copy)
    
    return results 