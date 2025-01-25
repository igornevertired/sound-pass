import yaml
from src.bot.telegram_bot import TelegramBot
from src.logger import setup_logging


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


if __name__ == '__main__':
    setup_logging()

    CONFIG_PATH = "./src/configs/config.yaml"
    config = load_config(CONFIG_PATH)
    TOKEN = config['API_KEY']

    bot = TelegramBot(TOKEN)
    bot.run()
