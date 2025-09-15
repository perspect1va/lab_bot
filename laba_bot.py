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
    user_states.pop(chat_id, None)
    show_main_menu(chat_id)

# Главное меню
def show_main_menu(chat_id):
    keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_markup.add(types.KeyboardButton("уники"))
    keyboard_markup.add(types.KeyboardButton("коты"))
    keyboard_markup.add(types.KeyboardButton("предсказание"))
    bot.send_message(chat_id, "Добро пожаловать! Выбери действие:", reply_markup=keyboard_markup)

# Обработка всех сообщений
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    chat_id = message.chat.id
    text = message.text.strip()
    username = message.from_user.username or "—"
    response = f'Вы написали "{text}", я не знаю такой команды.'

    if text == "Отмена":
        user_states.pop(chat_id, None)
        show_main_menu(chat_id)
        return

    # Обработка ожидаемого ввода
    if user_states.get(chat_id) == 'awaiting_country':
        handle_country_input(message)
        return

    if user_states.get(chat_id) == 'awaiting_name':
        handle_name_input(message)
        return

    # Блокировка других команд при активном состоянии
    if user_states.get(chat_id) in ['awaiting_country', 'awaiting_name']:
        bot.send_message(chat_id, "Пожалуйста, завершите текущий ввод или нажмите 'Отмена'.")
        return

    # Кнопка "уники"
    if text == "уники":
        bot.send_sticker(chat_id, "CAACAgIAAxkBAAEPVzZowVnFsoyIk_hp2LNo_zuTQGZhlgACTwADlb9JMgErK2skxYHhNgQ")
        user_states[chat_id] = 'awaiting_country'
        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(types.KeyboardButton("Отмена"))
        bot.send_message(chat_id, "Введите страну (например, Belarus):", reply_markup=cancel_markup)
        return

    # Кнопка "коты"
    elif text == "коты":
        bot.send_sticker(chat_id, "CAACAgIAAxkBAAEPVzVowVnF7O-7yOLJFZbDDSQeyWS7iQACR1QAAjvgmUkWLyWxzYb-XDYE")
        try:
            r = requests.get("https://catfact.ninja/fact")
            r.raise_for_status()
            fact = r.json().get("fact")
            bot.send_message(chat_id, f"Интересный факт о кошках:\n{fact}")
            log_to_csv(chat_id, username, text, "Cat Facts", fact)
            user_states[chat_id] = 'cat_fact_mode'
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка при получении факта: {e}")
            log_to_csv(chat_id, username, text, "Cat Facts", f"Ошибка: {e}")
        return

    # Кнопка "предсказание"
    elif text == "предсказание":
        bot.send_sticker(chat_id, "CAACAgIAAxkBAAEPVzhowVnFChAowQqjDOXpGOZmwHiZSQACRhYAAnuI-Esn4nImywnFZzYE")
        user_states[chat_id] = 'awaiting_name'
        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(types.KeyboardButton("Отмена"))
        bot.send_message(chat_id, "Введите имя для предсказания возраста:", reply_markup=cancel_markup)
        return

    # Ввод после "коты"
    elif user_states.get(chat_id) == 'cat_fact_mode':
        bot.send_message(chat_id, response)
        log_to_csv(chat_id, username, text, "—", response)
        return

    # Неизвестная команда
    else:
        bot.send_message(chat_id, response)
        log_to_csv(chat_id, username, text, "—", response)

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
            log_to_csv(chat_id, username, country, "UniverOfCountry", f"{len(data)} университетов")
        else:
            bot.send_message(chat_id, f"Университеты в {country} не найдены.")
            log_to_csv(chat_id, username, country, "UniverOfCountry", "0 университетов")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при запросе: {e}")
        log_to_csv(chat_id, username, country, "UniverOfCountry", f"Ошибка: {e}")
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
        log_to_csv(chat_id, username, name, "Agify.io", reply)
    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {e}")
        log_to_csv(chat_id, username, name, "Agify.io", f"Ошибка: {e}")
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
