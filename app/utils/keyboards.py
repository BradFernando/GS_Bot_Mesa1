from sqlalchemy import func
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from app.database import SessionLocal
from app.models import Category, Product, OrderProducts
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)


def get_otros_keyboard() -> InlineKeyboardMarkup:
    """Returns the keyboard for 'Preguntas acerca del Bot'."""
    keyboard = [
        [InlineKeyboardButton("¿Cuánto tiempo demora en llegar mi pedido? ⏳", callback_data="tiempo_pedido")],
        [InlineKeyboardButton("¿Cuál es el producto más pedido de este establecimiento? 📊",
                              callback_data="producto_mas_pedido")],
        [InlineKeyboardButton("Puse mal una orden ¿Qué puedo hacer? 😬❓", callback_data="orden_mal")],
        [InlineKeyboardButton("El aplicativo no abre. 😖", callback_data="app_no_abre")],
        [InlineKeyboardButton("Sobre la información Proporcionada 🤔:", callback_data="info_proporcionada")],
        [InlineKeyboardButton("Regresar al Inicio ↩", callback_data="return_start")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Consulta para obtener todas las categorías
async def show_categories(query: Update.callback_query):
    """Fetches categories from the database and shows them as inline buttons."""
    logger.info("Fetching categories from the database")
    async with SessionLocal() as session:
        async with session.begin():
            categories = (await session.execute(select(Category))).scalars().all()
            logger.info(f"Found categories: {categories}")

    if not categories:
        await query.edit_message_text(text="No hay categorías disponibles.")
        return

    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(category.name, callback_data=f"category_{category.id}")])

    keyboard.append([InlineKeyboardButton("Regresar al Inicio ↩", callback_data="return_start")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Selecciona una categoría:", reply_markup=reply_markup)


# Consulta para obtener los productos de una categoría
async def show_products(query, category_id):
    async with SessionLocal() as session:
        async with session.begin():
            products = (await session.execute(select(Product).where(Product.categoryId == category_id))).scalars().all()

    if not products:
        await query.edit_message_text(text="No hay productos disponibles en esta categoría.")
        return

    keyboard = []
    for product in products:
        keyboard.append(
            [InlineKeyboardButton(f"{product.name} - ${product.price}", callback_data=f"product_{product.id}")])

    keyboard.append([InlineKeyboardButton("Regresar a Categorías ↩", callback_data="return_categories")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Selecciona un producto:", reply_markup=reply_markup)


# Consulta para obtener el producto más pedido u ordenado
async def show_most_ordered_product(query: Update.callback_query) -> None:
    """Fetches and shows the most ordered product."""
    logger.info("Fetching the most ordered product")
    async with SessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                select(Product)
                .join(OrderProducts)
                .group_by(Product.id)
                .order_by(func.count(OrderProducts.id).desc())
                .limit(1)
            )
            most_ordered_product = result.scalars().first()
            logger.info(f"Most ordered product: {most_ordered_product}")

    if most_ordered_product:
        price = f"{most_ordered_product.price:.2f}"  # Format price to 2 decimal places
        response = f"El producto más pedido es {most_ordered_product.name} a un precio de ${price}."
    else:
        response = "No se encontró información sobre el producto más pedido."

    keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=response, reply_markup=reply_markup)


# Consulta para obtener el producto más vendido de una categoría
async def get_most_sold_product(category_id: int):
    async with SessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                select(Product, func.sum(OrderProducts.quantity).label('total_quantity'))
                .join(OrderProducts)
                .where(Product.categoryId == category_id)
                .group_by(Product.id)
                .order_by(func.sum(OrderProducts.quantity).desc())
                .limit(1)
            )
            most_sold_product = result.first()
    return most_sold_product


# Consulta para obtener la bebida más vendida
async def show_most_sold_drink(query: Update.callback_query) -> None:
    """Fetches and shows the most sold drink."""
    logger.info("Fetching the most sold drink")
    bebidas_category_id = 1
    try:
        most_sold_drink = await get_most_sold_product(bebidas_category_id)

        if most_sold_drink:
            product, total_quantity = most_sold_drink
            price = f"{product.price:.2f}"  # Formato del precio a dos decimales
            response = f"La bebida más vendida es {product.name} con {total_quantity} ventas a un precio de ${price}."
        else:
            response = "No se encontró información sobre la bebida más vendida."

        keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=response, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error en show_most_sold_drink: {e}")
        await query.edit_message_text(text="Ocurrió un error al obtener la bebida más vendida.")


# Consulta para obtener la bebida deportiva más vendida
async def show_most_sold_sport_drink(query: Update.callback_query) -> None:
    """Fetches and shows the most sold sport drink."""
    logger.info("Fetching the most sold sport drink")
    bebidas_deportivas_category_id = 2
    most_sold_sport_drink = await get_most_sold_product(bebidas_deportivas_category_id)

    if most_sold_sport_drink:
        product, total_quantity = most_sold_sport_drink
        price = f"{product.price:.2f}"  # Formato del precio a dos decimales
        response = f"La bebida deportiva más vendida es {product.name} con {total_quantity} ventas a un precio de ${price}."
    else:
        response = "No se encontró información sobre la bebida deportiva más vendida."

    keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=response, reply_markup=reply_markup)


