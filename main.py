# ______ ______              _____
# ___  //_/__(_)________________(_)_____________ _____________
# __  ,<  __  /__  ___/_  ___/_  /__  __ \_  __ `/  _ \_  ___/
# _  /| | _  / _(__  )_(__  )_  / _  / / /  /_/ //  __/  /
# /_/ |_| /_/  /____/ /____/ /_/  /_/ /_/_\__, / \___//_/
#                                        /____/

import logging
import yaml

from aiogram import Bot, Dispatcher, executor, types

# Load config file
config = yaml.safe_load(open("config.yml"))

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config['TOKEN'])
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Hello world!")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)