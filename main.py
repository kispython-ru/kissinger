import logging
import sqlalchemy as db

from aiogram import Dispatcher, executor, types

# Load config file
from sqlalchemy.orm import Session

import dbmanager
import messenger
import onboarding
from models import User


# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
dp = Dispatcher(messenger.bot)

# Initialize database
engine = db.create_engine('sqlite:///kissinger.sqlite')
# connection = engine.connect()
# metadata = db.MetaData()
# users = db.Table('users', metadata, autoload=True, autoload_with=engine)
session = Session(bind=engine)


@dp.message_handler(commands=['help'], commands_prefix='!/')
async def send_help(message: types.Message):
    await message.reply("Полковнику никто... Не пишет\nПолковника никто... не ждёёт...")


@dp.message_handler(commands=['start'], commands_prefix='!/')
async def send_welcome(message: types.Message):
    # Get user info from db
    # allusers = connection.execute(db.select([users]).where(users.columns.tid == message.from_user.id)).fetchall()

    # if unregistered
    # if len(allusers) == 0:
    #    connection.execute(db.insert(users).values(tid=message.from_user.id))
    #     await message.reply("You're a newbie here.. so, new entry inserted!")
    #    return

    # TODO: Reimagine this shit
    await onboarding.select_prefix(message.from_user.id)

    await message.reply("Hi, username! I can remember you. I am watching you!")


@dp.callback_query_handler()
async def callback_handler(callback: types.CallbackQuery):
    with Session(engine) as session:
        user = session.query(User).filter_by(tid=callback.from_user.id).first()
        print(user)
        payload = callback.data.split("_")
        action = payload[0]

        if action == "grouponboard":
            await onboarding.select_group(tid=callback.from_user.id, prefix=payload[1], mid=callback.message.message_id)
            return
        if action == "prefixonboard":
            await onboarding.select_prefix(callback.from_user.id, callback.message.message_id)
            return
        if action == "variantonboard":
            if len(payload) > 1:
                await dbmanager.record_gid(session, user, payload[1])
            await onboarding.select_variant(callback.from_user.id, callback.message.message_id)
        if action == "variantselected":
            if len(payload) > 1:
                await dbmanager.record_vid(session, user, payload[1])
            await dashboard(callback.from_user.id, callback.message.message_id)
    return


async def dashboard(tid, mid=0):
    await messenger.edit_or_send(tid, "Welcome onboard!", mid=mid)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
