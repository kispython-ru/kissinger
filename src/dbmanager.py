#      _ _
#     | | |
#   __| | |__  _ __ ___   __ _ _ __   __ _  __ _  ___ _ __
#  / _` | '_ \| '_ ` _ \ / _` | '_ \ / _` |/ _` |/ _ \ '__|
# | (_| | |_) | | | | | | (_| | | | | (_| | (_| |  __/ |
#  \__,_|_.__/|_| |_| |_|\__,_|_| |_|\__,_|\__, |\___|_|
#                                           __/ |
#                                          |___/

#
# Here I describe some syntactic sugar.
# Have you seen news? More sugar!
#

# write (override) group id for specified user
import yaml
from sqlalchemy.orm import Session
import sqlalchemy as db

import onboarding
from models import User

config = yaml.safe_load(open("src/config.yml"))
# Initialize database
engine = db.create_engine(config['SQLITE'])
session = Session(bind=engine)


# Write (override) group id to current user
async def record_gid(user, gid):
    user.gid = int(gid)
    session.commit()


# Write (override) variant id for specified user
async def record_vid(user, vid):
    user.vid = int(vid)
    session.commit()


# Get userinfo from database (register if it's new user)
async def getuser(tid):
    user = await getuserraw(tid)
    if user is None:
        await register(tid)
        raise Exception("notregistered") # TODO: fix govnocod
    if user.gid is None or user.vid is None:
        await onboarding.select_prefix(tid)
        raise Exception("notonboarded")
    return user


# Get user by telegram id sql query
async def getuserraw(tid):
    return session.query(User).filter_by(tid=tid).first()


# Register new user
async def register(tid):
    session.add(User(
        tid=tid,
    ))
    session.commit()
    await onboarding.select_prefix(tid)


# Reset all settings for specific user
async def resetuser(user):
    user.vid = None
    user.gid = None
    user.last_task = None
    session.commit()


async def applylasttask(user, taskid):
    user.last_task = taskid
    session.commit()
