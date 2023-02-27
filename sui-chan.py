import os
import time
import toml
import logging
import re

from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from dump_log import dump_log
import msgprocessing as msgp
import msgs
import userprocessing as usrp
import youtu
import watch_list

# set log level at main function
# if program will be completed, change to logging.ERROR
# when program should be debugged, change to logging.DEBUG
#logging.basicConfig(level=logging.ERROR)
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

    logger = logging.getLogger(__name__)
    dump_log('clear_command called', logger)

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
        say(msgs.confirm())
        has_more = True
        cursor = None

        while has_more:
            if count <= 0:
                break

            paramdict = { 'limit': min(count, 100), }
            if cursor is None:
                paramdict['latest'] = ts
            else:
                paramdict['cursor'] = cursor
            #msg_list, has_more, cursor = msgp.get_history(ch, client, say, logger, limit=limit, cursor=cursor, latest=ts)
            msg_list, has_more, cursor = msgp.get_history(ch, client, say, logger, **paramdict)

            msgp.clear_history(ch, msg_list, client, logger)
            count -= len(msg_list)
        say(msgs.finish())

# bot status
@app.message(re.compile(f'<@{bot_user_id}> *([W|w]here)'))
def return_joining_channels(say, logger, context):
    '''tell channel names where the bot joins
    
    `@BOTNAME where`
    '''

    logger = logging.getLogger(__name__)
    dump_log('return_joining_channels called', logger)

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


# register watch list
@app.message(re.compile(f'<@{bot_user_id}> *([W|w]atch)'))
def register_this_channel(message, say, logger, context):
    '''register watch list to sqlite3 file
    '''

    logger = logging.getLogger(__name__)

    dump_log('register_this_channel called', logger)

    ch = message['channel']
    watch_list.add_watch_list(ch)

    # 監視開始のメッセージを出力する


# unregister watch list
@app.message(re.compile(f'<@{bot_user_id}> *([U|u]nwatch)'))
def unregister_this_channel(message, say, logger, context):
    '''remove channel from watch list
    '''

    logger = logging.getLogger(__name__)

    dump_log('unregister_this_channel called', logger)

    ch = message['channel']
    watch_list.rm_watch_list(ch)

    # 監視終了のメッセージを出力する


def clear_watch_list():
    '''check watch list channel existance
    '''

    client = WebClient(token=slack_bot_token)
    pass

def get_watch_list():
    '''get watch list
    '''

    pass

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

    logger = logging.getLogger(__name__)
    dump_log('read_playlist called', logger)

    ch = message['channel']
    ts = message['ts']
    matches = context['matches'][0]
    if matches.find('youtube.com') > 0:
        pl_id = matches.replace('>', '').split('=')[-1]
        vids = youtu.get_playlist(pl_id, logger)
    else:
        dump_log('unknown playlist url', logger, 'error')
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

    logger = logging.getLogger(__name__)
    dump_log('check_duplicate called', logger)

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
    # this func needs user token scope
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

    logger = logging.getLogger(__name__)
    dump_log('mklist_message called', logger)

    ch = message['channel']
    ts = message['ts']
    client = WebClient(token=slack_user_token)

    dump_log(str(message), logger, 'debug')
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
    # this func needs user token scope
    msgp.rm_history(ch, ts, client, logger)


# message handling

@app.event('message')
def message_processing(message, logger):
    '''messageの内容に応じた処理を記述
    '''

    logger = logging.getLogger(__name__)
    dump_log('message_processing is called', logger)

    if 'attachments' in message:
        # 添付ファイルつきの処理
        dump_log(str(message), logger, 'debug')
        #dump_log(str(message['attachments']), logger, 'debug')


# debug
@app.message(re.compile(f'<@{bot_user_id}> *read$'))
def read_slack(message, say, logger, context):
    '''read slack message and dump to log
    
    This is a command to debug bot program.
    It might be useless for general user.
    
    `@BOTNAME read`
    '''

    logger = logging.getLogger(__name__)
    dump_log('read_slack called', logger)

    ch = message['channel']
    ts = message['ts']
    client = WebClient(token=slack_user_token)
    if 'thread_ts' in message:
        thread_ts = message['thread_ts']
        msg = msgp.get_message(ch, client, thread_ts, say)
    else:
        thread_ts = None

    dump_log(str([ch, ts, thread_ts]), logger, 'debug')
    dump_log(str(message), logger, 'debug')
    say(str([ch, ts, thread_ts]))
    msgp.rm_history(ch, ts, client, logger)


@app.message(re.compile(f'<@{bot_user_id}> *users$'))
def dump_users(message, say, logger, context):
    '''dump user list to log
    
    `@BOTNAME users`
    '''

    logger = logging.getLogger(__name__)
    dump_log('dump_users called', logger)

    client = WebClient(token=slack_bot_token)
    usrp.get_users(client, logger)


@app.message(re.compile(f'<@{bot_user_id}> *dm$'))
def send_dm(message, say, logger, context):
    '''send DM
    
    `@BOTNAME dm`
    '''

    logger = logging.getLogger(__name__)
    dump_log('send_dm called', logger)

    user_id = message['user']
    msg = 'test message'
    client = WebClient(token=slack_user_token)
    msgp.dm_write(user_id, msg, client, logger)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    #logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(module)s: %(levelname)s: %(message)s')

    # log file
    fh = logging.FileHandler('garie.log')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # watch list db file
    watch_list = watch_list.watch_list_db(config['watch-list']['filename'], logger)

    handler = SocketModeHandler(app, slack_app_token)
    handler.start()
