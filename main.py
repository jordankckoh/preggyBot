import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ConversationHandler, ContextTypes, JobQueue
)
import user_data
import asyncio
from datetime import time
from prompt import ask_question, get_tips

# Load environment variables
load_dotenv()

# Define states
AGE, ETHNICITY, GENDER, STAGE, COUNTRY, EXPERIENCE = range(6)

# Define state for ask command
ASKING = range(1)[0]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Clear any existing data in context
    context.user_data.clear()
    
    # Check if user has an existing profile
    user_profile = user_data.load_user_profile(str(update.effective_user.id))
    if user_profile:
        await update.message.reply_text(
            f"Welcome back! I already have your profile:\n\n"
            f"Age: {user_profile.get('age')}\n"
            f"Ethnicity: {user_profile.get('ethnicity')}\n"
            f"Gender: {user_profile.get('gender')}\n"
            f"Stage: {user_profile.get('stage')}\n"
            f"Country: {user_profile.get('country')}\n"
            f"Experience: {user_profile.get('experience')}\n\n"
            f"Would you like to update it? If yes, let's start with your age."
        )
    else:
        await update.message.reply_text(
            "Hi! Let's set up your profile.\nHow old are you?",
            reply_markup=ReplyKeyboardRemove()
        )
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    await update.message.reply_text("What's your ethnicity?")
    return ETHNICITY

