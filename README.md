# SoundPass Telegram Bot

## Описание

SoundPass — это Telegram-бот для автоматизированной работы с учетными записями Spotify, 
предлагающий выбор метода оплаты. Бот использует aiogram для обработки сообщений и asyncio 
для асинхронной работы.

## Функционал

- Авторизация через ввод логина и пароля
- Выбор метода оплаты
- Работа с inline-кнопками
- Использование асинхронных обработчиков команд

## Установка

### Клонирование репозитория

```bash
git clone https://github.com/your-repo/soundpass-bot.git
cd soundpass-bot
```
### Установка зависимостей

```bash
poetry install --sync
```

### Создание файла окружения

Создайте файл .env и добавьте токен бота:

```bash
BOT_TOKEN=your_telegram_bot_token
```

## Запуск

### Активация виртуального окружения

```bash
poetry shell
```

### Запуск бота

```bash
python src/bot/telegram_bot.py
```

## Используемые технологии

 - Python 3.10
 - Aiogram 3 — для работы с Telegram API
 - Poetry — для управления зависимостями
 - PostgreSQL

