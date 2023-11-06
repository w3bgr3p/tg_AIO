from telegram import Update, Bot, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Функция для обработки команды /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Отправь мне токен/ы, каждый с новой строки')

# Helper function to escape markdown characters
def escape_markdown(text):
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

# Функция для обработки полученного текстового сообщения
def wrap_tokens(update: Update, context: CallbackContext) -> None:
    tokens = update.message.text.split('\n')  # Разделяем сообщение на строки

    wrapped_tokens = []
    for token in tokens:
        # Шаблон, в который будет вставлен токен
        wrapped_token_template = """
function login(token) {
    setInterval(() => {
        document.body.appendChild(document.createElement `iframe`).contentWindow.localStorage.token = `"${token}"`
    }, 50);
    setTimeout(() => {
        location.reload();
    }, 2500);
}
    login('TOKEN');"""

        # Заменяем 'TOKEN' на фактический токен пользователя
        wrapped_token = wrapped_token_template.replace('TOKEN', token)
        wrapped_tokens.append(wrapped_token)

    # Отправляем обернутые токены, используя форматирование monospace в Telegram
    for wrapped_token in wrapped_tokens:
        update.message.reply_text(f'```{escape_markdown(wrapped_token)}```', parse_mode=ParseMode.MARKDOWN_V2)

# Основная функция для запуска бота
def main() -> None:
    # Создаем бота с использованием токена
    bot_token = 'TG_TOKEN'
    updater = Updater(token=bot_token, use_context=True)

    # Получаем диспетчера для регистрации обработчиков
    dispatcher = updater.dispatcher

    # Регистрируем обработчики команд
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, wrap_tokens))

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
