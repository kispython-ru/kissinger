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
import yaml
from aiogram import types

import messenger

config = yaml.safe_load(open("config.yml"))


# Send message with variant list
async def select_variant(tid, mid=0):
    r = requests.get(config['URL'] + 'variant/list')
    keyboard = types.InlineKeyboardMarkup(3)
    for variant in r.json():
        keyboard.add(
            types.InlineKeyboardButton(text=variant+1, callback_data="variantselected_" + str(variant))
        )
    keyboard.add(types.InlineKeyboardButton(text="<--", callback_data="variantonboard"))
    await messenger.edit_or_send(tid, "Select your variant", keyboard, mid)


# Send message with group list
async def select_group(tid, prefix, mid=0):
    r = requests.get(config['URL'] + 'group/' + prefix)
    keyboard = types.InlineKeyboardMarkup()
    for group in r.json():
        keyboard.add(
            types.InlineKeyboardButton(text=group["title"], callback_data="variantonboard_" + str(group["id"])))
    keyboard.add(types.InlineKeyboardButton(text="<--", callback_data="prefixonboard"))
    await messenger.edit_or_send(tid, "Select your group", keyboard, mid)


# Send message with prefix list
async def select_prefix(tid, mid=0):
    r = requests.get(config['URL'] + 'group/prefixes')
    keyboard = types.InlineKeyboardMarkup()
    for prefix in r.json()["prefixes"]:
        keyboard.add(types.InlineKeyboardButton(text=prefix, callback_data=("grouponboard_" + prefix)))
    await messenger.edit_or_send(tid, "Select your prefix", keyboard, mid)
