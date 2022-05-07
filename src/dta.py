import asyncio
import os

import requests
import yaml

config = yaml.safe_load(open(os.environ.get("CONFIG_PATH")))


async def get_alltasks(user):
    r = await make_get_request(f"{config['URL']}group/{user.gid}/variant/{user.vid}/task/list")
    return r.json()


async def get_task(user, taskid):
    r = await make_get_request(f"{config['URL']}group/{user.gid}/variant/{user.vid}/task/{taskid}")
    return r.json()


async def get_task(gid, vid, taskid):
    r = await make_get_request(f"{config['URL']}group/{gid}/variant/{vid}/task/{taskid}")
    return r.json()


async def send_task(gid, vid, taskid, solution):
    if config['DTATOKEN'] is None:
        raise Exception("DTA token is not set")
    r = await make_post_request(f"{config['URL']}group/{gid}/variant/{vid}/task/{taskid}", solution=solution)
    return r.json()


#
# Core method
# TODO: Количество попыток обращения и задержка между обращениями должны быть в конфиге
async def make_get_request(url):
    for i in range(0, 2):
        try:
            result = requests.get(url)
            if result.status_code == 200:
                return result
        except:
            pass
        await asyncio.sleep(2)
    raise Exception("Can't access DTA")


async def make_post_request(url, solution):
    for i in range(0, 2):
        try:
            result = requests.post(url, json={"code": solution},
                                    headers={"Content-Type": "application/json", "token": config['DTATOKEN']})
            if result.status_code == 200:
                return result
        except:
            pass
        await asyncio.sleep(2)
    raise Exception("Can't access DTA")
