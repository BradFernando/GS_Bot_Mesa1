import os
import re
import openai
from telegram import Update
from telegram.ext import ContextTypes
from app.utils.keyboards import (show_categories, show_most_ordered_product, show_most_sold_drink,
                                 show_most_sold_sport_drink, show_most_sold_breakfast, show_most_sold_starter,
                                 show_most_sold_second, show_most_sold_snack, recommend_drink_by_price,
                                 recommend_sport_drink_by_price, recommend_breakfast_by_price,
                                 recommend_starter_by_price, recommend_second_by_price, recommend_snack_by_price,
                                 show_product_by_name, show_product_stock_by_name, show_product_stock_by_productname,
                                 show_product_price_by_name, show_most_sold_main)
from app.utils.logging_config import setup_logging
from app.utils.rules import rules

logger = setup_logging()

# Configurar API de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Construir el contexto del sistema dinámicamente
system_context = {
    "role": "system",
    "content": " ".join(rules)  # Une las cadenas en rules en una sola cadena
}

# Definir constantes para patrones de expresiones regulares
MENU_PATTERNS = [
    r'\bmen[úu]\b', r'\bcarta\b', r'\bver opciones\b', r'\bver men[úu]\b', r'\bver carta\b'
]

MOST_ORDERED_PRODUCT_PATTERNS = [
    r'\bproducto m[aá]s pedido\b', r'\borden m[aá]s pedida\b', r'\bproducto m[aá]s vendido\b',
    r'\borden m[aá]s vendida\b', r'\bcu[aá]l es el producto más pedido\b'
]

MOST_SOLD_DRINK_PATTERNS = [
    r'\bbebida m[aá]s vendida\b', r'\bbebida m[aá]s popular\b', r'\bbebida m[aá]s pedida\b',
    r'\bcu[aá]l es la bebida más vendida\b', r'\bcu[aá]l es la bebida más popular\b'
]

MOST_SOLD_SPORT_DRINK_PATTERNS = [
    r'\bbebida deportiva m[aá]s vendida\b', r'\bbebida deportiva m[aá]s popular\b',
    r'\bbebida deportiva m[aá]s pedida\b',
    r'\bcu[aá]l es la bebida deportiva más vendida\b', r'\bcu[aá]l es la bebida deportiva más popular\b'
]

MOST_SOLD_BREAKFAST_PATTERNS = [
    r'\bdesayuno m[aá]s vendido\b', r'\bdesayuno m[aá]s popular\b', r'\bdesayuno m[aá]s pedido\b',
    r'\bcu[aá]l es el desayuno más vendido\b', r'\bcu[aá]l es el desayuno más popular\b'
]

MOST_SOLD_STARTER_PATTERNS = [
    r'\bentrada m[aá]s vendida\b', r'\bentrada m[aá]s popular\b', r'\bentrada m[aá]s pedida\b',
    r'\bcu[aá]l es la entrada más vendida\b', r'\bcu[aá]l es la entrada más popular\b'
]

MOST_SOLD_SECOND_COURSE_PATTERNS = [
    r'\bsegundo m[aá]s vendido\b', r'\bsegundo m[aá]s popular\b', r'\bsegundo m[aá]s pedido\b',
    r'\bcu[aá]l es el segundo más vendido\b', r'\bcu[aá]l es el segundo más popular\b'
]

MOST_SOLD_SNACK_PATTERNS = [
    r'\bsnack m[aá]s vendido\b', r'\bsnack m[aá]s popular\b', r'\bsnack m[aá]s pedido\b',
    r'\bcu[aá]l es el snack m[aá]s vendido\b', r'\bcu[aá]l es el snack m[aá]s popular\b'
]

PRODUCT_BY_NAME_PATTERN = [
    r'\btienes (\w+)\b',
    r'\bquiero un (\w+)\b',
    r'\bquiero una (\w+)\b',
    r'\bquisiera un (\w+)\b',
    r'\bquisiera una (\w+)\b',
    r'\bnecesito un (\w+)\b',
    r'\bnecesito una (\w+)\b'
    r'\bme gustar[ií]a un (\w+)\b',
    r'\bme gustar[ií]a una (\w+)\b',
    r'\bme gustar[ií]a pedir un (\w+)\b',
    r'\bme gustar[ií]a pedir una (\w+)\b',
    r'\bme gustar[ií]a ordenar un (\w+)\b',
    r'\bme gustar[ií]a ordenar una (\w+)\b',
    r'\bme gustar[ií]a pedir (\w+)\b',
    r'\bme gustar[ií]a ordenar (\w+)\b',
]