# Consulta para obtener el desayuno más vendido
async def show_most_sold_breakfast(query: Update.callback_query) -> None:
    """Fetches and shows the most sold breakfast."""
    logger.info("Fetching the most sold breakfast")
    desayunos_category_id = 3
    most_sold_breakfast = await get_most_sold_product(desayunos_category_id)

    if most_sold_breakfast:
        product, total_quantity = most_sold_breakfast
        price = f"{product.price:.2f}"  # Formato del precio a dos decimales
        response = f"El desayuno más vendido es {product.name} con {total_quantity} ventas a un precio de ${price}."
    else:
        response = "No se encontró información sobre el desayuno más vendido."

    keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=response, reply_markup=reply_markup)


# Consulta para obtener la entrada más vendida
async def show_most_sold_starter(query: Update.callback_query) -> None:
    """Fetches and shows the most sold starter."""
    logger.info("Fetching the most sold starter")
    entradas_category_id = 4
    most_sold_starter = await get_most_sold_product(entradas_category_id)

    if most_sold_starter:
        product, total_quantity = most_sold_starter
        price = f"{product.price:.2f}"  # Formato del precio a dos decimales
        response = f"La entrada más vendida es {product.name} con {total_quantity} ventas a un precio de ${price}."
    else:
        response = "No se encontró información sobre la entrada más vendida."

    keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=response, reply_markup=reply_markup)


# Consulta para obtener el segundo más vendido
async def show_most_sold_second(query: Update.callback_query) -> None:
    """Fetches and shows the most sold second."""
    logger.info("Fetching the most sold second")
    segundos_category_id = 5
    most_sold_second = await get_most_sold_product(segundos_category_id)

    if most_sold_second:
        product, total_quantity = most_sold_second
        price = f"{product.price:.2f}"  # Formato del precio a dos decimales
        response = f"El segundo más vendido es {product.name} con {total_quantity} ventas a un precio de ${price}."
    else:
        response = "No se encontró información sobre el segundo más vendido."

    keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=response, reply_markup=reply_markup)


# Consulta para obtener el snack más vendido
async def show_most_sold_snack(query: Update.callback_query) -> None:
    """Fetches and shows the most sold snack."""
    logger.info("Fetching the most sold snack")
    snacks_category_id = 6
    most_sold_snack = await get_most_sold_product(snacks_category_id)

    if most_sold_snack:
        product, total_quantity = most_sold_snack
        price = f"{product.price:.2f}"  # Formato del precio a dos decimales
        response = f"El snack mas vendido es {product.name} con {total_quantity} ventas a un precio de ${price}."
    else:
        response = "No se encontró información sobre los snacks más vendidos."

    keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=response, reply_markup=reply_markup)


# Consulta para obtener el producto más económico de una categoría
async def get_cheapest_product(category_id: int) -> Product:
    """Consulta para obtener el producto más económico de una categoría."""
    async with SessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                select(Product)
                .where(Product.categoryId == category_id)
                .order_by(Product.price.asc())  # Ordena por precio ascendente
                .limit(1)
            )
            cheapest_product = result.scalar_one_or_none()
    return cheapest_product


# Consulta para obtener el producto más económico de la categoría de bebidas
async def recommend_drink_by_price(query: Update.callback_query) -> None:
    """Fetches and shows the cheapest drink."""
    logger.info("Fetching the cheapest drink")
    bebidas_category_id = 1
    cheapest_drink = await get_cheapest_product(bebidas_category_id)

    if cheapest_drink:
        price = f"{cheapest_drink.price:.2f}"  # Formato del precio a dos decimales
        response = f"Te recomendamos la bebida más económica, es {cheapest_drink.name} a un precio de ${price}."
    else:
        response = "No se encontró información sobre la bebida más económica."

    keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=response, reply_markup=reply_markup)


