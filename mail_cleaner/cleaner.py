import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from bs4 import BeautifulSoup
import settings

# Настройка логгирования
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO)

# Создание клиента
client = TelegramClient('my_session', settings.API_ID, settings.API_HASH)
logging.info("Клиент создан")

@client.on(events.NewMessage(chats=-100xxxxxxxxxx))
async def message_handler(event):
    logging.info("Получено новое сообщение")
    
    # Получение содержимого сообщения
    message_content = event.message.text
    logging.info(f"Содержимое сообщения: {message_content}")

    # Преобразование HTML в текст с помощью BeautifulSoup
    soup = BeautifulSoup(message_content, 'html.parser')

    # Преобразование гиперссылок в формат Markdown
    for a in soup.find_all('a', href=True):
        a.replace_with(f"[{a.text if a.text else 'Link'}]({a['href']})")
    logging.info("Гиперссылки преобразованы в формат Markdown")

    # Отправка отредактированного сообщения
    await event.respond(soup.get_text(), parse_mode='md')
    logging.info("Отредактированное сообщение отправлено")

    # Удаление исходного сообщения
    await event.delete()
    logging.info("Исходное сообщение удалено")

async def main():
    async with client:
       
        # Запуск основного цикла событий
        await client.run_until_disconnected()

# Запуск асинхронной функции
import asyncio
asyncio.run(main())