# Patrones de expresión regular para extraer la cantidad y el nombre del producto
PRODUCT_ORDER_PATTERN = [
    r'\bquiero\s+(-?\d+)\s+(.+)',  # Permite números negativos y positivos
    r'\bquisiera\s+(-?\d+)\s+(.+)',
    r'\bnecesito\s+(-?\d+)\s+(.+)',
    r'\bme gustar[ií]a\s+(-?\d+)\s+(.+)',
    r'\bme gustar[ií]a pedir\s+(-?\d+)\s+(.+)',
    r'\bme gustar[ií]a ordenar\s+(-?\d+)\s+(.+)',
]

# Patrones de expresión regular para consultar la cantidad de un producto
PRODUCT_QUANTITY_PATTERN = [
    r'\bcu[aá]nt[oa]s?\s+([\w\s]+)\s+(?:tienes|hay|quedan)(?:\s+en\s+(?:stock|inventario|existencia|bodega|almac['
    r'eé]n|dep[oó]sito|disponibles))?\b'
]

# Patrones de expresión regular para consultar el precio por nombre de producto
PRODUCT_PRICE_PATTERN = [
    r'\bcu[aá]nto\s+(?:cuesta|vale|valen|cuestan)\s+(?:el|la|los|las)?\s*([a-zA-Z\s]+)\b',
    r'\bqu[eé]\s+(?:precio|valor|costo)\s+(?:tiene|tienen)\s+(?:el|la|los|las)?\s*([a-zA-Z\s]+)\b',
    r'\bprecio\s+(?:del|de\s+la|de\s+los|de\s+las)?\s*([a-zA-Z\s]+)\b',
    r'\bcosto\s+(?:del|de\s+la|de\s+los|de\s+las)?\s*([a-zA-Z\s]+)\b',
    r'\bvalor\s+(?:del|de\s+la|de\s+los|de\s+las)?\s*([a-zA-Z\s]+)\b'
]

RECOMMEND_PRODUCT_PATTERNS = {
    "drink": [
        r'\bbebida recomendada\b', r'\bqu[eé] bebida recomiendas\b', r'\bqu[eé] bebida me recomiendas\b',
        r'\bqu[eé] bebida es buena\b', r'\bqu[eé] bebida econ[oó]mica me recomiendas\b',
        r'\bqu[eé] bebida es buena y econ[oó]mica\b'
    ],
    "sport_drink": [
        r'\bbebida deportiva recomendada\b', r'\bqu[eé] bebida deportiva recomiendas\b',
        r'\bqu[eé] bebida deportiva me recomiendas\b',
        r'\bqu[eé] bebida deportiva es buena\b', r'\bqu[eé] bebida deportiva econ[oó]mica me recomiendas\b',
        r'\bqu[eé] bebida deportiva es buena y econ[oó]mica\b'
    ],
    "breakfast": [
        r'\bdesayuno recomendado\b', r'\bqu[eé] desayuno recomiendas\b', r'\bqu[eé] desayuno me recomiendas\b',
        r'\bqu[eé] desayuno es bueno\b', r'\bqu[eé] desayuno econ[oó]mico me recomiendas\b',
        r'\bqu[eé] desayuno es bueno y econ[oó]mico\b'
    ],
    "starter": [
        r'\bentrada recomendada\b', r'\bqu[eé] entrada recomiendas\b', r'\bqu[eé] entrada me recomiendas\b',
        r'\bqu[eé] entrada es buena\b', r'\bqu[eé] entrada econ[oó]mica me recomiendas\b',
        r'\bqu[eé] entrada es buena y econ[oó]mica\b'
    ],
    "second_course": [
        r'\bsegundo recomendado\b', r'\bqu[eé] segundo recomiendas\b', r'\bqu[eé] segundo me recomiendas\b',
        r'\bqu[eé] segundo es bueno\b', r'\bqu[eé] segundo econ[oó]mico me recomiendas\b',
        r'\bqu[eé] segundo es bueno y econ[oó]mico\b', r'\bqu[eé] plato fuerte recomiendas\b',
        r'\bqu[eé] plato fuerte me recomiendas\b', r'\bqu[eé] plato fuerte es bueno\b',
        r'\bqu[eé] plato fuerte econ[oó]mico me recomiendas\b', r'\bqu[eé] plato fuerte es bueno y econ[oó]mico\b'
    ],
    "snack": [
        r'\bsnack recomendado\b', r'\bqu[eé] snack recomiendas\b', r'\bqu[eé] snack me recomiendas\b',
        r'\bqu[eé] snack es bueno\b', r'\bqu[eé] snack econ[oó]mico me recomiendas\b',
        r'\bqu[eé] snack es bueno y econ[oó]mico\b'
    ],
    "main": [
        r'\balmuerzo recomendado\b', r'\bqu[eé] almuerzo recomiendas\b', r'\bqu[eé] almuerzo me recomiendas\b',
        r'\bqu[eé] almuerzo es bueno\b', r'\bqu[eé] almuerzo econ[oó]mico me recomiendas\b',
        r'\bqu[eé] almuerzo es bueno y econ[oó]mico\b'

    ]
}
EXIT_PATTERNS = [r'\bsalir\b', r'\bsalir del chat\b', r'\bterminar\b']


