import telebot
from telebot import types
import json
import random
import os

with open("token.txt", "r") as file:
    TOKEN = file.read().strip()

bot = telebot.TeleBot(TOKEN)

print("Запустил бота. Работает")

with open("words.json", "r", encoding="utf-8") as f:
    words = json.load(f)

def load_user_data():
    try:
        with open("user_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        data = {}
        with open("user_data.json", "w") as f:
            json.dump(data, f)
        return data


def save_user_data(data):
    with open("user_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_translation(message, correct_answer):
    markup = types.InlineKeyboardMarkup()
    return_menu_button = types.InlineKeyboardButton("Вернуться в меню", callback_data="return_menu")
    send_new_word_button = types.InlineKeyboardButton("Получить новое слово", callback_data="send_newword")
    markup.add(return_menu_button, send_new_word_button)


    user_answer = message.text.strip().lower()
    if user_answer == correct_answer.lower():
        bot.send_message(message.chat.id, "✅ Вы ответили верно!", reply_markup=markup)

        user_data = load_user_data()
        user_data[str(message.chat.id)]["score"] += 1
        save_user_data(user_data)
    else:
        bot.send_message(message.chat.id, f"❌ К сожалению, вы ответили неверно :( \n Правильный ответ: {correct_answer}", reply_markup=markup)

global photo_msg
photo_msg = None
global rank_msg
rank_msg = None


@bot.message_handler(commands=["start"])
def start(message):
    global photo_msg
    photo_path = "img/start_photo.png"
    photo_msg = bot.send_photo(message.chat.id, open(photo_path, "rb"))

    markup = types.InlineKeyboardMarkup()
    menu_button = types.InlineKeyboardButton("Меню", callback_data="menu_button_clicked")
    markup.add(menu_button)
    bot.send_message(message.chat.id, "Привет! Я бот, который поможет тебе изучить английские слова. Нажми на меню для начала работы.", reply_markup=markup)

@bot.message_handler(commands=["menu"])
def menu(message):
    global rank_msg
    global photo_msg
    if photo_msg:
        if photo_msg.message_id is not None:
            try:
                bot.delete_message(message.chat.id, photo_msg.message_id)
            except:
                pass
    if rank_msg:
        if rank_msg.message_id is not None:
            try:
                bot.delete_message(message.chat.id, rank_msg.message_id)
            except:
                pass
    markup = types.InlineKeyboardMarkup()
    send_newword_button = types.InlineKeyboardButton("Получить новое слово", callback_data="send_newword")
    show_score_button = types.InlineKeyboardButton("Показать счет", callback_data="show_score_button")
    markup.add(send_newword_button, show_score_button)
    bot.send_message(message.chat.id, "Вы находитесь в главном меню. Доступные команды:", reply_markup=markup)


@bot.message_handler(commands=["show_score"])
def show_user_score(message):
    global rank_msg
    bot.delete_message(message.chat.id, message.message_id)

    markup = types.InlineKeyboardMarkup()
    return_menu_button = types.InlineKeyboardButton("Вернуться в меню", callback_data="return_menu")
    markup.add(return_menu_button)

    user_data = load_user_data()
    chat_id = str(message.chat.id)
    this_score = user_data.get(chat_id, {}).get("score", 0)

    all_users = []
    for user_id, data in user_data.items():
        score = data.get("score", 0)
        all_users.append((user_id, score))

    sorted_users = sorted(all_users, key=lambda x: x[1], reverse=True)

    rank = None
    for index, (user_id, score) in enumerate(sorted_users, start=1):
        if user_id == chat_id:
            rank = index
            break
    if rank is not None:
        rank_msg = bot.send_message(message.chat.id, f"Ваше место в рейтинге: {rank}")
    if this_score > 0:
        bot.send_message(message.chat.id, f"Ваш счет: {this_score}. Вы молодцы!", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас пока нет счета! Начинайте его поскорее набирать", reply_markup=markup)


@bot.message_handler(commands=["send_new_word"])
def send_new_word(message):
    bot.delete_message(message.chat.id, message.message_id)
    chat_id = str(message.chat.id)
    user_data = load_user_data()

    eng_word = random.choice(list(words.keys()))
    rus_word = words[eng_word]
    correct_word = random.randint(1, 3)

    score = user_data.get(chat_id, {}).get("score", 0)
    user_data[chat_id] = {
        "eng_word": eng_word,
        "rus_word": rus_word,
        "correct_word": correct_word,
        "score": score
        }
    if "score" not in user_data[chat_id]:
        user_data[chat_id]["score"] = 0
    save_user_data(user_data)

    markup = types.InlineKeyboardMarkup()
    memorize_button = types.InlineKeyboardButton("Закрепить!", callback_data="memorize_word")
    markup.add(memorize_button)

    bot.send_message(message.chat.id, f"Новое слово! \n \n {eng_word.capitalize()} означает {rus_word.capitalize()}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_data = load_user_data()
    chat_id = str(call.message.chat.id)

    if call.data == "menu_button_clicked":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        menu(call.message)

    elif call.data == "send_newword":
        send_new_word(call.message)

    elif call.data == "memorize_word":
        if chat_id not in user_data:
            bot.send_message(call.message.chat.id, "Сначала получи слово.")
            return

        eng_word = user_data[chat_id]["eng_word"]
        rus_word = user_data[chat_id]["rus_word"]
        correct_word = user_data[chat_id]["correct_word"]
        memorize_lang = random.choice(["eng", "rus"])
        memorize_type = random.choice(["choice", "write"])
        if memorize_type == "choice":
            if memorize_lang == "rus":
                variants = []
                while len(variants) < 3:
                    this_word = words[random.choice(list(words.keys()))]
                    if this_word != rus_word and this_word not in variants:
                        variants.append(this_word)
                variants[correct_word - 1] = rus_word

                markup = types.InlineKeyboardMarkup()
                var1 = types.InlineKeyboardButton(variants[0], callback_data="var1")
                var2 = types.InlineKeyboardButton(variants[1], callback_data="var2")
                var3 = types.InlineKeyboardButton(variants[2], callback_data="var3")
                markup.add(var1, var2, var3)

                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.send_message(call.message.chat.id, f'Как переводится слово {eng_word}?', reply_markup=markup)
            
            elif memorize_lang == "eng":
                variants = []
                while len(variants) < 3:
                    rand_eng, rand_rus = random.choice(list(words.items()))
                    if rand_eng != eng_word and rand_eng not in variants:
                        variants.append(rand_eng)
                variants[correct_word - 1] = eng_word

                markup = types.InlineKeyboardMarkup()
                var1 = types.InlineKeyboardButton(variants[0], callback_data="var1")
                var2 = types.InlineKeyboardButton(variants[1], callback_data="var2")
                var3 = types.InlineKeyboardButton(variants[2], callback_data="var3")
                markup.add(var1, var2, var3)

                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.send_message(call.message.chat.id, f'Как переводится слово {rus_word}?', reply_markup=markup)
        elif memorize_type == "write":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            if memorize_lang == "rus":
                msg = bot.send_message(call.message.chat.id, f"Как переводится слово {rus_word}?")
                bot.register_next_step_handler(msg, check_translation, correct_answer=eng_word)
            elif memorize_lang == "eng":
                msg = bot.send_message(call.message.chat.id, f"Как переводится слово {eng_word}?")
                bot.register_next_step_handler(msg, check_translation, correct_answer=rus_word)



                

    elif call.data.startswith("var"):
        if chat_id not in user_data:
            bot.send_message(call.message.chat.id, "Сначала получи слово.")
            return

        correct = user_data[chat_id]["correct_word"]
        chosen = int(call.data[-1])

        bot.delete_message(call.message.chat.id, call.message.message_id)

        markup = types.InlineKeyboardMarkup()
        return_menu_button = types.InlineKeyboardButton("Вернуться в меню", callback_data="return_menu")
        send_new_word_button = types.InlineKeyboardButton("Получить новое слово", callback_data="send_newword")
        markup.add(return_menu_button, send_new_word_button)

        if chosen == correct:
            bot.send_message(call.message.chat.id, "✅ Вы ответили верно!", reply_markup=markup)
            user_data[chat_id]["score"] += 1
            save_user_data(user_data)
        else:
            bot.send_message(call.message.chat.id, f"❌ К сожалению, вы ответили неверно :( \n Правильный ответ: {correct}", reply_markup=markup)
    
    elif call.data == "show_score_button":
        show_user_score(call.message)

    elif call.data == "return_menu":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        menu(call.message)



bot.infinity_polling()