# Consulta para obtener el producto más económico de la categoría de bebidas deportivas
async def recommend_sport_drink_by_price(query: Update.callback_query) -> None:
    """Fetches and shows the cheapest sport drink."""
    logger.info("Fetching the cheapest sport drink")
    bebidas_deportivas_category_id = 2
    cheapest_sport_drink = await get_cheapest_product(bebidas_deportivas_category_id)

    if cheapest_sport_drink:
        price = f"{cheapest_sport_drink.price:.2f}"  # Formato del precio a dos decimales
        response = f"Te recomendamos la bebida deportiva más económica, es {cheapest_sport_drink.name} a un precio de ${price}."
    else:
        response = "No se encontró información sobre la bebida deportiva más económica."

    keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=response, reply_markup=reply_markup)


# Consulta para obtener el producto más económico de la categoría de desayunos
async def recommend_breakfast_by_price(query: Update.callback_query) -> None:
    """Fetches and shows the cheapest breakfast."""
    logger.info("Fetching the cheapest breakfast")
    desayunos_category_id = 3
    cheapest_breakfast = await get_cheapest_product(desayunos_category_id)

    if cheapest_breakfast:
        price = f"{cheapest_breakfast.price:.2f}"  # Formato del precio a dos decimales
        response = f"Te recomendamos el desayuno más económico, es {cheapest_breakfast.name} a un precio de ${price}."
    else:
        response = "No se encontró información sobre el desayuno más económico."

    keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=response, reply_markup=reply_markup)


# Consulta para obtener el producto más económico de la categoría de entradas
async def recommend_starter_by_price(query: Update.callback_query) -> None:
    """Fetches and shows the cheapest starter."""
    logger.info("Fetching the cheapest starter")
    entradas_category_id = 4
    cheapest_starter = await get_cheapest_product(entradas_category_id)

    if cheapest_starter:
        price = f"{cheapest_starter.price:.2f}"  # Formato del precio a dos decimales
        response = f"Te recomendamos la entrada más económica, es {cheapest_starter.name} a un precio de ${price}."
    else:
        response = "No se encontró información sobre la entrada más económica."

    keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=response, reply_markup=reply_markup)


# Consulta para obtener el producto más económico de la categoría de segundos
async def recommend_second_by_price(query: Update.callback_query) -> None:
    """Fetches and shows the cheapest second."""
    logger.info("Fetching the cheapest second")
    segundos_category_id = 5
    cheapest_second = await get_cheapest_product(segundos_category_id)

    if cheapest_second:
        price = f"{cheapest_second.price:.2f}"  # Formato del precio a dos decimales
        response = f"Te recomendamos el segundo más económico, es {cheapest_second.name} a un precio de ${price}."
    else:
        response = "No se encontró información sobre el segundo más económico."

    keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=response, reply_markup=reply_markup)


# Consulta para obtener el producto más económico de la categoría de snacks
async def recommend_snack_by_price(query: Update.callback_query) -> None:
    """Fetches and shows the cheapest snack."""
    logger.info("Fetching the cheapest snack")
    snacks_category_id = 6
    cheapest_snack = await get_cheapest_product(snacks_category_id)

    if cheapest_snack:
        price = f"{cheapest_snack.price:.2f}"  # Formato del precio a dos decimales
        response = f"Te recomendamos el snack más económico, es {cheapest_snack.name} a un precio de ${price}."
    else:
        response = "No se encontró información sobre el snack más económico."

    keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=response, reply_markup=reply_markup)


# Consulta para obtener el producto más económico de la categoría de snacks
async def show_most_sold_main(query: Update.callback_query) -> None:
    """Fetches and shows the most sold main."""
    logger.info("Fetching the most sold main")
    entradas_category_id = 4
    segundos_category_id = 5

    most_sold_starter = await get_most_sold_product(entradas_category_id)
    most_sold_second = await get_most_sold_product(segundos_category_id)

    if most_sold_starter and most_sold_second:
        starter_product, starter_quantity = most_sold_starter
        second_product, second_quantity = most_sold_second

        starter_price = f"{starter_product.price:.2f}"
        second_price = f"{second_product.price:.2f}"

        response = (
            f"Nuestro plato mas solicitado el siguiente:\n"
            f"- Como entrada tenemos {starter_product.name} con {starter_quantity} ventas a un precio de ${starter_price}.\n"
            f"- Y te ofrecemos de segundo: {second_product.name} con {second_quantity} ventas a un precio de ${second_price}."
        )
    else:
        response = "No se encontró información sobre el plato más vendido."

    keyboard = [[InlineKeyboardButton("Regresar a las Preguntas ↩", callback_data="return_otros")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=response, reply_markup=reply_markup)