# Función para vaciar el chat y cerrar la sesión
async def exit_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from app.telegram_bot import greeting_messages  # Importación retrasada
    chat_id = update.message.chat_id
    if chat_id in greeting_messages:
        greeting_message_id = greeting_messages[chat_id]["greeting_message_id"]
        await context.bot.delete_message(chat_id=chat_id, message_id=greeting_message_id)
        del greeting_messages[chat_id]

    await update.message.reply_text(
        "Gracias por preferirnos. ¡Hasta pronto 👋! Recuerda que para volver a ingresar "
        "puedes presionar el botón de abajo para ejecutar el comando /start.👈",
    )


# Función para verificar si un mensaje coincide con algún patrón
def match_pattern(patterns, message):
    for pattern in patterns:
        if re.search(pattern, message):
            print(f"Pattern matched: {pattern}")
            return True
    return False


# Función para manejar la respuesta basada en el patrón detectado
async def handle_response(update, patterns, handler_function):
    if match_pattern(patterns, update.message.text.lower()):
        logger.info(f"Pattern matched. Handling with {handler_function.__name__}")
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await handler_function(fake_query)
        return True
    return False


# Función para manejar la respuesta basada en el patrón detectado
async def handle_response_by_name(update, patterns, handler_function):
    message = update.message.text.lower()
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            product_name = match.group(1).strip().title()
            logger.info(f"Product name extracted: {product_name}")
            fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
            await handler_function(fake_query, product_name)
            return True
        else:
            logger.info("Tu mensaje esta siendo revisado...")
    return False


# Función para manejar la respuesta basada en el patrón detectado por cantidad y nombre
async def handle_response_by_quantity(update: Update, patterns, handler_function):
    message = update.message.text.lower()
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            try:
                # Extraer la cantidad y el nombre del producto
                product_quantity = int(match.group(1).strip())
                product_name = match.group(2).strip().title()

                logger.info(f"Product quantity extracted: {product_quantity}")
                logger.info(f"Product name extracted: {product_name}")

                # Crear un objeto de consulta simulado para la función del controlador
                fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})

                # Llamar a la función del controlador con la consulta simulada
                await handler_function(fake_query, product_name, product_quantity)
                return True
            except ValueError:
                logger.error(f"Cantidad no válida extraída: {match.group(1)}")
                await update.message.reply_text("Por favor, proporciona una cantidad válida.")
                return True
        else:
            logger.info("Tu mensaje está siendo revisado...")
    return False


# Función para manejar la respuesta basada en el patrón detectado por cantidad
async def handle_response_by_quantityofproduct(update: Update, patterns, handler_function):
    message = update.message.text.lower()
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            try:
                product_name = match.group(1).strip().title()
                logger.info(f"Product name extracted: {product_name}")
                fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
                await handler_function(fake_query, product_name)
                return True
            except IndexError:
                logger.error("No such group in pattern matching")
                continue
        else:
            logger.info("Tu mensaje está siendo revisado...")
    return False


# Función para manejar la respuesta basada en el patrón detectado por precio
async def handle_response_by_price(update: Update, patterns, handler_function):
    message = update.message.text.lower()
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            try:
                product_name = match.group(1).strip().title()
                logger.info(f"Product name extracted: {product_name}")
                fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
                await handler_function(fake_query, product_name)
                return True
            except IndexError:
                logger.error("No such group in pattern matching")
                continue
        else:
            logger.info("Tu mensaje está siendo revisado...")
    return False


