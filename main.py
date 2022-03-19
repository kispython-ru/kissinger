import logging

import requests
import sqlalchemy as db
import yaml

from aiogram import Dispatcher, executor, types

from aiogram.dispatcher import filters
from sqlalchemy.orm import Session

import re
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from robobrowser import RoboBrowser

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

# TODO: Config initialization must be centralised. And config path put to .env
config = yaml.safe_load(open("config.yml"))


@dp.message_handler((filters.RegexpCommandsFilter(regexp_commands=['task_([0-9]*)'])))
async def send_help(message: types.Message, regexp_command):
    user = session.query(User).filter_by(tid=message.from_user.id).first()
    if user.gid is None or user.vid is None:
        await onboarding.select_prefix(message.from_user.id)
        return
    await open_task(user, str(int(regexp_command.group(1)) - 1))


@dp.message_handler(commands=['help'], commands_prefix='!/')
async def send_help(message: types.Message):
    await message.reply("Полковнику никто... Не пишет\nПолковника никто... не ждёёт...")


@dp.message_handler(commands=['reset'], commands_prefix='!/')
async def send_help(message: types.Message):
    user = session.query(User).filter_by(tid=message.from_user.id).first()

    user.vid = None
    user.gid = None
    user.last_task = None
    session.commit()

    await message.reply("✅ Настройки сброшены!")

    await onboarding.select_prefix(user.tid)


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

    await dashboard(user)


@dp.message_handler()
async def tasks_acceptor(message: types.Message):
    # Get user info from db
    user = session.query(User).filter_by(tid=message.from_user.id).first()

    # if unregistered --> add to database and onboard
    if user is None:
        await register_and_onboard(message.from_user.id)
        return
    if user.gid is None or user.vid is None:
        await onboarding.select_prefix(message.from_user.id)
        return

  #  headers = {'User-Agent': 'Kissinger/1.0'}
   # payload = {'code': message.text.encode('utf-8'), 'csrf_token': user.lt_token}
    # TODO: Договориcь о нормальном API, ну что это за ёбань с плясками?
    browser = RoboBrowser(history=True)
    browser.open("http://kispython.ru" + '/group/' + str(user.gid) + '/variant/' + str(user.vid) + '/task/' + str(user.last_task))

    form = browser.get_form(action='/group/' + str(user.gid) + '/variant/' + str(user.vid) + '/task/' + str(user.last_task))
    form  # <RoboForm q=>
    form['code'].value = message #.text.encode('utf-8')
    browser.submit_form(form)
    r = requests.post("http://kispython.ru/" + 'group/' + str(user.gid) + '/variant/' + str(user.vid) + '/task/' + str(user.last_task), headers=headers,data=payload)

    print(browser.select("card-subtitle"))
    print(browser.response)
    #print(str(r.status_code) + ': ' + str(r.content))
    await open_task(user, user.last_task)


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
            await dashboard(user, callback.message.message_id)
        case "task":
            await open_task(user, payload[1], callback.message.message_id, callback.id)
        case "dashboard":
            await dashboard(user, callback.message.message_id)
        case _:
            print("No case founded for ", payload[0])
    return


async def dashboard(user, mid=0):
    r = requests.get(config['URL'] + 'group/' + str(user.gid) + '/variant/' + str(user.vid) + '/task/list')
    keyboard = types.InlineKeyboardMarkup()
    # answer = "👨‍🏫 Ваши успехи в обучении: \n\n"
    answer = ""
    for task in r.json():
        answer = ""
        match task['status']:
            case 0:
                answer += '⏳ '
            case 1:
                answer += '🏃‍♂️💨 '
            case 2:
                answer += '✔️ '
            case 3:
                answer += '❌ '
            case 4:
                answer += '⚪ '
        # answer += "Задание " + str(task['id']+1) + ": " + task['status_name'] + "\nПосмотреть: /task_" + str(task['id']+1) + "\n\n"
        answer += "Задание " + str(task['id'] + 1) + ": " + task['status_name']
        keyboard.add(
            types.InlineKeyboardButton(text=answer, callback_data="task_" + str(task['id']))
        )
    await messenger.edit_or_send(user.tid, "👨‍🏫 Ваши успехи в обучении:", keyboard, mid)


async def register_and_onboard(tid):
    session.add(User(
        tid=tid,
    ))
    session.commit()
    await onboarding.select_prefix(tid)


async def open_task(user, taskid, mid=0, callid=0):
    # TODO: on all requests check status code
    r = requests.get(config['URL'] + 'group/' + str(user.gid) + '/variant/' + str(user.vid) + '/task/' + str(taskid))
    try:
        answer = "Задание " + str(int(taskid) + 1) + "\n"

        match r.json()['status']:
            case 0:
                answer += '⏳ '
            case 1:
                answer += '🏃‍♂️💨 '
            case 2:
                answer += '✔️ '
            case 3:
                answer += '❌ '
            case 4:
                answer += '⚪ '

        answer += r.json()["status_name"] + "\n\n"

        # TODO: Parse target and paste here
        answer += "Ссылка на задание: " + r.json()["source"] + "\n\n"

        answer += "Когда сделаете, скопируйте свой код и оправьте мне в виде сообщения сюда, я его проверю"
        keyboard = types.InlineKeyboardMarkup()
        if r.json()["status"] == 0 or r.json()["status"] == 1:
            keyboard.add(
                types.InlineKeyboardButton(text="Обновить", callback_data="task_" + taskid)
            )
        keyboard.add(
            types.InlineKeyboardButton(text="<--", callback_data="dashboard")
        )
        await messenger.edit_or_send(user.tid, answer, keyboard, mid)



        # r = requests.get("http://kispython.ru" + 'group/' + str(user.gid) + '/variant/' + str(user.vid) + '/task/' + taskid)

    except:
        # TODO: Костыльно как-то, переделай
        await messenger.popup_error(callid, "⛔ Не удалось выполнить запрос")


        user.last_task = taskid
    session.commit()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
