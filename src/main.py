import logging

import requests
import yaml

from aiogram import Dispatcher, executor, types

from aiogram.dispatcher import filters

import werkzeug

# Так надо
werkzeug.cached_property = werkzeug.utils.cached_property
from robobrowser import RoboBrowser

from src import dbmanager, messenger
import onboarding

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
dp = Dispatcher(messenger.bot)

# TODO: Config initialization must be centralised. And config path put to .env
config = yaml.safe_load(open("src/config.yml"))


@dp.message_handler((filters.RegexpCommandsFilter(regexp_commands=['task_([0-9]*)'])))
async def send_help(message: types.Message, regexp_command):
    # TODO: User registration must be centralized
    user = await dbmanager.getuser(message.from_user.id)

    await open_task(user, str(int(regexp_command.group(1)) - 1))


@dp.message_handler(commands=['help'], commands_prefix='!/')
async def send_help(message: types.Message):
    await message.reply("Полковнику никто... Не пишет\nПолковника никто... не ждёёт...")


@dp.message_handler(commands=['reset'], commands_prefix='!/')
async def send_help(message: types.Message):
    user = await dbmanager.getuser(message.from_user.id)
    await dbmanager.resetuser(user)
    await message.reply("✅ Настройки сброшены!")
    await onboarding.select_prefix(user.tid)


@dp.message_handler(commands=['start'], commands_prefix='!/')
async def send_welcome(message: types.Message):
    user = await dbmanager.getuser(message.from_user.id)
    await dashboard(user)


@dp.message_handler()
async def tasks_acceptor(message: types.Message):
    # Get user info from db
    user = await dbmanager.getuser(message.from_user.id)

    # TODO: Договориcь о нормальном API, ну что это за ёбань с плясками?

    # Create headless browser
    browser = RoboBrowser(user_agent='Kissinger/1.0')

    # Open DTA and insert code to form
    browser.open("http://kispython.ru" + '/group/' + str(user.gid) + '/variant/' + str(user.vid) + '/task/' + str(user.last_task))
    form = browser.get_form(action='/group/' + str(user.gid) + '/variant/' + str(user.vid) + '/task/' + str(user.last_task))
    form  # <RoboForm q=>
    form['code'].value = message  # .text.encode('utf-8')
    browser.submit_form(form)

    # TODO: check is request successful

    # Redirect to task viewer
    await open_task(user, user.last_task)
    # Нет, я не могу просто отправить POST. В форме нужно передавать не только code, но и csrf token, который где-то нужно взять


#
# Here I handle all callback requests. IDK how to make filter on aiogram level so...
# TODO: Better action name management
@dp.callback_query_handler()
async def callback_handler(callback: types.CallbackQuery):
    # Get user info from db
    user = await dbmanager.getuserraw(callback.from_user.id)

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
                await dbmanager.record_gid(user, payload[1])
            await onboarding.select_variant(callback.from_user.id, callback.message.message_id)
        case "variantselected":
            if len(payload) > 1:
                await dbmanager.record_vid(user, payload[1])
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
        answer += "Задание " + str(task['id'] + 1) + ": " + task['status_name']
        keyboard.add(
            types.InlineKeyboardButton(text=answer, callback_data="task_" + str(task['id']))
        )
    await messenger.edit_or_send(user.tid, "👨‍🏫 Ваши успехи в обучении:", keyboard, mid)


# TODO: onerror show it's reason (is not implemented in api, mb i should parse webbage again
async def open_task(user, taskid, mid=0, callid=0):
    # answer string
    answer = "Задание " + str(int(taskid) + 1) + "\n"

    #
    # There are problem: direct request returns 500 sometimes
    # So first of all:
    # TODO: Resolve promlem with official api
    # Second one:
    # For now we will make LIST request and take necessary task by it's id

    req = requests.get(config['URL'] + 'group/' + str(user.gid) + '/variant/' + str(user.vid) + '/task/list')
    r = req.json()[int(taskid)]

    href = r['source']

    try:
        match r['status']:
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

        answer += r["status_name"] + "\n\n"
    except:
        # TODO: Костыльно как-то, переделай
        await messenger.popup_error(callid, "⛔ Не удалось выполнить запрос")

    # TODO: Fix bug where ios client can't open this link
    # TODO: Smart webpage parsing
    answer += "Ссылка на задание:  " + href + "\n\n"
    answer += "Когда сделаете, скопируйте свой код и оправьте мне в виде сообщения сюда, я его проверю"
    keyboard = types.InlineKeyboardMarkup()
    # TODO: Autoupdate
    # TODO: Show button only for tasks in processing
    keyboard.add(
        types.InlineKeyboardButton(text="Обновить", callback_data="task_" + str(taskid))
    )
    keyboard.add(
        types.InlineKeyboardButton(text="<--", callback_data="dashboard")
    )
    await messenger.edit_or_send(user.tid, answer, keyboard, mid)
    await dbmanager.applylasttask(user, taskid)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
