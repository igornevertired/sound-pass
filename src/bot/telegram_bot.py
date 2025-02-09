import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from src.handlers.user_data_handler import UserDataHandler
from src.db.db_manager import SubscriptionModel, get_db
import yaml


def load_messages(file_path: str = "src/configs/messages.yaml") -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


class SubscriptionCallback(CallbackData, prefix="sub"):
    type: str


class TelegramBot:
    PRICES = {'sub_3': 1090, 'sub_6': 2390, 'sub_12': 3490}
    DURATIONS = {'sub_3': 90, 'sub_6': 180, 'sub_12': 365}

    def __init__(self, token):
        self.bot = Bot(token)
        self.dp = Dispatcher()
        self.user_data_handler = UserDataHandler()
        self.setup_handlers()
        self.messages = load_messages()

    def get_price(self, tariff):
        return self.PRICES.get(tariff, 0)

    def calculate_next_pay_time(self, tariff):
        return datetime.now() + timedelta(days=self.DURATIONS.get(tariff, 0))

    def setup_handlers(self):
        @self.dp.message(Command("start"))
        async def send_welcome(message: types.Message):
            await self.show_main_menu(message.chat.id)

        @self.dp.callback_query()
        async def callback_handler(call: types.CallbackQuery):
            chat_id = call.message.chat.id
            data = call.data

            if data == 'pay':
                await self.show_subscription_options(call.message.chat.id, call.message.message_id)

            elif data.startswith('sub_'):
                self.user_data_handler.add_user(chat_id)
                self.user_data_handler.update_user_data(chat_id, "subscription", data)
                self.user_data_handler.update_user_step(chat_id, "login")
                await self.bot.send_message(chat_id, self.messages["login"])
            elif data == 'help':
                await self.bot.send_message(chat_id, "Здесь будет информация о помощи.")
            elif data == 'back':
                await self.show_main_menu(chat_id=call.message.chat.id, message_id=call.message.message_id)
            elif data in ['card', 'crypto']:
                await self.process_payment(chat_id, data)
            elif data == 'paid':
                await self.bot.send_message(
                    chat_id, self.messages["processing_payment_message"]
                )

        @self.dp.message()
        async def handle_text(message: types.Message):
            chat_id = message.chat.id
            user_data = self.user_data_handler.get_user_data(chat_id)
            if not user_data:
                return

            step = user_data.get("step")
            await self.process_step(chat_id, step, message.text, None)

    async def process_step(self, chat_id, step, text, call: types.CallbackQuery = None):
        if step == "login":
            self.user_data_handler.update_user_data(chat_id, "login", text)
            self.user_data_handler.update_user_step(chat_id, "password")
            await self.bot.send_message(chat_id, self.messages["password"])

        elif step == "password":
            self.user_data_handler.update_user_data(chat_id, "password", text)
            self.user_data_handler.update_user_step(chat_id, "payment_method")

            message_id = call.message.message_id if call else None
            await self.show_payment_options(chat_id=chat_id, message_id=message_id)

    async def process_payment(self, chat_id, method):
        user_data = self.user_data_handler.get_user_data(chat_id)
        if not user_data:
            return

        self.user_data_handler.update_user_data(chat_id, "payment_method", method)
        subscription = user_data.get("subscription")
        login = user_data.get("login")
        password = user_data.get("password")

        async for session in get_db():
            await SubscriptionModel.create_subscription(
                session=session,
                name=login,
                password=password,
                tariff=subscription,
                payment_method=method,
                price=self.get_price(subscription),
                created_time=datetime.now(),
                next_pay_time=self.calculate_next_pay_time(subscription)
            )

        await self.bot.send_message(chat_id, self.messages["thank_you_message"])
        self.user_data_handler.delete_user(chat_id)

    async def edit_message(self, chat_id, message_id, text=None, photo_path=None, reply_markup=None):
        """
        Функция для редактирования сообщения: можно менять текст, фото и клавиатуру.

        """

        if photo_path:
            media = InputMediaPhoto(media=FSInputFile(photo_path), caption=text)
            await self.bot.edit_message_media(media=media, chat_id=chat_id, message_id=message_id,
                                              reply_markup=reply_markup)
        elif text:
            await self.bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id,
                                             reply_markup=reply_markup)

    async def show_subscription_options(self, chat_id: int, message_id: int = None):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=f"Spotify Premium {sub[-1]} мес - {price} руб",
                                                   callback_data=sub)]
                             for sub, price in self.PRICES.items()] + [
                                [InlineKeyboardButton(text="⬅️ Назад", callback_data='back')]]
        )

        if message_id:
            await self.bot.edit_message_media(
                media=InputMediaPhoto(media=FSInputFile("src/img/subscribe.jpg")),
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=markup
            )
        else:
            photo = FSInputFile("src/img/tariff.jpg")
            await self.bot.send_photo(chat_id, photo=photo, reply_markup=markup)

    async def show_payment_options(self, chat_id: int, message_id: int = None):
        """
        Показывает методы оплаты в том же окне.

        """

        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 Карта", callback_data='card'),
                 InlineKeyboardButton(text="🪙 Криптовалюта", callback_data='crypto')],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data='back')]
            ]
        )

        if message_id:
            await self.bot.edit_message_media(
                media=InputMediaPhoto(media=FSInputFile("src/img/payment.jpg")),
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=markup
            )
        else:
            photo = FSInputFile("src/img/payment.jpg")
            await self.bot.send_photo(chat_id, photo=photo, reply_markup=markup)

    async def show_main_menu(self, chat_id: int, message_id: int = None):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить подписку", callback_data='pay')],
                [InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/igornevertired")],
                [InlineKeyboardButton(text="⭐️ Отзывы", url="https://t.me/+Cnn1_qTnCgljYzAy")]
            ]
        )

        if message_id:
            await self.bot.edit_message_media(
                media=InputMediaPhoto(
                    media=FSInputFile("src/img/welcome.jpg"),
                    caption=self.messages["welcome_message"],
                    parse_mode="MarkdownV2"
                ),
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=markup
            )
        else:
            await self.bot.send_photo(
                chat_id,
                photo=FSInputFile("src/img/welcome.jpg"),
                caption=self.messages["welcome_message"],
                parse_mode="MarkdownV2",
                reply_markup=markup
            )

    async def run(self):
        logging.info("Бот запущен...")
        await self.dp.start_polling(self.bot)
