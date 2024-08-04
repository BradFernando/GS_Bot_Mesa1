import multiprocessing
from app.telegram_bot import run_bot
from app.start_fastapi import start_fastapi

if __name__ == "__main__":
    # Iniciar FastAPI en un proceso separado
    fastapi_process = multiprocessing.Process(target=start_fastapi)
    fastapi_process.start()

    # Ejecutar el bot de Telegram en el proceso principal
    run_bot()

    # Esperar a que FastAPI termine (opcional)
    fastapi_process.join()
