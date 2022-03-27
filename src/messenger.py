#
#
#  _ __ ___   ___  ___ ___  ___ _ __   __ _  ___ _ __
# | '_ ` _ \ / _ \/ __/ __|/ _ \ '_ \ / _` |/ _ \ '__|
# | | | | | |  __/\__ \__ \  __/ | | | (_| |  __/ |
# |_| |_| |_|\___||___/___/\___|_| |_|\__, |\___|_|
#                                      __/ |
#                                     |___/

#
#
# Just cover on telegram api library with resolutions of most known problems with telegram bot api
#

import yaml
from aiogram import Bot

# Init telegram bot api
# TODO: Config initialization must be centralised. And config path put to .env
config = yaml.safe_load(open("src/config.yml"))
bot = Bot(token=config['TOKEN'])


# Edit existed message or send new
# TODO: Send new message on error with edit_message function
async def edit_or_send(tid, text, keyboard=None, mid=0):
    if mid != 0:
        await bot.edit_message_text(chat_id=tid, message_id=mid, reply_markup=keyboard, text=text)
    else:
        await bot.send_message(chat_id=tid, reply_markup=keyboard, text=text)


async def popup_error(callid, text):
    await bot.answer_callback_query(callid, text)