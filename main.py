import logging

from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = ''

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
print("start")


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Hello world!")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)