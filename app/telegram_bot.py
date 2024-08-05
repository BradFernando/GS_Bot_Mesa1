from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

from app.GPT.gpt_integration import handle_text
from app.utils.responses import responses
from app.utils.keyboards import get_otros_keyboard, show_categories, show_products, show_most_ordered_product
from app.utils.logging_config import setup_logging
from app.config import settings

logger = setup_logging()

# Se define el nombre del bot aquí
bot_name = "MesaBot"


# Function to get the greeting based on the current time
def get_greeting() -> str:
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        return "Buenos días"
    elif 12 <= current_hour < 18:
        return "Buenas tardes"
    else:
        return "Buenas noches"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a greeting message followed by inline buttons."""
    logger.info("Handling /start command")

    # Determine the source of the update
    if isinstance(update, Update) and update.message:
        user_first_name = update.message.from_user.first_name
        chat_id = update.message.chat_id
    elif isinstance(update, Update) and update.callback_query:
        user_first_name = update.callback_query.from_user.first_name
        chat_id = update.callback_query.message.chat_id
    else:
        logger.warning("Update does not have message or callback_query")
        return  # Exit if neither condition is met

    greeting = get_greeting()

    # Log the chat_id to ensure it's being captured correctly
    logger.info(f"Chat ID: {chat_id}")

    # Format the greeting message using Markdown
    greeting_message = responses["greeting_message"].format(
        greeting=greeting,
        user_first_name=user_first_name,
        chat_id=f"`{chat_id}`",  # Usa backticks para formato de código
        bot_name=bot_name
    )

    if isinstance(update, Update) and update.message:
        await update.message.reply_text(greeting_message, parse_mode='Markdown')
    elif isinstance(update, Update) and update.callback_query:
        await update.callback_query.message.edit_text(greeting_message, parse_mode='Markdown')

    keyboard = [
        [InlineKeyboardButton("Cuál es el menú de hoy 📋", callback_data="menu")],
        [InlineKeyboardButton("Cómo puedo realizar un pedido 📑❓", callback_data="pedido")],
        [InlineKeyboardButton("Preguntas acerca del Bot 🤖⁉", callback_data="otros")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if isinstance(update, Update) and update.message:
        await update.message.reply_text(responses["menu_message"], reply_markup=reply_markup)
    elif isinstance(update, Update) and update.callback_query:
        await update.callback_query.message.edit_text(responses["menu_message"], reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    await query.answer()

    logger.info(f"Callback data received: {query.data}")

    if query.data == "menu":
        await show_categories(query)
    elif query.data.startswith("category_"):
        category_id = int(query.data.split("_")[1])
        await show_products(query, category_id)
    elif query.data == "pedido":
        response = responses["pedido_response"]
        keyboard = [[InlineKeyboardButton("Regresar al Inicio ↩", callback_data="return_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=response, reply_markup=reply_markup)
    elif query.data == "otros":
        reply_markup = get_otros_keyboard()
        await query.edit_message_text(text=responses["other_questions_message"], reply_markup=reply_markup)
    elif query.data == "tiempo_pedido":
        response = responses["tiempo_pedido_response"]
        keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=response, reply_markup=reply_markup)
    elif query.data == "producto_mas_pedido":
        await show_most_ordered_product(query)
    elif query.data == "orden_mal":
        response = responses["orden_mal_response"]
        keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=response, reply_markup=reply_markup)
    elif query.data == "app_no_abre":
        response = responses["app_no_abre_response"]
        keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=response, reply_markup=reply_markup)
    elif query.data == "info_proporcionada":
        response = responses["info_proporcionada_response"]
        keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=response, reply_markup=reply_markup)
    elif query.data == "return_start":
        await start(update, context)
    elif query.data == "return_otros":
        reply_markup = get_otros_keyboard()
        await query.edit_message_text(text=responses["other_questions_message"], reply_markup=reply_markup)
    elif query.data == "return_categories":
        logger.info("Returning to categories")
        await show_categories(query)


def run_bot():
    application = Application.builder().token(settings.bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))  # Manejar mensajes de texto

    application.run_polling()
