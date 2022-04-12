#
# Cute and user-friendly registration described here
#
import os

import requests
import yaml
from aiogram import types

import messenger

config = yaml.safe_load(open(os.environ.get("CONFIG_PATH")))


# Send message with variant list
async def select_variant(tid, mid=0):
    r = requests.get(f"{config['URL']}variant/list")

    indexer = 1
    if len(r.json()) % 4 == 0:
        indexer = 4
    elif len(r.json()) % 3 == 0:
        indexer = 3
    elif len(r.json()) % 2 == 0:
        indexer = 2

    keyboard = types.InlineKeyboardMarkup(indexer)
    row = []
    for variant in r.json():
        row.append(types.InlineKeyboardButton(text=variant + 1, callback_data="variantselected_" + str(variant)))
        if len(row) == indexer:
            keyboard.row(*row)
            row = []
    keyboard.add(types.InlineKeyboardButton(text="<--", callback_data="prefixonboard"))
    await messenger.edit_or_send(tid, "🗂️ Выберите свой вариант", keyboard, mid)


# Send message with group list
async def select_group(tid, prefix, mid=0):
    r = requests.get(f"{config['URL']}group/{prefix}")
    keyboard = types.InlineKeyboardMarkup()
    for group in r.json():
        keyboard.add(
            types.InlineKeyboardButton(text=group["title"], callback_data="variantonboard_" + str(group["id"])))
    keyboard.add(types.InlineKeyboardButton(text="<--", callback_data="prefixonboard"))
    await messenger.edit_or_send(tid, "🤔 Выберите свою группу", keyboard, mid)


# Send message with prefix list
async def select_prefix(tid, mid=0):
    r = requests.get(f"{config['URL']}group/prefixes")
    keyboard = types.InlineKeyboardMarkup()
    for prefix in r.json()["prefixes"]:
        keyboard.add(types.InlineKeyboardButton(text=prefix + "  ➡️", callback_data=("grouponboard_" + prefix)))
    await messenger.edit_or_send(tid, "🤔 Выберите свою группу", keyboard, mid)
