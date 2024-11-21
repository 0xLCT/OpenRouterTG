import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Send me a message and I will process it with OpenRouter.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Get message from user
        user_message = update.message.text
        
        # Send to OpenRouter
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": os.getenv("SITE_URL", "http://localhost"),
                "X-Title": "TelegramOpenRouterBot"
            },
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )
        
        # Send response back to user
        response = completion.choices[0].message.content
        await update.message.reply_text(response)
        
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    # Create application
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run bot
    application.run_polling()

if __name__ == "__main__":
    main()