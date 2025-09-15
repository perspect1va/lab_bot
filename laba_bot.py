import telebot
import requests
import csv
from datetime import datetime
from telebot import types
from secret import BOT_API_TOKEN

TELEGRAM_TOKEN = BOT_API_TOKEN
bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_states = {}

# Логирование действий
def log_to_csv(user_id, username, motion, api_name, api_answer):
    now = datetime.now()
    date = now.strftime('%Y-%m-%d')
    time = now.strftime('%H:%M:%S')
    with open("bot_log.csv", mode="a", encoding="utf-8", newline='') as file:
        writer = csv.writer(file)
        writer.writerow([user_id, f"@{username}", motion, api_name, date, time, api_answer])
# Старт
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    show_main_menu(chat_id)
# Главное меню без кнопки "Меню"
def show_main_menu(chat_id):
    keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_markup.add(types.KeyboardButton("уники"))
    keyboard_markup.add(types.KeyboardButton("коты"))
    keyboard_markup.add(types.KeyboardButton("предсказание"))
    bot.send_message(chat_id, "Добро пожаловать! Выбери действие:", reply_markup=keyboard_markup)
# Обработка медиафайлов
@bot.message_handler(content_types=['document'])
def addfile(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = message.document.file_name
        with open(f'D:\\практос\\{file_name}', 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id, f"Файл {file_name} успешно сохранён.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при сохранении файла: {e}")
# Обработка всех сообщений
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    chat_id = message.chat.id
    text = message.text.strip()
    username = message.from_user.username or "—"
    if text == "Отмена":
        user_states.pop(chat_id, None)
        show_main_menu(chat_id)
        return
    if user_states.get(chat_id) in ['awaiting_country', 'awaiting_name'] and text in ["уники", "коты", "предсказание", "Отмена"]:
        user_states.pop(chat_id, None)
    if user_states.get(chat_id) == 'awaiting_country':
        handle_country_input(message)
        return
    if user_states.get(chat_id) == 'awaiting_name':
        handle_name_input(message)
        return
    if text == "уники":
        bot.send_sticker(chat_id, "CAACAgIAAxkBAAEPVzZowVnFsoyIk_hp2LNo_zuTQGZhlgACTwADlb9JMgErK2skxYHhNgQ")
        user_states[chat_id] = 'awaiting_country'
        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(types.KeyboardButton("Отмена"))
        bot.send_message(chat_id, "Введите страну (например, Belarus):", reply_markup=cancel_markup)
        return
    elif text == "коты":
        bot.send_sticker(chat_id, "CAACAgIAAxkBAAEPVzVowVnF7O-7yOLJFZbDDSQeyWS7iQACR1QAAjvgmUkWLyWxzYb-XDYE")
        try:
            r = requests.get("https://catfact.ninja/fact")
            r.raise_for_status()
            fact = r.json().get("fact")
            bot.send_message(chat_id, f"Интересный факт о кошках:\n{fact}")
            log_to_csv(chat_id, username, "Button press", "Cat Facts", fact)
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка при получении факта: {e}")
            log_to_csv(chat_id, username, "Button press", "Cat Facts", f"Ошибка: {e}")
        return
    elif text == "предсказание":
        bot.send_sticker(chat_id, "CAACAgIAAxkBAAEPVzhowVnFChAowQqjDOXpGOZmwHiZSQACRhYAAnuI-Esn4nImywnFZzYE")
        user_states[chat_id] = 'awaiting_name'
        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(types.KeyboardButton("Отмена"))
        bot.send_message(chat_id, "Введите имя для предсказания возраста:", reply_markup=cancel_markup)
        return
    else:
        response = f'Вы написали "{text}", я не знаю такой команды.'
        bot.send_message(chat_id, response)
        log_to_csv(chat_id, username, "Keyboard typing", "NONE", "NONE")
# Университеты
def handle_country_input(message):
    chat_id = message.chat.id
    country = message.text.strip()
    url = f"http://universities.hipolabs.com/search?country={country}"
    username = message.from_user.username or "—"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if data:
            reply = f"Университеты в {country}:\n\n" + "\n".join(f"- {uni['name']}" for uni in data[:30])
            bot.send_message(chat_id, reply)
            log_to_csv(chat_id, username, "Keyboard typing", "UniverOfCountry", f"{len(data)} университетов")
        else:
            bot.send_message(chat_id, f"Университеты в {country} не найдены.")
            log_to_csv(chat_id, username, "Keyboard typing", "UniverOfCountry", "0 университетов")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при запросе: {e}")
        log_to_csv(chat_id, username, "Keyboard typing", "UniverOfCountry", f"Ошибка: {e}")
    user_states.pop(chat_id, None)
# Предсказание возраста
def handle_name_input(message):
    chat_id = message.chat.id
    name = message.text.strip()
    url = f"https://api.agify.io/?name={name}"
    username = message.from_user.username or "—"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        age = data.get("age")
        count = data.get("count")
        if age is not None and count is not None:
            reply = f"Имя: {name}\nПредполагаемый возраст: {age} лет\nНа основе {count} человек."
        else:
            reply = f"Не удалось получить возраст для имени {name}."
        bot.send_message(chat_id, reply)
        log_to_csv(chat_id, username, "Keyboard typing", "Agify.io", reply)
    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {e}")
        log_to_csv(chat_id, username, "Keyboard typing", "Agify.io", f"Ошибка: {e}")
    user_states.pop(chat_id, None)

# Запуск
def main():
    try:
        print("Бот стартовал")
        bot.polling(none_stop=True, interval=0.5, timeout=3600)
    except Exception as e:
        print("Бот не стартовал:", e)

if __name__ == "__main__":
    main()
