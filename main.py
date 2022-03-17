import logging
import yaml
import sqlalchemy as db

from aiogram import Bot, Dispatcher, executor, types

# Load config file
config = yaml.safe_load(open("config.yml"))

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config['TOKEN'])
dp = Dispatcher(bot)

# Initialize database
engine = db.create_engine('sqlite:///kissinger.sqlite')
connection = engine.connect()
metadata = db.MetaData()
users = db.Table('users', metadata, autoload=True, autoload_with=engine)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    user = connection.execute(db.select([users]).where(users.columns.tid == message.from_user.id)).fetchall()

    if len(user) == 0:
        connection.execute(db.insert(users).values(tid=message.from_user.id))
        await message.reply("You're a newbie here.. so, new entry inserted!")
    else:
        await message.reply("Hi, username! I can remember you. I am watching you! ")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
