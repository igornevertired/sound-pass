import logging
from datetime import datetime, timedelta

import telebot
from telebot import types
from src.handlers.user_data_handler import UserDataHandler
from src.db.db_manager import SubscriptionModel


class TelegramBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.user_data_handler = UserDataHandler()
        self.setup_handlers()

    def get_price_by_tariff(self, tariff):
        # Возвращает цену в зависимости от типа подписки
        prices = {
            'sub_3': 1090,
            'sub_6': 2390,
            'sub_12': 3490
        }
        return prices.get(tariff, 0)

    def calculate_next_pay_time(self, tariff):
        durations = {
            'sub_3': timedelta(days=90),
            'sub_6': timedelta(days=180),
            'sub_12': timedelta(days=365)
        }
        return datetime.now() + durations.get(tariff, timedelta(days=0))

    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            self.show_main_menu(message.chat.id)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            chat_id = call.message.chat.id

            if call.data == 'pay':
                self.show_subscription_options(chat_id)

            elif call.data.startswith('sub_'):
                self.user_data_handler.add_user(chat_id)
                self.user_data_handler.update_user_data(chat_id, "subscription", call.data)
                self.bot.send_message(chat_id, "Введите ваш логин:")
                self.user_data_handler.update_user_step(chat_id, "login")

            elif call.data == 'help':
                self.bot.send_message(chat_id, "Здесь будет информация о помощи.")

            elif call.data == 'support':
                self.bot.send_message(chat_id, "Свяжитесь с поддержкой: @ваш_аккаунт")

            elif call.data == 'reviews':
                self.show_reviews(chat_id)

            elif call.data == 'back':
                self.show_main_menu(chat_id)

            elif call.data == 'paid':
                self.bot.send_message(chat_id,
                                      "🔄 Мы обрабатываем ваш платеж. Совсем скоро вы сможете пользоваться Spotify! 🎶")


            elif call.data in ['card', 'crypto']:
                # Обработка выбора способа оплаты
                self.user_data_handler.update_user_data(chat_id, "payment_method", call.data)
                self.user_data_handler.update_user_step(chat_id, "payment_method")

                # Сохраняем данные в базу данных
                user_data = self.user_data_handler.get_user_data(chat_id)
                subscription_data = user_data.get("subscription")
                login = user_data.get("login")
                password = user_data.get("password")
                payment_method = call.data  # Способ оплаты

                SubscriptionModel.create_subscription(
                    name=login,
                    password=password,
                    tariff=subscription_data,
                    payment_method=payment_method,
                    price=self.get_price_by_tariff(subscription_data),
                    created_time=datetime.now(),
                    next_pay_time=self.calculate_next_pay_time(subscription_data)
                )

                self.bot.send_message(chat_id, "Ваши данные сохранены. Спасибо за покупку!")
                self.user_data_handler.delete_user(chat_id)  # Очищаем данные пользователя

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

                elif step == "payment_method":
                    # Сохраняем данные в базу данных
                    subscription_data = user_data.get("subscription")
                    login = user_data.get("login")
                    password = user_data.get("password")
                    payment_method = message.text  # Способ оплаты

                    # Пример: сохраняем данные в базу данных
                    SubscriptionModel.create_subscription(
                        name=login,  # Используем логин как имя
                        password=password,
                        payment_method=payment_method,
                        tariff=subscription_data,  # Тип подписки (sub_3, sub_6, sub_12)
                        price=self.get_price_by_tariff(subscription_data),  # Цена подписки
                        created_time=datetime.now(),  # Текущее время
                        next_pay_time=self.calculate_next_pay_time(subscription_data)  # Время следующей оплаты
                    )

                    self.user_data_handler.delete_user(chat_id)  # Очищаем данные пользователя

    def show_subscription_options(self, chat_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_sub_3 = types.InlineKeyboardButton("Spotify Premium 3 мес - 1090 руб", callback_data='sub_3')
        btn_sub_6 = types.InlineKeyboardButton("Spotify Premium 6 мес - 2390 руб", callback_data='sub_6')
        btn_sub_12 = types.InlineKeyboardButton("Spotify Premium 12 мес - 3490 руб", callback_data='sub_12')
        markup.add(btn_sub_3, btn_sub_6, btn_sub_12)

        self.bot.send_message(chat_id, "Выберите подписку:", reply_markup=markup)

    def show_reviews(self, chat_id):
        reviews_text = "⭐️⭐️⭐️⭐️⭐️\nОтличный сервис! Быстро и качественно.\n\n"
        reviews_text += "⭐️⭐️⭐️⭐️\nВсе понравилось, но есть небольшие замечания.\n\n"
        reviews_text += "⭐️⭐️⭐️\nНеплохо, но можно лучше.\n\n"
        reviews_text += "⭐️⭐️\nНе очень доволен, есть проблемы.\n\n"
        reviews_text += "⭐️\nОчень плохой опыт.\n\n"

        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data='back')
        markup.add(btn_back)

        self.bot.send_message(chat_id, reviews_text, reply_markup=markup)

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
        btn_reviews = types.InlineKeyboardButton("⭐️ Отзывы", callback_data='reviews')
        markup.add(btn_pay, btn_help, btn_support, btn_reviews)

        self.bot.send_message(chat_id, "SoundPass Bot — твой надежный помощник в мире музыки!\n\n"
                                       "С помощью этого бота ты можешь легко и быстро оплатить подписку на Spotify и "
                                       "наслаждаться любимыми треками без перерывов.\n\n"
                                       "Выберите интересующая вас опция:", reply_markup=markup)

    def run(self):
        logging.info("Бот запущен...")
        self.bot.polling(none_stop=True)
