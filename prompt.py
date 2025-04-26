import os
from dotenv import load_dotenv
import asyncio
from telegram import Bot
from openai import OpenAI
import user_data

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_IDS = os.getenv('TELEGRAM_CHAT_ID', '').split(',')  # Split multiple IDs by comma
OPEN_AI_API_KEY = os.getenv('OPEN_AI_API_KEY')
OPEN_AI_MODEL = "gpt-4o-mini"

def ask_question(user_id=None, question=None):
    """
    Let a user ask a question to the bot; considering the user's profile data
    
    Args:
        user_id (str): The telegram user ID
        question (str): The question asked by the user
        
    Returns:
        str: The generated response
    """
    # Try to get the user's profile if user_id is provided
    user_profile = None
    if user_id:
        user_profile = user_data.load_user_profile(user_id)
    
    # Create a personalized prompt based on available profile data
    system_message = "You are an expert on parenting and pregnancy that explains things in an easy to understand way."
    
    if user_profile:
        # Extract user profile data
        age = user_profile.get('age', 'unknown age')
        ethnicity = user_profile.get('ethnicity', '')
        gender = user_profile.get('gender', '')
        stage = user_profile.get('stage', '')
        country = user_profile.get('country', '')
        experience = user_profile.get('experience', '')
        
        # Build a personalized context
        context = f"I am an {age}-year-old {ethnicity} {gender}. "
        
        if stage and stage != 'n/a':
            context += f"I am in {stage} of pregnancy. "
        
        if experience:
            context += f"I am a {experience.lower()}. "
            
        if country:
            context += f"I am located in {country}. "
        
        # Default question if none provided
        if not question:
            question = "Give me advice for my situation."
            
        # Combine context with user question
        prompt = f"{context}\n\nMy question is: {question}"
    else:
        # Default prompt for users without profiles
        if not question:
            prompt = "Give me general advice for new parents."
        else:
            prompt = question
    
    # Create the message using OpenAI
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]
    
    client = OpenAI(api_key=OPEN_AI_API_KEY)
    response = client.chat.completions.create(
        model=OPEN_AI_MODEL,
        messages=messages
    )
    return response.choices[0].message.content

def get_tips(user_id=None):
    """
    Generate a personalized message based on user profile data
    
    Args:
        user_id (str): The telegram user ID
        
    Returns:
        str: The generated message
    """
    # Try to get the user's profile if user_id is provided
    user_profile = None
    if user_id:
        user_profile = user_data.load_user_profile(user_id)
    
    # Create a personalized prompt based on available profile data
    system_message = "You are an expert on fertility and pregnancy for parents and expecting parents whose tips are easy to understand and digest. "
    
    if user_profile:
        # Extract user profile data
        age = user_profile.get('age', 'unknown age')
        ethnicity = user_profile.get('ethnicity', '')
        gender = user_profile.get('gender', '')
        stage = user_profile.get('stage', '')
        country = user_profile.get('country', '')
        experience = user_profile.get('experience', '')
        
        # Build a personalized prompt
        prompt = f"Generate a tip for a {age}-year-old {ethnicity} {gender}."
        
        if stage and stage != 'n/a':
            prompt += f"who is in {stage} of pregnancy. "
        
        if experience:
            prompt += f"They are a {experience.lower()}. "
            
        if country:
            prompt += f"They are located in {country}. "
            
        prompt += "The tips should be less than 100 words in point form and prioritize readability and digestability. The tips should revolve around nutrition, fertility windows, supplements, fertility advice, diet and exercise advice."
    else:
        # Default prompt if no user profile
        prompt = "Generate a general tip about pregnancy and fertility. The tips should be less than 100 words in point form and prioritize readability and digestability."
    
    # Create the message using OpenAI
    roles_motivational_message = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]
    
    client = OpenAI(api_key=OPEN_AI_API_KEY)
    response = client.chat.completions.create(
        model=OPEN_AI_MODEL,
        messages=roles_motivational_message
    )
    return response.choices[0].message.content