async def ethnicity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ethnicity'] = update.message.text
    gender_keyboard = [["Female", "Male"]]
    await update.message.reply_text(
        "What's your gender?", 
        reply_markup=ReplyKeyboardMarkup(gender_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return GENDER

async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_gender = update.message.text.lower()
    context.user_data['gender'] = update.message.text
    
    # If gender is male, skip the stage question and set stage to 'n/a'
    if user_gender == 'male':
        context.user_data['stage'] = 'n/a'
        await update.message.reply_text("What country are you in?")
        return COUNTRY
    else:
        # For non-male users, ask about the stage
        stage_keyboard = [["Pre-pregnancy", "1st Trimester"], ["2nd Trimester", "3rd Trimester"], ["Postpartum"]]
        await update.message.reply_text(
            "What stage are you in?", 
            reply_markup=ReplyKeyboardMarkup(stage_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return STAGE

async def stage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['stage'] = update.message.text
    await update.message.reply_text("What country are you in?")
    return COUNTRY

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['country'] = update.message.text
    experience_keyboard = [["First-time parent", "Experienced parent"]]
    await update.message.reply_text(
        "Are you a first-time parent or experienced?", 
        reply_markup=ReplyKeyboardMarkup(experience_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return EXPERIENCE

async def experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['experience'] = update.message.text
    
    # Save to persistent storage
    user_id = str(update.effective_user.id)
    user_data.save_user_profile(user_id, context.user_data)
    
    # Profile complete
    profile_text = f"""Profile saved:
- Age: {context.user_data.get('age')}
- Ethnicity: {context.user_data.get('ethnicity')}
- Gender: {context.user_data.get('gender')}
- Stage: {context.user_data.get('stage')}
- Country: {context.user_data.get('country')}
- Experience: {context.user_data.get('experience')}"""
    
    await update.message.reply_text(
        f"Thanks! Your profile has been saved.\n\n{profile_text}",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Operation canceled.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

async def view_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View current user profile."""
    user_id = str(update.effective_user.id)
    profile = user_data.load_user_profile(user_id)
    
    if profile:
        profile_text = f"""Your profile:
- Age: {profile.get('age')}
- Ethnicity: {profile.get('ethnicity')}
- Gender: {profile.get('gender')}
- Stage: {profile.get('stage')}
- Country: {profile.get('country')}
- Experience: {profile.get('experience')}
- Last updated: {profile.get('last_updated', 'N/A')}"""
        
        await update.message.reply_text(profile_text)
    else:
        await update.message.reply_text(
            "You don't have a profile yet. Use /start to create one."
        )

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the ask conversation."""
    await update.message.reply_text("What is your question?")
    return ASKING

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the user's question and end the conversation."""
    user_id = str(update.effective_user.id)
    question = update.message.text
    
    # Send typing action while generating response
    await update.message.chat.send_action(action="typing")
    
    # Get the response from OpenAI
    response = ask_question(user_id, question)
    
    # Send the response
    await update.message.reply_text(response)
    
    # End the conversation
    return ConversationHandler.END

async def send_daily_tip(context: ContextTypes.DEFAULT_TYPE):
    """Sends a personalized tip to all registered users."""
    user_ids = user_data.get_all_user_ids()
    if not user_ids:
        print("No users found to send daily tips.")
        return

    print(f"Starting daily tip sending to {len(user_ids)} users...")
    for user_id in user_ids:
        try:
            tip = get_tips(user_id) # Note: get_tips is synchronous
            await context.bot.send_message(chat_id=user_id, text=tip)
            print(f"Sent daily tip to user {user_id}")
            # Add a small delay to avoid hitting rate limits if many users
            await asyncio.sleep(1) 
        except Exception as e:
            print(f"Failed to send tip to user {user_id}: {e}")
    print("Finished sending daily tips.")

async def setup_application():
    """Setup the bot application with handlers and job queue.""" 
    # Get token from environment variable
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

    builder = Application.builder().token(token)
    builder.job_queue(JobQueue()) 

    application = builder.build() 

    # Profile Conversation Handler - Restored full definition
    profile_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            ETHNICITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ethnicity)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            STAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, stage)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, experience)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Ask Conversation Handler - Verified definition
    ask_conv_handler = ConversationHandler(
            entry_points=[CommandHandler('ask', ask)],
            states={
                ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Help Command Handler Function Definition
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        await update.message.reply_text(
            "Use /start to setup/update your profile.\n"
            "Use /profile to view your profile.\n"
            "Use /ask to ask a question.\n"
            "Use /cancel to stop profile setup or asking a question."
        )

    # Add all handlers
    application.add_handler(profile_conv_handler)
    application.add_handler(ask_conv_handler)
    application.add_handler(CommandHandler("profile", view_profile))
    application.add_handler(CommandHandler("help", help_command)) # Added help handler

    return application

async def main():
    """Start the bot with explicit lifecycle management."""
    application = await setup_application()
    print("Application setup complete.")

    # --- Schedule the daily tip job ---
    # Ensure job_queue exists before accessing it
    if application.job_queue:
        job_queue = application.job_queue
        # Run daily at 09:00 UTC.
        daily_time = time(hour=5, minute=0, second=0)
        job_queue.run_daily(send_daily_tip, time=daily_time, name="daily_tip_job")
        print(f"Scheduled daily tip job to run at {daily_time} UTC.")
    else:
        print("JobQueue not available, skipping job scheduling.")
    # ----------------------------------

    # Explicitly initialize, start, and start polling
    print("Initializing application...")
    await application.initialize()
    print("Starting application...")
    await application.start()
    print("Starting updater polling...")
    await application.updater.start_polling()
    print("Bot is running. Press Ctrl+C to stop.")

    # Keep the application running indefinitely until interrupted
    # Create a future that never completes
    stop_future = asyncio.Future()
    try:
        await stop_future
    except KeyboardInterrupt:
        print("Ctrl+C received, shutting down...")
    except asyncio.CancelledError:
        print("Task cancelled, shutting down...")
    finally:
        # Explicitly stop polling and shutdown
        print("Stopping updater polling...")
        await application.updater.stop()
        print("Stopping application...")
        await application.stop()
        print("Shutting down application...")
        await application.shutdown()
        print("Shutdown complete.")

if __name__ == '__main__':
    # Add check for Windows ProactorEventLoop if needed, though likely not the issue here
    # if os.name == 'nt':
    #     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    # Run the async main function using asyncio.run()
    asyncio.run(main())