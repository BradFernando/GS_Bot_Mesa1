import os
import re
import openai
from telegram import Update
from telegram.ext import ContextTypes

from app.utils.rules import rules
from app.utils.keyboards import show_categories, show_most_ordered_product, show_most_sold_drink, \
    show_most_sold_sport_drink, show_most_sold_breakfast, show_most_sold_starter, show_most_sold_second, \
    show_most_sold_snack, recommend_drink_by_price, recommend_sport_drink_by_price, recommend_breakfast_by_price, \
    recommend_starter_by_price, recommend_second_by_price, recommend_snack_by_price, show_most_sold_main
from app.utils.logging_config import setup_logging

logger = setup_logging()

# Configurar API de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Construir el contexto del sistema dinámicamente
system_context = {
    "role": "system",
    "content": " ".join(rules)  # Une las cadenas en rules en una sola cadena
}


# Manejador de mensajes de texto
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja los mensajes de texto entrantes de los usuarios."""
    user_message = update.message.text.lower()  # Convertir a minúsculas para coincidencia de patrones
    logger.info(f"Received message from user: {user_message}")

    # Expresiones regulares para diferentes contextos
    menu_patterns = [
        r'\bmen[úu]\b',  # Detectar variaciones de "menú"
        r'\bcarta\b',  # "carta" como sinónimo de menú
        r'\bver opciones\b',  # frases como "ver opciones"
        r'\bver men[úu]',  # frases como "ver menú"
        r'\bver carta\b'  # frases como "ver carta"
    ]

    most_ordered_product_patterns = [
        r'\bproducto m[aá]s pedido\b',
        r'\borden m[aá]s pedida\b',
        r'\bproducto m[aá]s vendido\b',
        r'\borden m[aá]s vendida\b',
        r'\bcu[aá]l es el producto más pedido\b',
    ]

    most_sold_drink_patterns = [
        r'\bbebida m[aá]s vendida\b',
        r'\bbebida m[aá]s popular\b',
        r'\bbebida m[aá]s pedida\b',
        r'\bcu[aá]l es la bebida más vendida\b',
        r'\bcu[aá]l es la bebida más popular\b'
    ]

    most_sold_sport_drink_patterns = [
        r'\bbebida deportiva m[aá]s vendida\b',
        r'\bbebida deportiva m[aá]s popular\b',
        r'\bbebida deportiva m[aá]s pedida\b',
        r'\bcu[aá]l es la bebida deportiva más vendida\b',
        r'\bcu[aá]l es la bebida deportiva más popular\b'
    ]

    most_sold_breakfast_patterns = [
        r'\bdesayuno m[aá]s vendido\b',
        r'\bdesayuno m[aá]s popular\b',
        r'\bdesayuno m[aá]s pedido\b',
        r'\bcu[aá]l es el desayuno más vendido\b',
        r'\bcu[aá]l es el desayuno más popular\b'
    ]

    most_sold_starter_patterns = [
        r'\bentrada m[aá]s vendida\b',
        r'\bentrada m[aá]s popular\b',
        r'\bentrada m[aá]s pedida\b',
        r'\bcu[aá]l es la entrada más vendida\b',
        r'\bcu[aá]l es la entrada más popular\b'
    ]

    most_sold_second_course_patterns = [
        r'\bsegundo m[aá]s vendido\b',
        r'\bsegundo m[aá]s popular\b',
        r'\bsegundo m[aá]s pedido\b',
        r'\bcu[aá]l es el segundo más vendido\b',
        r'\bcu[aá]l es el segundo más popular\b'
    ]

    most_sold_snack_patterns = [
        r'\bsnack m[aá]s vendido\b',
        r'\bsnack m[aá]s popular\b',
        r'\bsnack m[aá]s pedido\b',
        r'\bcu[aá]l es el snack m[aá]s vendido\b',
        r'\bcu[aá]l es el snack m[aá]s popular\b'
    ]

    most_sold_food_patterns = [
        r'\bcomida m[aá]s vendida\b',
        r'\bcomida m[aá]s popular\b',
        r'\bcomida m[aá]s pedida\b',
        r'\bcu[aá]l es la comida más vendida\b',
        r'\bcu[aá]l es la comida más popular\b',
        r'\bcu[aá]l es la comida más pedida\b',
        r'\bcu[aá]l es el platillo más vendido\b',
        r'\bcu[aá]l es el platillo más popular\b'
        r'\bcu[aá]l es el plato más vendido\b',
        r'\bcu[aá]l es el plato más popular\b',
        r'\bcu[aá]l es el plato más pedido\b',
        r'\bqu[eé] almuerzo me recomiendas\b',
        r'\bqu[eé] almuerzo es bueno\b',
        r'\bqu[eé] almuerzo es económico\b',
    ]

    # Define patrones de recomendación para cada categoría
    recommend_product_patterns = {
        "drink": [
            r'\bbebida recomendada\b',
            r'\bqu[eé] bebida recomiendas\b',
            r'\bqu[eé] bebida me recomiendas\b',
            r'\bqu[eé] bebida es buena\b',
            r'\bqu[eé] bebida econ[oó]mica me recomiendas\b',
            r'\bqu[eé] bebida es buena y econ[oó]mica\b'
        ],
        "sport_drink": [
            r'\bbebida deportiva recomendada\b',
            r'\bqu[eé] bebida deportiva recomiendas\b',
            r'\bqu[eé] bebida deportiva me recomiendas\b',
            r'\bqu[eé] bebida deportiva es buena\b',
            r'\bqu[eé] bebida deportiva econ[oó]mica me recomiendas\b',
            r'\bqu[eé] bebida deportiva es buena y econ[oó]mica\b'
        ],
        "breakfast": [
            r'\bdesayuno recomendado\b',
            r'\bqu[eé] desayuno recomiendas\b',
            r'\bqu[eé] desayuno me recomiendas\b',
            r'\bqu[eé] desayuno es bueno\b',
            r'\bqu[eé] desayuno econ[oó]mico me recomiendas\b',
            r'\bqu[eé] desayuno es bueno y econ[oó]mico\b'
        ],
        "starter": [
            r'\bentrada recomendada\b',
            r'\bqu[eé] entrada recomiendas\b',
            r'\bqu[eé] entrada me recomiendas\b',
            r'\bqu[eé] entrada es buena\b',
            r'\bqu[eé] entrada econ[oó]mica me recomiendas\b',
            r'\bqu[eé] entrada es buena y econ[oó]mica\b'
        ],
        "second_course": [
            r'\bsegundo recomendado\b',
            r'\bqu[eé] segundo recomiendas\b',
            r'\bqu[eé] segundo me recomiendas\b',
            r'\bqu[eé] segundo es bueno\b',
            r'\bqu[eé] segundo econ[oó]mico me recomiendas\b',
            r'\bqu[eé] segundo es bueno y econ[oó]mico\b'
        ],
        "snack": [
            r'\bsnack recomendado\b',
            r'\bqu[eé] snack recomiendas\b',
            r'\bqu[eé] snack me recomiendas\b',
            r'\bqu[eé] snack es bueno\b',
            r'\bqu[eé] snack econ[oó]mico me recomiendas\b',
            r'\bqu[eé] snack es bueno y econ[oó]mico\b'
        ]
    }

    # Verificar si el mensaje del usuario pide el menú
    if any(re.search(pattern, user_message) for pattern in menu_patterns):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await show_categories(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por el producto más pedido
    if any(re.search(pattern, user_message) for pattern in most_ordered_product_patterns):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await show_most_ordered_product(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por la bebida más vendida
    if any(re.search(pattern, user_message) for pattern in most_sold_drink_patterns):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await show_most_sold_drink(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por la bebida deportiva más vendida
    if any(re.search(pattern, user_message) for pattern in most_sold_sport_drink_patterns):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await show_most_sold_sport_drink(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por el desayuno más vendido
    if any(re.search(pattern, user_message) for pattern in most_sold_breakfast_patterns):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await show_most_sold_breakfast(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por la entrada más vendida
    if any(re.search(pattern, user_message) for pattern in most_sold_starter_patterns):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await show_most_sold_starter(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por el segundo más vendido
    if any(re.search(pattern, user_message) for pattern in most_sold_second_course_patterns):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await show_most_sold_second(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por el snack más vendido
    if any(re.search(pattern, user_message) for pattern in most_sold_snack_patterns):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await show_most_sold_snack(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por una recomendación de bebida
    if any(re.search(pattern, user_message) for pattern in recommend_product_patterns["drink"]):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await recommend_drink_by_price(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por una recomendación de bebida deportiva
    if any(re.search(pattern, user_message) for pattern in recommend_product_patterns["sport_drink"]):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await recommend_sport_drink_by_price(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por una recomendación de desayuno
    if any(re.search(pattern, user_message) for pattern in recommend_product_patterns["breakfast"]):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await recommend_breakfast_by_price(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por una recomendación de entrada
    if any(re.search(pattern, user_message) for pattern in recommend_product_patterns["starter"]):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await recommend_starter_by_price(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por una recomendación de segundo
    if any(re.search(pattern, user_message) for pattern in recommend_product_patterns["second_course"]):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await recommend_second_by_price(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por una recomendación de snack
    if any(re.search(pattern, user_message) for pattern in recommend_product_patterns["snack"]):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await recommend_snack_by_price(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por la comida más vendida
    if any(re.search(pattern, user_message) for pattern in most_sold_food_patterns):
        fake_query = type('FakeQuery', (object,), {'edit_message_text': update.message.reply_text})
        await show_most_sold_main(fake_query)
        return

    # Verificar si el mensaje del usuario pregunta por una recomendación de desayuno

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
