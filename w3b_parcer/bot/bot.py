import sys
import os
from telethon import TelegramClient, events
import re
import logging
from telethon.tl.functions.channels import JoinChannelRequest

# Добавляем путь к родительскому каталогу в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Определите ROOT_DIR как путь к каталогу вашего проекта
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from settings import API_ID, API_HASH, MY_CHANNEL_ID, YOUR_USER_ID, BOT_TOKEN

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client_bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Функция для определения типа введенных данных
def get_input_type(user_input):
    if re.match(r"^\d+$", user_input):
        return "ID"
    elif user_input.startswith("@"):
        return "USERNAME"
    elif user_input.startswith("https://t.me/"):
        return "LINK"
    else:
        return None

# Функция для добавления ключевых слов в keywords.txt
def add_keywords(keywords):
    with open(os.path.join(ROOT_DIR, "keywords.txt"), "r") as file:
        existing_keywords = file.readlines()
    existing_keywords = [kw.strip() for kw in existing_keywords]
    with open(os.path.join(ROOT_DIR, "keywords.txt"), "a") as file:
        for keyword in keywords:
            if keyword not in existing_keywords:
                file.write(f"{keyword}\n")

# Функция для сохранения данных в watch.txt
def save_to_watch_file(channel_id, username):
    with open(os.path.join(ROOT_DIR, "watch.txt"), "a") as file:
        file.write(f"{channel_id} : {username} : kwd\n")

# Функция для проверки, содержит ли текст ключевые слова
def contains_keywords(text):
    with open(os.path.join(ROOT_DIR, "keywords.txt"), "r") as file:
        keywords = [kw.strip() for kw in file.readlines()]
    return any(keyword in text for keyword in keywords)

# Функция для удаления канала из watch.txt
def remove_channel(data):
    with open(os.path.join(ROOT_DIR, "watch.txt"), "r") as file:
        channels = file.readlines()
    with open(os.path.join(ROOT_DIR, "watch.txt"), "w") as file:
        for channel in channels:
            if data not in channel:
                file.write(channel)

# Функция для удаления ключевого слова из keywords.txt
def remove_keyword(keyword):
    with open(os.path.join(ROOT_DIR, "keywords.txt"), "r") as file:
        keywords = file.readlines()
    with open(os.path.join(ROOT_DIR, "keywords.txt"), "w") as file:
        for kw in keywords:
            if kw.strip() != keyword:
                file.write(kw)

def read_user_channels():
    with open(os.path.join(ROOT_DIR, "user_channels.txt"), "r", encoding="utf-8") as file:
        channels = [line.strip() for line in file.readlines()]
    return channels


# Асинхронные функции для обработки ввода
async def handle_id(channel_id):
    entity = await client_bot.get_entity(int(channel_id))
    username = entity.username if entity.username else "Неизвестно"
    save_to_watch_file(channel_id, username)

async def handle_username(username):
    try:
        entity = await client_bot.get_entity(username)
        channel_id = entity.id
        save_to_watch_file(channel_id, username)
    except Exception as e:
        logger.error(f"Ошибка при обработке username {username}: {e}")

async def handle_link(link):
    username = link.split("/")[-1]
    if not username.startswith("@"):
        username = "@" + username
    await handle_username(username)

async def get_channel_id_from_input(user_input):
    input_type = get_input_type(user_input)
    if input_type == "ID":
        return user_input
    elif input_type == "USERNAME":
        entity = await client_bot.get_entity(user_input)
        return str(entity.id)
    elif input_type == "LINK":
        username = user_input.split("/")[-1]
        if not username.startswith("@"):
            username = "@" + username
        entity = await client_bot.get_entity(username)
        return str(entity.id)
    else:
        return None

async def join_to_channel(channel_link_or_username):
    try:
        await client_bot(JoinChannelRequest(channel_link_or_username))
        logger.info(f"Успешно вступил в {channel_link_or_username}")
    except Exception as e:
        logger.error(f"Ошибка при вступлении в {channel_link_or_username}: {e}")
        
async def send_bot_message(text):
    await client_bot.send_message(YOUR_USER_ID, text)


@client_bot.on(events.NewMessage(pattern='/change_status'))
async def change_status_command(event):
    args = event.text.split()
    if len(args) != 3:
        await event.respond("Используйте формат: `/change_status {имя канала} {off/kwd/all}`")
        return

    channel_input, status = args[1], args[2]
    if status not in ['off', 'kwd', 'all']:
        await event.respond("Неверный статус. Допустимые статусы: off, kwd, all.")
        return

    channel_id = await get_channel_id_from_input(channel_input)
    if not channel_id:
        await event.respond("Неверный формат канала.")
        return

    with open(os.path.join(ROOT_DIR, "watch.txt"), "r") as file:
        lines = file.readlines()

    found = False
    for i, line in enumerate(lines):
        if line.startswith(channel_id):
            lines[i] = f"{channel_id} : {channel_input} : {status}\n"
            found = True
            break

    if not found:
        await event.respond("Канал не найден в списке.")
        return

    with open(os.path.join(ROOT_DIR, "watch.txt"), "w") as file:
        file.writelines(lines)

    await event.respond(f"Статус канала {channel_input} изменен на {status}.")

