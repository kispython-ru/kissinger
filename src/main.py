#
# Initialization and checkup
#
import asyncio
from requests_html import AsyncHTMLSession
from multiprocessing import Process

print('''
 ______ ______              _____
 ___  //_/__(_)________________(_)_____________ _____________
 __  ,<  __  /__  ___/_  ___/_  /__  __ \_  __ `/  _ \_  ___/
 _  /| | _  / _(__  )_(__  )_  / _  / / /  /_/ //  __/  /
 /_/ |_| /_/  /____/ /____/ /_/  /_/ /_/_\__, / \___//_/
                                        /____/
                         Modern Telegram bot for kispython.ru
''')

print('Loading dependencies...')

import logging

logging.basicConfig(level=logging.WARN)

import os
import yaml

if os.getenv("CONFIG_PATH") is None:
    print("[FATAL] Please set CONFIG_PATH environment variable")
    exit(1)

if os.path.exists(os.getenv("CONFIG_PATH")) is False:
    print("[FATAL] Config file not found")
    exit(1)

config = yaml.safe_load(open(os.environ.get("CONFIG_PATH")))

if config is None:
    print("[FATAL] Config file is empty")
    exit(1)

if config["TGTOKEN"] is None:
    print("[FATAL] Telegram token not found")
    exit(1)

if config["SQLITE"] is None:
    print("[FATAL] SQLite database path not found")
    exit(1)

if config["URL"] is None:
    print("[FATAL] Please set DTA URL in config file")
    exit(1)

if config["DTATOKEN"] is None:
    print("[WARN] DTA token not found. You can't use DTA legacy functions without it. Token will be required in "
          "future versions.")

from aiogram import Dispatcher, executor, types

from aiogram.dispatcher import filters

import werkzeug

werkzeug.cached_property = werkzeug.utils.cached_property
from robobrowser import RoboBrowser

import dbmanager, messenger, dta
import onboarding

from selenium import webdriver

from flask import render_template

dp = Dispatcher(messenger.bot)

@dp.message_handler(commands=['about'], commands_prefix='!/')
async def about(message: types.Message):
    await messenger.edit_or_send(message.from_user.id,
                                 "🤵‍♂️ Kissinger v2.0\n\nGithub: github.com/kispython-ru/kissinger\n\nСделал @aaplnv")


@dp.message_handler((filters.RegexpCommandsFilter(regexp_commands=['task_([0-9]*)'])))
async def send_help(message: types.Message, regexp_command):
    # TODO: User registration must be centralized
    user = await dbmanager.getuser(message.from_user.id)

    await open_task(user, str(int(regexp_command.group(1)) - 1))


@dp.message_handler(commands=['help'], commands_prefix='!/')
async def send_help(message: types.Message):
    await message.reply("🤷 Вопросы и ответы:\n\n"
                        "Q: Как отправить ответ на задание?\n"
                        "A: Откройте карточку задания, скопируйте код в лс боту и просто отправьте его,\n\n"
                        "Q: Задание не принимается. Видимо, телеграмм отформатировал сообщение так, что kispython его не воспринимает. Что делать?\n"
                        "A: Попробуйте заключить код в три апострафа (```) в начале и в конце. Так телеграмм не будет применять markdown на код\n\n"
                        "Q: Как связаться с разработчиками?"
                        "A: Откройте issue в нашем репозитории: https://github.com/aaplnv/Kissinger/issues")


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


async def send_task(gid, vid, taskid, solution):
    await dta.send_task(gid, vid, taskid, solution)


# Bypass official api if you have any problems
async def send_task_bypass(gid, vid, taskid, solution):
    # Create headless browser
    browser = RoboBrowser(user_agent='Kissinger/2.0')

    # Open DTA and insert code to form
    browser.open(f"http://kispython.ru/group/{gid}/variant/{vid}/task/{taskid}")
    form = browser.get_form(
        action=f"/group/{gid}/variant/{vid}/task/{taskid}")
    form  # <RoboForm q=>
    form['code'].value = solution
    browser.submit_form(form)
    # TODO: check is request successful


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
    tasks = await dta.get_alltasks(user)
    keyboard = types.InlineKeyboardMarkup()
    for task in tasks:
        emoji = await emoji_builder(task['status'])
        answer = emoji + f"Задание {(task['id'] + 1)}: {task['status_name']}"
        keyboard.add(
            types.InlineKeyboardButton(text=answer, web_app=types.WebAppInfo(url="https://beta.kissinger.ru/group/{}/var/{}/task/{}".format(user.gid, user.vid, task['id']))))
    await messenger.edit_or_send(user.tid, "👨‍🏫 Ваши успехи в обучении:", keyboard, mid)


async def open_task(user, taskid, mid=0, callid=0):
    # answer string
    answer = "Задание " + str(int(taskid) + 1) + "\n"

    task = await dta.get_task(user, taskid)

    answer += await emoji_builder(task['status']) + task['status_name'] + "\n"
    if task["error_message"] is not None:
        answer += str(task["error_message"]) + "\n"
    #photo = await parse_task(href)

    answer += "Когда сделаете, скопируйте свой код и оправьте мне в виде сообщения сюда, я его проверю"
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(text="<--", callback_data="dashboard")
    )
    if mid == 0 or (task['status'] != 1 and task['status'] != 0):
        mid = await messenger.edit_or_send(user.tid, answer, keyboard, mid)

    if (task['status'] == 3 or task['status'] == 4):
        await dbmanager.applylasttask(user, taskid)

    # Auto update on working
    if task['status'] == 1 or task['status'] == 0:
        await asyncio.sleep(5)
        await open_task(user, taskid, mid, callid)


async def emoji_builder(statuscode):
    emojis = ['⏳ ', '🏃‍♂️💨 ', '✔️ ', '❌ ', '⚪️ ']
    return emojis[statuscode]


async def cut_task(link, vid):
    rslt = ""
    session = AsyncHTMLSession()
    r = await session.get(link)
    recording = False
    for line in r.html.find():
        if line.find(f'#вариант-{str(int(vid) + 1)}'):
            recording = True
            print("Recording started")

        if line.find(f'#вариант-{str(int(vid)+2)}'):
            recording = False
            print("Recording ended")

        if recording:
            rslt += line.html

    return rslt


def startserver():
    from flask import Flask
    from flask import request

    app = Flask(__name__)

    @app.route('/group/<gid>/var/<vid>/task/<tid>', methods=['GET'])
    async def hello(tid: int, vid: int, gid: int):
        task = await dta.get_task(gid, vid, tid)
        return render_template('task.html', tid=tid, vid=vid, gid=gid, source=await cut_task(task['source'], vid), emojistatus=await emoji_builder(task['status']))

    @app.route('/group/<gid>/var/<vid>/task/<tid>', methods=['POST'])
    async def accept(tid: int, vid: int, gid: int):
        jsn = request.get_json()
        user = await dbmanager.getuser(jsn['userid'])
        await send_task(gid, vid, tid, jsn['code'])
        number = int(tid) + 1
        await messenger.answer_query(jsn['query_id'], ("🚀 Вы отправили ответ на задание " + str(number)))
        await open_task(user, str(tid))
        return "OK"

    app.run(host="0.0.0.0")


def main():
    flaskprocess = Process(target=startserver)
    try:
        flaskprocess.start()
    except BaseException:
        print(f"Error occured while starting process {flaskprocess}")

    asyncio.run(executor.start_polling(dp, skip_updates=True))
    asyncio.run(startserver())
    print("[ OK ] Bot started")


if __name__ == '__main__':
    main()

