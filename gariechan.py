import os
import time
import toml
import logging
import re

from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import msgprocessing as msgp
import msgs
import youtu

# set log level at main function
# if program will be completed, change to logging.ERROR
# when program should be debugged, change to logging.DEBUG
logging.basicConfig(level=logging.ERROR)
#logging.basicConfig(level=logging.INFO)
#logging.basicConfig(level=logging.DEBUG)

config = toml.load(open('secret.toml'))

slack_app_token = config['socket-mode']['token']

# user = hadacchi, this token grant as hadacchi to bot
slack_user_token = config['socket-mode']['user_oauth_access_token']
# bot user = garie, this token only grant as garie to bot
slack_bot_token = config['socket-mode']['bot_user_oauth_access_token']

# this is keyword when this bot mentioned
client = WebClient(token=slack_bot_token)
bot_user_id = client.auth_test()['user_id']
del client

app = App(token=slack_bot_token)

### event API ###

# slack message control
@app.message(re.compile(f'<@{bot_user_id}> *clear *([^ ]*)$'))
def clear_command(message, say, logger, context):
    '''remove message in the channel

    `@BOTNAME clear [all|NUM]`

    where `NUM` is the number that you want to remove.

    If you type this command in a channel, bot remove channel messages.
    Target message has replies, this command also remove them.

    If you type this command in a thread, bot remove all replies in the thread and
    thread head message.
    In this case, any `OPTIONS` are ignored, and remove all replies.
    '''

    matches = context['matches'][0]
    if matches == '':
        count = 100
    elif matches == 'all':
        count = 99999999
    elif matches.isdigit():
        count = int(matches)
    else:
        logging.error('Invalid number {matches}')
        say(msgs.error())
        return

    ch = message['channel']
    client = WebClient(token=slack_user_token)

    if 'thread_ts' in message:
        # this command called in reply
        msgp.clear_replies(ch, message['thread_ts'], count, client, logger)
        # ここにthread_tsを消す処理を追加する
    else:
        ts = message['ts']
        #say(msgs.confirm())
        has_more = True

        while has_more:
            if count <= 0:
                break

            limit = min(count, 100)
            msg_list, has_more, cursor = msgp.get_history(ch, client, say, logger, limit=limit)  #, latest=ts)

            msgp.clear_history(ch, msg_list, client, logger)
            count -= len(msg_list)

# bot status
@app.message(re.compile(f'<@{bot_user_id}> *([W|w]here)'))
def return_joining_channels(say, logger, context):
    '''tell channel names where the bot joins

    `@BOTNAME where`
    '''

    client = WebClient(token=slack_bot_token)

    # if you want only channels, ch['is_channel'] will be good filter

    channels = []

    for ch in client.conversations_list()['channels']:
        members = client.conversations_members(channel=ch['id'])['members']
        if bot_user_id in members:
            channels.append(ch['name'])
    if len(channels) > 0:
        say(msgs.imin().format('\n'.join(channels)))
    else:
        say(msgs.noplace())


# YouTube playlist handling
# For this bot, a thread is a playlist and replies of the thread are playlist
# items.
@app.message(re.compile(f'<@{bot_user_id}> *pick *([^ ]*)$'))
def read_playlist(message, say, logger, context):
    '''read your playlist or public playlist
    
    `@BOTNAME pick URL`,  
    where `URL` is a playlist URL.
    
    Acceptable format is `https://youtube.com/playlist?list=PLAYLIST_ID`.
    Any other QUERY_STRING is not acceptable.
    
    Playlist items are written as replies of pick command.
    If you type this command in a thread, bot adds items to the thread.
    '''

    ch = message['channel']
    ts = message['ts']
    matches = context['matches'][0]
    if matches.find('youtube.com') > 0:
        pl_id = matches.replace('>', '').split('=')[-1]
        vids = youtu.get_playlist(pl_id, logger)
    else:
        logger.error('unknown playlist url')
        vids = []

    if len(vids) > 0:
        for vid in vids:
            say(f'https://www.youtube.com/watch?v={vid}', thread_ts=ts)
            time.sleep(1)


@app.message(re.compile(f'<@{bot_user_id}> *check$'))
def check_duplicate(message, say, logger, context):
    '''check duplicate item in a thread

    `@BOTNAME check`

    If there are duplicate items in a thread, video ids and ordinal numbers of
    them are written in the thread. Then 1st items are not written.
    '''

    if 'thread_ts' in message:
        ch = message['channel']
        ts = message['ts']
        client = WebClient(token=slack_user_token)
        thread_ts = message['thread_ts']
        listname, video_ids, dup = msgp.get_video_ids_from_replies(
            ch, thread_ts, client, logger)

        if len(dup) > 0:
            say(msgs.dup().format('\n'.join([f'No.{i+1}: `{vid}`' for vid, i in dup])), thread_ts=thread_ts)

    # delete command message
    msgp.rm_history(ch, ts, client, logger)


@app.message(re.compile(f'<@{bot_user_id}> *playlist$'))
def mklist_message(message, say, logger, context):
    '''make playlist with replies
    
    `@BOTNAME playlist`
    
    Make playlist. Name of it is thread head message. Items of it are replies of
    the thread.
    Acceptable video URL is
    `https://youtu.be/VIDEO_ID`
    or `https://www.youtube.com/watch?v=VIDEO_ID`.
    '''

    ch = message['channel']
    ts = message['ts']
    #client = WebClient(token=slack_bot_token)
    client = WebClient(token=slack_user_token)

    logger.debug(str(message))
    # say(msgs.confirm(),thread_ts=ts)

    if 'thread_ts' in message:
        # pick command is in the thread
        # now, search the thread
        thread_ts = message['thread_ts']
        listname, video_ids, dup = msgp.get_video_ids_from_replies(
            ch, thread_ts, client, logger)

        if len(dup) > 0:
            say(msg.dup().format('\n'.join([f'No.{i+1}: `{vid}`' for vid, i in dup])), thread_ts=thread_ts)

        response = youtu.make_playlist(listname, logger)

        youtu.insert_video_to_playlist(response['id'], video_ids, logger)


    # delete command message
    msgp.rm_history(ch, ts, client, logger)


# debug
@app.message(re.compile(f'<@{bot_user_id}> *read$'))
def read_slack(message, say, logger,context):
    '''read slack message and dump to log
    
    This is a command to debug bot program.
    It might be useless for general user.
    
    `@BOTNAME read`
    '''

    ch = message['channel']
    ts = message['ts']
    client = WebClient(token=slack_user_token)
    if 'thread_ts' in message:
        thread_ts = message['thread_ts']
        msg = msgp.get_message(ch, client, thread_ts, say)
    else:
        thread_ts = None

    logger.error(str([ch, ts, thread_ts]))
    say(str([ch, ts, thread_ts]))
    msgp.rm_history(ch, ts, client, logger)


@app.event('message')
def nop(message, logger):
    '''dump debug message when any message is posted in the slack
    '''

    logger.debug(str(message))


if __name__ == "__main__":
    logger = logging.getLogger()
    # logger.setLevel(logging.INFO)
    # logger.setLevel(logging.DEBUG)

    # log file
    fh = logging.FileHandler('garie.log')
    logger.addHandler(fh)

    handler = SocketModeHandler(app, slack_app_token)
    handler.start()