@client_bot.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    await event.respond(
        'w3bparcer manager v0.3\n'
        '- Добавить канал: `/add_chan` + ID, @username или ссылка\n'
        '- Удалить канал: `/rm_chan` + ID, @username или ссылка\n'
        '- Просмотреть список каналов для отслеживания: `/view_channels`\n'
        '- Изменить статус отслеживания канала: `/change_status {имя канала} {off/kwd/all}`\n'
        '- Добавить ключевые слова: `/add_keywords` + слова\n'
        '- Удалить ключевые слова: `/rm_kwd` + слова\n'
        '- Просмотреть ключевые слова: `/view_keywords`\n'
        '- Просмотреть каналы парсера: `/read_user_channels`\n'
        '- Вступить в канал: `/join` + @username или ссылка'
    )

    
@client_bot.on(events.NewMessage(pattern='/add_chan'))
async def add_chan_command(event):
    user_input = event.text.split(maxsplit=1)
    if len(user_input) < 2:
        await event.respond("Пожалуйста, укажите ID, @username или ссылку на канал после команды. Например, `/add_chan @channelname`.")
        return
    user_input = user_input[1].strip()
    input_type = get_input_type(user_input)
    if input_type == "ID":
        await handle_id(user_input)
    elif input_type == "USERNAME":
        await handle_username(user_input)
    elif input_type == "LINK":
        await handle_link(user_input)
    else:
        await event.respond("Неверный формат ввода. Пожалуйста, введите корректный ID, @username или ссылку.")
        return
    await event.respond(f"Добавлено: {user_input}")

@client_bot.on(events.NewMessage(pattern='/add_keywords'))
async def add_keywords_command(event):
    message = event.text.split()
    if len(message) > 1:
        keywords = message[1:]
        add_keywords(keywords)
        await event.respond(f"Ключевые слова добавлены: {', '.join(keywords)}")
    else:
        await event.respond("Пожалуйста, укажите ключевые слова после команды. Например, `/add_keywords слово1 слово2`.")

@client_bot.on(events.NewMessage(pattern='/view_keywords'))
async def view_keywords_command(event):
    with open(os.path.join(ROOT_DIR, "keywords.txt"), "r") as file:
        keywords = file.readlines()
    if keywords:
        await event.respond(f"Текущие ключевые слова: {', '.join(keywords)}")
    else:
        await event.respond("Ключевые слова отсутствуют.")

@client_bot.on(events.NewMessage(pattern='/rm_chan'))
async def rm_chan_command(event):
    user_input = event.text.split(maxsplit=1)
    if len(user_input) < 2:
        await event.respond("Пожалуйста, укажите ID, @username или ссылку на канал после команды. Например, `/rm_chan @channelname`.")
        return
    user_input = user_input[1].strip()
    remove_channel(user_input)
    await event.respond(f"Удалено (если было в списке): {user_input}")

@client_bot.on(events.NewMessage(pattern='/rm_kwd'))
async def rm_kwd_command(event):
    user_input = event.text.split(maxsplit=1)
    if len(user_input) < 2:
        await event.respond("Пожалуйста, укажите ключевое слово после команды. Например, `/rm_kwd слово1`.")
        return
    keyword = user_input[1].strip()
    remove_keyword(keyword)
    await event.respond(f"Удалено (если было в списке): {keyword}")

@client_bot.on(events.NewMessage(pattern='/view_channels'))
async def view_channels_command(event):
    with open(os.path.join(ROOT_DIR, "watch.txt"), "r") as file:
        channels = file.readlines()
    if channels:
        await event.respond(f"Текущие каналы:\n{''.join(channels)}")
    else:
        await event.respond("Каналы отсутствуют.")

@client_bot.on(events.NewMessage(pattern='/join'))
async def join_command(event):
    channel_to_join = event.text.split(maxsplit=1)
    if len(channel_to_join) < 2:
        await event.respond("Пожалуйста, укажите @username или ссылку на канал после команды. Например, `/join @channelname`.")
        return
    channel_to_join = channel_to_join[1].strip()
    
    # Запись канала в файл
    with open(os.path.join(ROOT_DIR, "channels_to_join.txt"), "a") as file:
        file.write(f"{channel_to_join}\n")
    
    await event.respond(f"Запрос на вступление в канал {channel_to_join} отправлен.")

@client_bot.on(events.NewMessage(pattern='/read_user_channels'))
async def read_user_channels_command(event):
    channels = read_user_channels()
    if channels:
        await event.respond("Пользовательские каналы:\n" + '\n'.join(channels))
    else:
        await event.respond("Пользовательские каналы отсутствуют.")

        
if __name__ == "__main__":
    logger.info("Бот запущен...")
    client_bot.run_until_disconnected()
