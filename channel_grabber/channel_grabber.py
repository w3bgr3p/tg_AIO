import logging
from telethon import TelegramClient, events
from settings import API_ID, API_HASH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def get_user_channels(client):
    logging.info("Начинаем получение списка каналов...")
    channels = []
    count = 0
    async for dialog in client.iter_dialogs():
        count += 1
        if count % 100 == 0:
            logging.info(f"Обработано {count} диалогов...")
        if dialog.is_channel:
            chat_id = dialog.entity.id
            username = dialog.entity.username or "N/A"
            link = f"https://t.me/{username}" if username != "N/A" else "N/A"
            channels.append(f"-100{chat_id} : @{username} : {link}")

    logging.info(f"Найдено {len(channels)} каналов.")
    with open("channels.txt", "w", encoding="utf-8") as file:
        for channel in channels:
            file.write(f"{channel}\n")
    logging.info("Список каналов записан в файл channels.txt.")

async def main():
    logging.info("Запуск скрипта...")
    async with TelegramClient('anon', API_ID, API_HASH) as client:
        await get_user_channels(client)
    logging.info("Скрипт завершил работу.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
