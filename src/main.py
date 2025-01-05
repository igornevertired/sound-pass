import logging
import telebot
from telebot import types
import yaml
from logger import setup_logging


class ConfigLoader:
    @staticmethod
    def load_config(config_path):
        with open(config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)


class UserDataHandler:
    def __init__(self):
        self.user_data = {}

    def add_user(self, chat_id):
        if chat_id not in self.user_data:
            self.user_data[chat_id] = {}

    def update_user_step(self, chat_id, step):
        self.user_data[chat_id]["step"] = step

    def update_user_data(self, chat_id, key, value):
        self.user_data[chat_id][key] = value

    def get_user_data(self, chat_id):
        return self.user_data.get(chat_id, {})

    def delete_user(self, chat_id):
        if chat_id in self.user_data:
            del self.user_data[chat_id]


class TelegramBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.user_data_handler = UserDataHandler()
        self.setup_handlers()

    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            self.show_main_menu(message.chat.id)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            chat_id = call.message.chat.id

            if call.data == 'pay':
                self.bot.send_message(chat_id, "Введите ваш логин:")
                self.user_data_handler.add_user(chat_id)
                self.user_data_handler.update_user_step(chat_id, "login")

            elif call.data == 'help':
                self.bot.send_message(chat_id, "Здесь будет информация о помощи.")

            elif call.data == 'support':
                self.bot.send_message(chat_id, "Свяжитесь с поддержкой: @ваш_аккаунт")

            elif call.data == 'back':
                self.show_main_menu(chat_id)

            elif call.data == 'paid':
                self.bot.send_message(chat_id,
                                      "🔄 Мы обрабатываем ваш платеж. Совсем скоро вы сможете пользоваться Spotify! 🎶")

            elif call.data == 'card':
                self.user_data_handler.update_user_data(chat_id, "payment_method", "Карта")
                self.send_payment_details(chat_id, "💳 Реквизиты для оплаты картой:\n"
                                                   "Номер карты: 4377 7237 7250 0918 \n"
                                                   "После оплаты пришлите чек перевода в чат")

            elif call.data == 'crypto':
                self.user_data_handler.update_user_data(chat_id, "payment_method", "Криптовалюта")
                self.send_payment_details(chat_id, "🪙 Реквизиты для оплаты криптовалютой:\n"
                                                   "Кошелек TRC20: TXmM4MpjoLweyBJa1FaLQYDaXBigWtadNi")

        @self.bot.message_handler(func=lambda message: True)
        def handle_text(message):
            chat_id = message.chat.id
            user_data = self.user_data_handler.get_user_data(chat_id)

            if user_data:
                step = user_data.get("step")

                if step == "login":
                    self.user_data_handler.update_user_data(chat_id, "login", message.text)
                    self.user_data_handler.update_user_step(chat_id, "password")
                    self.bot.send_message(chat_id, "Введите ваш пароль:")

                elif step == "password":
                    self.user_data_handler.update_user_data(chat_id, "password", message.text)
                    self.user_data_handler.update_user_step(chat_id, "payment_method")

                    markup = types.InlineKeyboardMarkup(row_width=2)
                    btn_card = types.InlineKeyboardButton("💳 Карта", callback_data='card')
                    btn_crypto = types.InlineKeyboardButton("🪙 Криптовалюта", callback_data='crypto')
                    markup.add(btn_card, btn_crypto)

                    self.bot.send_message(chat_id, "Выберите способ оплаты:", reply_markup=markup)

    def send_payment_details(self, chat_id, details):
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data='back')
        btn_paid = types.InlineKeyboardButton("✅ Оплатил", callback_data='paid')
        markup.add(btn_back, btn_paid)

        self.bot.send_message(chat_id, details, reply_markup=markup)

    def show_main_menu(self, chat_id):
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_pay = types.InlineKeyboardButton("💳 Оплатить подписку", callback_data='pay')
        btn_help = types.InlineKeyboardButton("❓ Помощь", callback_data='help')
        btn_support = types.InlineKeyboardButton("🆘 Поддержка", callback_data='support')
        markup.add(btn_pay, btn_help, btn_support)

        self.bot.send_message(chat_id, "SoundPass Bot — твой надежный помощник в мире музыки!\n\n"
                                       "С помощью этого бота ты можешь легко и быстро оплатить подписку на Spotify и "
                                       "наслаждаться любимыми треками без перерывов.\n\n"
                                       "Выберите интересующая вас опцию:", reply_markup=markup)

    def run(self):
        logging.info("Бот запущен...")
        self.bot.polling(none_stop=True)


if __name__ == '__main__':
    setup_logging()

    CONFIG_PATH = "./src/configs/config.yaml"
    config = ConfigLoader.load_config(CONFIG_PATH)
    TOKEN = config['API_KEY']

    bot = TelegramBot(TOKEN)
    bot.run()