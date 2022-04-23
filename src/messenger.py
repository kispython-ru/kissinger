#
# Just cover on telegram api library with resolutions of most known problems
#
import os

import yaml
from aiogram import Bot

# Init telegram bot api
# TODO: Config initialization must be centralised. And config path put to .env
from aiogram.utils.exceptions import MessageNotModified

print('Telegram API initialization...')
config = yaml.safe_load(open(os.environ.get("CONFIG_PATH")))
bot = Bot(token=config['TGTOKEN'])


# Edit existed message or send new
async def edit_or_send(tid, text, keyboard=None, mid=0):
    if mid != 0:
        try:
            await bot.edit_message_text(chat_id=tid, message_id=mid, reply_markup=keyboard, text=text)
            return mid
        except MessageNotModified:
            pass
        except:
            return (await bot.send_message(chat_id=tid, reply_markup=keyboard, text=text)).message_id
    else:
        return (await bot.send_message(chat_id=tid, reply_markup=keyboard, text=text)).message_id


async def edit_or_send_photo(tid, text, photo, keyboard=None, mid=0):
    if mid != 0:
        try:
            await bot.edit_message_photo(chat_id=tid, message_id=mid, photo=photo, reply_markup=keyboard, caption=text)
            return mid
        except MessageNotModified:
            pass
        except:
            return (await bot.send_photo(chat_id=tid, photo=photo, reply_markup=keyboard, caption=text)).message_id
    else:
        return (await bot.send_message(chat_id=tid, photo=photo, reply_markup=keyboard, caption=text)).message_id


async def popup_error(callid, text):
    await bot.answer_callback_query(callid, text)