import sys
import os
import json
from telethon import TelegramClient, events
import logging
import asyncio
from telethon.tl.functions.channels import JoinChannelRequest
# Добавляем путь к родительскому каталогу в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Определите ROOT_DIR как путь к каталогу вашего проекта
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from settings import API_ID, API_HASH, MY_CHANNEL_ID, YOUR_USER_ID, BOT_TOKEN

def save_last_message_ids():
    with open(os.path.join(ROOT_DIR, "last_message_ids.json"), "w", encoding="utf-8") as file:
        json.dump(last_message_ids, file)

def load_last_message_ids():
    if os.path.exists(os.path.join(ROOT_DIR, "last_message_ids.json")):
        with open(os.path.join(ROOT_DIR, "last_message_ids.json"), "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

async def get_user_channels():
    channels = []
    async for dialog in client_user.iter_dialogs():
        if dialog.is_channel:
            channels.append(dialog.name)
    with open(os.path.join(ROOT_DIR, "user_channels.txt"), "w", encoding="utf-8") as file:
        for channel in channels:
            file.write(f"{channel}\n")


# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client_user = TelegramClient('user_session', API_ID, API_HASH)

last_message_ids = load_last_message_ids()  # словарь для хранения ID последнего пересланного сообщения для каждого канала
logger.info(f"Загруженные последние ID сообщений при старте: {last_message_ids}")

# Функция для проверки, содержит ли текст ключевые слова
def contains_keywords(text):
    with open(os.path.join(ROOT_DIR, "keywords.txt"), "r", encoding="utf-8") as file:
        keywords = [kw.strip() for kw in file.readlines()]
    return any(keyword in text for keyword in keywords)

async def monitor_channels():
    while True:
        with open(os.path.join(ROOT_DIR, "watch.txt"), "r", encoding="utf-8") as file:
            channels = file.readlines()
            logger.info(f"Загруженные последние ID сообщений из файла: {last_message_ids}")  # Переместите эту строку сюда

        for channel in channels:
            channel_id, channel_name, status = channel.strip().split(" : ")
            if not channel_id.startswith("-100"):
                channel_id = "-100" + channel_id

            last_id = last_message_ids.get(channel_id, 0)  # получаем ID последнего пересланного сообщения или 0

            try:
                max_id = 0  # переменная для хранения максимального ID сообщения в этой итерации
                async for message in client_user.iter_messages(int(channel_id), min_id=last_id + 1):  # проверяем только новые сообщения
                    if status == "all":
                        await client_user.forward_messages(MY_CHANNEL_ID, message)
                        logger.info(f"Пересылаем сообщение с ID {message.id} из канала {channel_id}")
                    elif status == "kwd" and message.text and contains_keywords(message.text):
                        await client_user.forward_messages(MY_CHANNEL_ID, message)
                    
                    # обновляем max_id, если текущий ID сообщения больше
                    if message.id > max_id:
                        logger.info(f"Обновленный ID для канала {channel_id}: {max_id}")
                        max_id = message.id

                # обновляем ID последнего пересланного сообщения для этого канала после обработки всех сообщений
                if max_id > 0:
                    last_message_ids[channel_id] = max_id
                logger.info(f"Обновленный ID для канала {channel_id}: {last_message_ids[channel_id]}")
            except Exception as e:
                logger.error(f"Ошибка при обработке канала {channel_id}: {e}")
        save_last_message_ids()
        logger.info(f"Сохраненные последние ID сообщений: {last_message_ids}")
        await asyncio.sleep(60)  # Проверяем каждую минуту

async def join_channels_from_file():
    while True:
        if not os.path.exists(os.path.join(ROOT_DIR, "channels_to_join.txt")):
            await asyncio.sleep(60)  # Пауза в 60 секунд перед следующей проверкой
            continue

        with open(os.path.join(ROOT_DIR, "channels_to_join.txt"), "r", encoding="utf-8") as file:
            channels = file.readlines()

        # Если есть каналы для вступления
        if channels:
            for channel in channels:
                try:
                    await client_user(JoinChannelRequest(channel.strip()))
                    logger.info(f"Успешно вступил в канал {channel.strip()}")
                    await get_user_channels()
                    # Отправка сообщения с результатом
                    await client_user.send_message(YOUR_USER_ID, f"Успешно вступил в канал {channel.strip()}")
                except Exception as e:
                    logger.error(f"Ошибка при вступлении в канал {channel.strip()}: {e}")
                    # Отправка сообщения с ошибкой
                    await client_user.send_message(YOUR_USER_ID, f"Ошибка при вступлении в канал {channel.strip()}: {e}")

            # Очистите файл после вступления во все каналы
            with open(os.path.join(ROOT_DIR, "channels_to_join.txt"), "w", encoding="utf-8") as file:
                file.write("")

        await asyncio.sleep(60)  # Пауза в 60 секунд перед следующей проверкой






if __name__ == "__main__":
    logger.info("Мониторинг каналов и вступление в каналы начато...")
    client_user.start()
    
    # Вызов функции при запуске
    client_user.loop.run_until_complete(get_user_channels())
    
    # Запускаем задачи напрямую через событийный цикл Telethon
    client_user.loop.create_task(monitor_channels())
    client_user.loop.run_until_complete(join_channels_from_file())
    
    # Запускаем событийный цикл непрерывно
    client_user.loop.run_forever()
