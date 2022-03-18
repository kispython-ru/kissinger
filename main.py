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
session = Session(bind=engine)


@dp.message_handler(commands=['help'], commands_prefix='!/')
async def send_help(message: types.Message):
    await message.reply("Полковнику никто... Не пишет\nПолковника никто... не ждёёт...")


@dp.message_handler(commands=['start'], commands_prefix='!/')
async def send_welcome(message: types.Message):
    # Get user info from db
    user = session.query(User).filter_by(tid=message.from_user.id).first()

    # if unregistered --> add to database and onboard
    if user is None:
        await register_and_onboard(message.from_user.id)
        return
    if user.gid is None or user.vid is None:
        await onboarding.select_prefix(message.from_user.id)
        return

    await dashboard(message.from_user.id)


#
# Here I handle all callback requests. IDK how to make filter on aiogram level so...
# TODO: Better action name management
@dp.callback_query_handler()
async def callback_handler(callback: types.CallbackQuery):
    # Get user info from db
    user = session.query(User).filter_by(tid=callback.from_user.id).first()

    # if unregistered --> add to database and onboard
    if user is None:
        await register_and_onboard(callback.from_user.id)
        return

    # Get payload from callback data
    payload = callback.data.split("_")

    # Find action for request
    match payload[0]:
        case "grouponboard":
            await onboarding.select_group(tid=callback.from_user.id, prefix=payload[1], mid=callback.message.message_id)
        case "prefixonboard":
            await onboarding.select_prefix(callback.from_user.id, callback.message.message_id)
        case "variantonboard":
            if len(payload) > 1:
                await dbmanager.record_gid(session, user, payload[1])
            await onboarding.select_variant(callback.from_user.id, callback.message.message_id)
        case "variantselected":
            if len(payload) > 1:
                await dbmanager.record_vid(session, user, payload[1])
            await dashboard(callback.from_user.id, callback.message.message_id)
        case _:
            print("No case founded for ", payload[0])
    return


async def dashboard(tid, mid=0):
    await messenger.edit_or_send(tid, "Welcome onboard!", mid=mid)


async def register_and_onboard(tid):
    session.add(User(
        tid=tid,
    ))
    session.commit()
    await onboarding.select_prefix(tid)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
