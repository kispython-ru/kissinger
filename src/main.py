import logging
import time

import yaml

from aiogram import Dispatcher, executor, types

from aiogram.dispatcher import filters

import werkzeug

# Так надо
werkzeug.cached_property = werkzeug.utils.cached_property
from robobrowser import RoboBrowser

from src import dbmanager, messenger, dta
import onboarding

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
dp = Dispatcher(messenger.bot)

# TODO: Config initialization must be centralised. And config path put to .env
config = yaml.safe_load(open("src/config.yml"))


@dp.message_handler(commands=['about'], commands_prefix='!/')
async def about(message: types.Message):
    await messenger.edit_or_send(message.from_user.id, "🤵‍♂️ Kissinger v1.1\n\nGithub: github.com/aaplnv/kissinger\n\nСделал @aaplnv")


@dp.message_handler((filters.RegexpCommandsFilter(regexp_commands=['task_([0-9]*)'])))
async def send_help(message: types.Message, regexp_command):
    # TODO: User registration must be centralized
    user = await dbmanager.getuser(message.from_user.id)

    await open_task(user, str(int(regexp_command.group(1)) - 1))


@dp.message_handler(commands=['help'], commands_prefix='!/')
async def send_help(message: types.Message):
    await message.reply("🤷 Вопросы и ответы:\n\n"
                        "Q: Как отправить ответ на задание?\n"
                        "A: Откройте карточку задания, скопируйте код в лс боту и просто отправьте его, лол\n\n"
                        "Q: Задание не принимается. Видимо, телеграмм отформатировал сообщение так, что kispython его не воспринимает. Что делать?\n"
                        "A: Попробуйте заключить код в три апострафа (```) в начале и в конце. Так телеграмм не будет применять markdown на код\n\n"
                        "Q: Как связаться с разработчиками?"
                        "A: @worldbeater по вопросам kispython, @aaplnv по вопросам бота")


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
async def accept_task(message: types.Message):
    # Get user info from db
    user = await dbmanager.getuser(message.from_user.id)

    # TODO: Official send_task support
    try:
        print("Trying to send task")
        await send_task(user.gid, user.vid, user.last_task, message.text, message.entities)
        print("Task sent")
    except Exception as e:
        print("Error sending task")
        print(e)
        await send_task_bypass(user.gid, user.vid, user.last_task, message.text, message.entities)

    # Redirect to task viewer
    await open_task(user, user.last_task)


async def send_task(gid, vid, taskid, solution, entities):
    await dta.send_task(gid, vid, taskid, await undo_telegram_solution_modifications(solution, entities))


# Bypass official api if you have any problems
async def send_task_bypass(gid, vid, taskid, solution, entities):
    # Create headless browser
    browser = RoboBrowser(user_agent='Kissinger/1.0')

    # Open DTA and insert code to form
    browser.open(f"http://kispython.ru/group/{gid}/variant/{vid}/task/{taskid}")
    form = browser.get_form(
        action=f"/group/{gid}/variant/{vid}/task/{taskid}")
    form  # <RoboForm q=>
    form['code'].value = await undo_telegram_solution_modifications(solution, entities)
    browser.submit_form(form)
    # TODO: check is request successful


# Telegram can cut some important characters from your code. But we can fix it.
async def undo_telegram_solution_modifications(solution, entities):
    # TODO: Undo telegram markdown styles

    for entity in entities:
        if entity.type == 'bold':
            solution = solution[:entity.offset] + "** " + solution[entity.offset:(entity.offset + entity.length)] + " **" + solution[entity.offset + entity.length:]
        if entity.type == 'italic':
            solution = solution[:entity.offset] + "* " + solution[entity.offset:(entity.offset + entity.length)] + " *" + solution[entity.offset + entity.length:]
    # Собираю инфу:
    # * и ** выделают код курсивом и жирным. Выход: проверка на стили, восстановление звёздочек в случае обнаружения
    return solution + "\n"


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
            types.InlineKeyboardButton(text=answer, callback_data=f"task_{str(task['id'])}")
        )
    await messenger.edit_or_send(user.tid, "👨‍🏫 Ваши успехи в обучении:", keyboard, mid)


async def open_task(user, taskid, mid=0, callid=0):
    # answer string
    answer = "Задание " + str(int(taskid) + 1) + "\n"

    task = await dta.get_task(user, taskid)

    href = task['source']

    answer += await emoji_builder(task['status']) + task['status_name'] + "\n"
    if task["error_message"] is not None:
        answer += str(task["error_message"])+"\n"
    answer += await parse_task(href)

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
        time.sleep(5)
        await open_task(user, taskid, mid, callid)


async def parse_task(url):
    # TODO: Use RoboBrowser, parse information and paste it here
    # if domain = sovietov.com ==> parse; else:
    return "Условие: " + url + "\n\n"


async def emoji_builder(statuscode):
    emojis = ['⏳ ', '🏃‍♂️💨 ', '✔️ ', '❌ ', '⚪️ ']
    return emojis[statuscode]


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
