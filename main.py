import logging
import yaml

from aiogram import Bot, Dispatcher, executor, types

config = yaml.safe_load(open("config.yml"))

API_TOKEN = config['TOKEN']

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Hello world!")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)