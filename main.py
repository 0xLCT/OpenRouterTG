import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Parse whitelist from env (comma-separated list of user IDs)
WHITELIST = [int(id.strip()) for id in os.getenv("ALLOWED_USERS", "").split(",") if id.strip()]

# Configure OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Dicionário para armazenar histórico de conversas para cada usuário
conversation_history = {}

# Adiciona variáveis globais
available_models = {
    '1': 'anthropic/claude-3.5-sonnet:beta',
    '2': 'anthropic/claude-3-5-haiku:beta',
    '3': 'google/gemini-pro-1.5',
    '4': 'google/gemini-flash-1.5',
    '5': 'meta-llama/llama-3.1-8b-instruct',
    '6': 'mistralai/mistral-nemo',
    '7': 'openai/gpt-4o',
    '8': 'openai/gpt-4o-mini'
}
user_models = {}  # Armazena preferências de modelo do usuário

# Adicionar função whitelist
def is_user_allowed(user_id: int) -> bool:
    return len(WHITELIST) == 0 or user_id in WHITELIST

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.message.from_user.id):
        await update.message.reply_text('Não autorizado.')
        return
    await update.message.reply_text('Ola sou seu assistente pessoal.\nUse /models para escolher o modelo e /clear para limpar o contexto')

async def models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.message.from_user.id):
        await update.message.reply_text('Não autorizado.')
        return
    keyboard = [
        [InlineKeyboardButton("Claude 3.5 Sonnet", callback_data='1')],
        [InlineKeyboardButton("Claude 3.5 Haiku", callback_data='2')],
        [InlineKeyboardButton("Gemini Pro 1.5", callback_data='3')],
        [InlineKeyboardButton("Gemini Flash 1.5", callback_data='4')],
        [InlineKeyboardButton("Llama 3.1 8B", callback_data='5')],
        [InlineKeyboardButton("Mistral Nemo", callback_data='6')],
        [InlineKeyboardButton("GPT-4o", callback_data='7')],
        [InlineKeyboardButton("GPT-4o Mini", callback_data='8')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Selecione um modelo:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.callback_query.from_user.id):
        await update.callback_query.answer('Não autorizado.')
        return
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    selected_model = available_models[query.data]
    user_models[user_id] = selected_model
    await query.edit_message_text(f"Modelo selecionado: {selected_model}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.message.from_user.id):
        await update.message.reply_text('Sorry, you are not authorized to use this bot.')
        return
    try:
        user_id = update.message.from_user.id
        user_message = update.message.text
        
        model = user_models.get(user_id, "openai/gpt-4o-mini")
        
        if user_id not in conversation_history:
            conversation_history[user_id] = []

        conversation_history[user_id].append({"role": "user", "content": user_message})
        
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": os.getenv("SITE_URL", "http://localhost"),
                "X-Title": "TelegramOpenRouterBot"
            },
            model=model,
            messages=conversation_history[user_id]
        )
        
        response = completion.choices[0].message.content
        conversation_history[user_id].append({"role": "assistant", "content": response})
        await update.message.reply_text(response)
        
    except Exception as e:
        await update.message.reply_text(f"Erro: {str(e)}")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.message.from_user.id):
        await update.message.reply_text('Não autorizado.')
        return
    user_id = update.message.from_user.id
    if user_id in conversation_history:
        del conversation_history[user_id]
    await update.message.reply_text('Contexto limpo.')

def main():

    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(CommandHandler("models", models))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()