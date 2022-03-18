#              _                         _ _
#             | |                       | (_)
#   ___  _ __ | |__   ___   __ _ _ __ __| |_ _ __   __ _
#  / _ \| '_ \| '_ \ / _ \ / _` | '__/ _` | | '_ \ / _` |
# | (_) | | | | |_) | (_) | (_| | | | (_| | | | | | (_| |
#  \___/|_| |_|_.__/ \___/ \__,_|_|  \__,_|_|_| |_|\__, |
#                                                   __/ |
#                                                  |___/

#
# Cute and user-friendly registration described here
#

import requests
from aiogram import types

from main import bot, config


# Send message with variant list
async def select_variant(tid, mid=0):
    r = requests.get(config['URL'] + 'variant/list')
    keyboard = types.InlineKeyboardMarkup(3)
    for variant in r.json():
        keyboard.add(
            types.InlineKeyboardButton(text=variant+1, callback_data="variantselected_" + str(variant))
        )
    keyboard.add(types.InlineKeyboardButton(text="<--", callback_data="variantonboard"))
    if mid != 0:
        await bot.edit_message_text(chat_id=tid, message_id=mid, reply_markup=keyboard, text="Select your variant")
    else:
        await bot.send_message(chat_id=tid, reply_markup=keyboard, text="Select your variant")


# Send message with group list
async def select_group(tid, prefix, mid=0):
    r = requests.get(config['URL'] + 'group/' + prefix)
    keyboard = types.InlineKeyboardMarkup()
    for group in r.json():
        keyboard.add(
            types.InlineKeyboardButton(text=group["title"], callback_data="variantonboard_" + str(group["id"])))
    keyboard.add(types.InlineKeyboardButton(text="<--", callback_data="prefixonboard"))
    if mid != 0:
        await bot.edit_message_text(chat_id=tid, message_id=mid, reply_markup=keyboard, text="Select your group")
    else:
        await bot.send_message(chat_id=tid, reply_markup=keyboard, text="Select your group")


# Send message with prefix list
async def select_prefix(tid, mid=0):
    r = requests.get(config['URL'] + 'group/prefixes')
    keyboard = types.InlineKeyboardMarkup()
    for prefix in r.json()["prefixes"]:
        keyboard.add(types.InlineKeyboardButton(text=prefix, callback_data=("grouponboard_" + prefix)))

    if mid is not 0:
        await bot.edit_message_text(chat_id=tid, message_id=mid, reply_markup=keyboard, text="Select your prefix")
    else:
        await bot.send_message(chat_id=tid, reply_markup=keyboard, text="Select your prefix")