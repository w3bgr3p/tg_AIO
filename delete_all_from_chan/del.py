from telethon.sync import TelegramClient
from telethon.sessions import StringSession

TOKEN = 'TOKEN'
CHANNEL_ID = '@chanel'
# Введите свой API_ID и API_HASH
API_ID = XXXXXXXX
API_HASH = 'xxxxxxxxxxxxxxxxxx'
 # Замените на имя вашего канала

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    for message in client.iter_messages(CHANNEL_ID):
        print(f"Deleting message with ID: {message.id}")
        client.delete_messages(CHANNEL_ID, message.id)

print("All messages deleted.")
