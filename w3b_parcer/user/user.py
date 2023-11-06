import sys
import telethon
import os
import time
import json
from telethon import TelegramClient, events
import logging
import asyncio
from telethon.tl.functions.channels import JoinChannelRequest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Путь к файлу сессии
session_file_name = 'user_session.session'
session_file_path = os.path.join(ROOT_DIR, session_file_name)

# Проверяем наличие файла сессии
if not os.path.exists(session_file_path):
    # Файла нет, создаем новую сессию
    client_user = TelegramClient('user_session', API_ID, API_HASH)
else:
    # Файл сессии существует, используем его для создания клиента
    client_user = TelegramClient(session_file_path, API_ID, API_HASH)



last_message_ids = load_last_message_ids()
logger.info(f"Загруженные последние ID сообщений при старте: {last_message_ids}")

def contains_keywords(text):
    with open(os.path.join(ROOT_DIR, "keywords.txt"), "r", encoding="utf-8") as file:
        keywords = [kw.strip().lower() for kw in file.readlines()]
    return any(keyword in text.lower() for keyword in keywords)


async def monitor_channels():
    while True:
        with open(os.path.join(ROOT_DIR, "watch.txt"), "r", encoding="utf-8") as file:
            channels = file.readlines()
            logger.info(f"Загруженные последние ID сообщений из файла: {last_message_ids}")

        for channel in channels:
            channel_id, channel_name, status = channel.strip().split(" : ")
            if not channel_id.startswith("-100"):
                channel_id = "-100" + channel_id

            last_id = last_message_ids.get(channel_id, 0)
            max_id = last_id

            try:
                async for message in client_user.iter_messages(int(channel_id), min_id=last_id + 1):
                    # Пропустить служебные сообщения
                    if isinstance(message, telethon.tl.patched.MessageService):
                        continue

                    if status == "all":
                        await client_user.forward_messages(MY_CHANNEL_ID, message)
                        logger.info(f"Пересылаем сообщение с ID {message.id} из канала {channel_id}")
                    elif status == "kwd" and message.text:
                        logger.info(f"Проверка сообщения с ID {message.id} из канала {channel_id} на наличие ключевых слов")
                        if contains_keywords(message.text):
                            await client_user.forward_messages(MY_CHANNEL_ID, message)
                            logger.info(f"Пересылаем сообщение с ID {message.id} из канала {channel_id} по ключевым словам")
                        else:
                            logger.info(f"Сообщение с ID {message.id} из канала {channel_id} не содержит ключевых слов")

                    if message.id > max_id:
                        max_id = message.id

                if max_id > last_id:
                    logger.info(f"Обновление ID для канала {channel_id} с {last_id} на {max_id}")
                    last_message_ids[channel_id] = max_id
                    save_last_message_ids()
                    logger.info(f"Обновленный ID для канала {channel_id}: {max_id}")

            except Exception as e:
                if "A wait of" in str(e) and "is required" in str(e):
                    wait_time = int(str(e).split(" ")[3]) + 5  # извлекаем время ожидания и добавляем 5 секунд на всякий случай
                    logger.warning(f"Ожидание {wait_time} секунд из-за ограничений Telegram API...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Ошибка при обработке канала {channel_id}: {e}")

        await asyncio.sleep(30)



async def join_channels_from_file():
    while True:
        if not os.path.exists(os.path.join(ROOT_DIR, "channels_to_join.txt")):
            await asyncio.sleep(60)
            continue

        with open(os.path.join(ROOT_DIR, "channels_to_join.txt"), "r", encoding="utf-8") as file:
            channels = file.readlines()

        if channels:
            for channel in channels:
                try:
                    await client_user(JoinChannelRequest(channel.strip()))
                    logger.info(f"Успешно вступил в канал {channel.strip()}")
                    await get_user_channels()
                    await client_user.send_message(YOUR_USER_ID, f"Успешно вступил в канал {channel.strip()}")
                except Exception as e:
                    logger.error(f"Ошибка при вступлении в канал {channel.strip()}: {e}")
                    await client_user.send_message(YOUR_USER_ID, f"Ошибка при вступлении в канал {channel.strip()}: {e}")

            with open(os.path.join(ROOT_DIR, "channels_to_join.txt"), "w", encoding="utf-8") as file:
                file.write("")

        await asyncio.sleep(60)

if __name__ == "__main__":
    logger.info("Мониторинг каналов и вступление в каналы начато...")
    client_user.start()
    client_user.loop.run_until_complete(get_user_channels())
    client_user.loop.create_task(monitor_channels())
    client_user.loop.run_until_complete(join_channels_from_file())
    client_user.loop.run_forever()
