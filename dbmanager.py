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
async def record_gid(session, user, gid):
    user.gid = int(gid)
    session.commit()


# write (override) variant id for specified user
async def record_vid(session, user, vid):
    user.vid = int(vid)
    session.commit()