# Manejador de mensajes de texto
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja los mensajes de texto entrantes de los usuarios."""
    user_message = update.message.text.lower()  # Convertir a minúsculas para coincidencia de patrones
    logger.info(f"Received message from user: {user_message}")

    # Verificar si el mensaje coincide con los patrones de salida
    if match_pattern(EXIT_PATTERNS, user_message):
        await exit_chat(update, context)
        return

    # Diccionario para mapear patrones a funciones de manejo
    pattern_handlers = [
        (MENU_PATTERNS, show_categories),
        (MOST_ORDERED_PRODUCT_PATTERNS, show_most_ordered_product),
        (MOST_SOLD_DRINK_PATTERNS, show_most_sold_drink),
        (MOST_SOLD_SPORT_DRINK_PATTERNS, show_most_sold_sport_drink),
        (MOST_SOLD_BREAKFAST_PATTERNS, show_most_sold_breakfast),
        (MOST_SOLD_STARTER_PATTERNS, show_most_sold_starter),
        (MOST_SOLD_SECOND_COURSE_PATTERNS, show_most_sold_second),
        (MOST_SOLD_SNACK_PATTERNS, show_most_sold_snack),
        (RECOMMEND_PRODUCT_PATTERNS["drink"], recommend_drink_by_price),
        (RECOMMEND_PRODUCT_PATTERNS["sport_drink"], recommend_sport_drink_by_price),
        (RECOMMEND_PRODUCT_PATTERNS["breakfast"], recommend_breakfast_by_price),
        (RECOMMEND_PRODUCT_PATTERNS["starter"], recommend_starter_by_price),
        (RECOMMEND_PRODUCT_PATTERNS["second_course"], recommend_second_by_price),
        (RECOMMEND_PRODUCT_PATTERNS["snack"], recommend_snack_by_price),
        (RECOMMEND_PRODUCT_PATTERNS["main"], show_most_sold_main)
    ]

    # Verificar y manejar cada patrón
    for patterns, handler_function in pattern_handlers:
        if await handle_response(update, patterns, handler_function):
            return

    # Diccionario para mapear patrones a funciones de manejo por nombre
    pattern_handlersbyname = [
        (PRODUCT_BY_NAME_PATTERN, show_product_by_name),
    ]
    # Verificar y manejar unicamente el patrón de productos por nombre
    for patterns, handler_function in pattern_handlersbyname:
        if await handle_response_by_name(update, patterns, handler_function):
            return

    # Diccionario para mapear patrones a funciones de manejo por cantidad
    pattern_handlersbyquantity = [
        (PRODUCT_ORDER_PATTERN, show_product_stock_by_name)
    ]
    # Verificar y manejar unicamente el patrón de productos por cantidad
    for patterns, handler_function in pattern_handlersbyquantity:
        if await handle_response_by_quantity(update, patterns, handler_function):
            return

    # Diccionario para mapear patrones a funciones de manejo por cantidad
    pattern_handlersbyquantityofproduct = [
        (PRODUCT_QUANTITY_PATTERN, show_product_stock_by_productname)
    ]

    # Verificar y manejar unicamente el patrón de productos por cantidad
    for patterns, handler_function in pattern_handlersbyquantityofproduct:
        if await handle_response_by_quantityofproduct(update, patterns, handler_function):
            return

    # Diccionario para mapear patrones a funciones de manejo por precio
    pattern_handlersbyprice = [
        (PRODUCT_PRICE_PATTERN, show_product_price_by_name)
    ]

    # Verificar y manejar unicamente el patrón de productos por precio
    for patterns, handler_function in pattern_handlersbyprice:
        if await handle_response_by_name(update, patterns, handler_function):
            return

    # Obtener el historial de la conversación
    chat_id = update.message.chat_id
    if "conversation_history" not in context.chat_data:
        context.chat_data["conversation_history"] = []

    # Añadir el mensaje del usuario al historial
    context.chat_data["conversation_history"].append({"role": "user", "content": user_message})

    # Construir el historial de mensajes para el modelo
    messages = [system_context] + context.chat_data["conversation_history"]

    try:
        # Enviar el historial de mensajes al modelo GPT-3.5-turbo para obtener una respuesta
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        # Extraer el contenido de la respuesta de GPT-3.5-turbo
        gpt_response = response.choices[0].message['content'].strip()

        # Añadir la respuesta del asistente al historial
        context.chat_data["conversation_history"].append({"role": "assistant", "content": gpt_response})

        # Enviar la respuesta de vuelta al usuario
        await update.message.reply_text(gpt_response)
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        await update.message.reply_text("Lo siento, algo salió mal al procesar tu solicitud.")
