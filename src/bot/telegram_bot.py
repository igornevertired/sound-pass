import logging
import os
from datetime import datetime, timedelta, timezone
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from src.handlers.user_data_handler import UserDataHandler
from src.db.db_manager import SubscriptionModel, get_db
import yaml
from aiogram import F

SCREENSHOT_DIR = "screenshots"


def load_messages(file_path: str = "src/configs/messages.yaml") -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


class SubscriptionCallback(CallbackData, prefix="sub"):
    type: str


class TelegramBot:
    PRICES = {'sub_3': 1090, 'sub_6': 2390, 'sub_12': 3490}
    DURATIONS = {'sub_3': 90, 'sub_6': 180, 'sub_12': 365}
    PAYMENT_DETAILS = {"card": "1234 5678 9012 3456", "sbp": "+7 999 123 45 67"}  # Данные для оплаты

    def __init__(self, token):
        self.bot = Bot(token)
        self.dp = Dispatcher()
        self.user_data_handler = UserDataHandler()
        self.setup_handlers()
        self.messages = load_messages()

    def get_price(self, tariff):
        return self.PRICES.get(tariff, 0)

    def calculate_next_pay_time(self, tariff):
        return datetime.now(timezone.utc) + timedelta(days=self.DURATIONS.get(tariff, 0))

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
            elif data == 'back':
                await self.show_main_menu(chat_id=call.message.chat.id, message_id=call.message.message_id)
            elif data in ['card', 'sbp']:
                await self.process_payment(chat_id, data)
            elif data == 'paid':
                await self.confirm_payment(chat_id)

        @self.dp.message(F.content_type == types.ContentType.PHOTO)
        async def handle_screenshot(message: types.Message, bot: Bot):
            chat_id = message.chat.id
            user_data = self.user_data_handler.get_user_data(chat_id)

            if not user_data or user_data.get("step") != "waiting_screenshot":
                return

            login = user_data.get("login", "unknown")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = "screenshots"  # Папка для сохранения
            os.makedirs(screenshot_dir, exist_ok=True)  # Создаем папку, если её нет
            filename = f"{screenshot_dir}/{login}_{timestamp}.jpg"

            photo = message.photo[-1]  # Берем самое большое фото
            file = await bot.get_file(photo.file_id)  # Получаем объект файла
            await bot.download_file(file.file_path, filename)  # Скачиваем файл

            self.user_data_handler.update_user_data(chat_id, "screenshot", filename)
            self.user_data_handler.update_user_step(chat_id, "waiting_payment_confirmation")

            markup = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Оплатил ✅", callback_data="paid")]]
            )

            await bot.send_message(
                chat_id, "Скриншот получен. Теперь нажмите кнопку 'Оплатил ✅'.", reply_markup=markup
            )

        @self.dp.message()
        async def handle_text(message: types.Message):
            chat_id = message.chat.id
            user_data = self.user_data_handler.get_user_data(chat_id)
            if not user_data:
                return

            step = user_data.get("step")
            username = message.from_user.username or "unknown"
            self.user_data_handler.update_user_data(chat_id, "telegram_username", username)
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
        self.user_data_handler.update_user_step(chat_id, "waiting_screenshot")
        payment_info = self.PAYMENT_DETAILS[method]

        await self.bot.send_message(
            chat_id, f"Отправьте оплату на: {payment_info}. У вас есть 15 минут. Затем отправьте скриншот оплаты."
        )

    async def confirm_payment(self, chat_id):
        user_data = self.user_data_handler.get_user_data(chat_id)
        if not user_data or user_data.get("step") != "waiting_payment_confirmation":
            await self.bot.send_message(chat_id, "Сначала отправьте скриншот оплаты!")
            return

        login = user_data.get("login")
        password = user_data.get("password")
        subscription = user_data.get("subscription")
        payment_method = user_data.get("payment_method")
        screenshot = user_data.get("screenshot")
        telegram_username = user_data.get("telegram_username", "unknown")

        created_time = datetime.now(timezone.utc).replace(tzinfo=None)
        next_pay_time = self.calculate_next_pay_time(subscription).replace(tzinfo=None)

        async for session in get_db():
            await SubscriptionModel.create_subscription(
                session=session,
                name=login,
                password=password,
                telegram_username=telegram_username,
                tariff=subscription,
                payment_method=payment_method,
                price=self.get_price(subscription),
                created_time=created_time,
                next_pay_time=next_pay_time,
                screenshot=screenshot
            )

        await self.bot.send_message(chat_id, "Оплата подтверждена! Подписка активирована.")
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
                [InlineKeyboardButton(text="💳 Банковская карта", callback_data='card'),
                 InlineKeyboardButton(text=" СБП", callback_data='sbp')],
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
