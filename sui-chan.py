import os
import os.path
import time
import toml
import logging
import re
import urllib.request
import urllib.error

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
loglevel = logging.DEBUG
#loglevel = logging.INFO
#loglevel = logging.ERROR

logfile = 'suisei.log'

formatter = logging.Formatter('%(asctime)s %(module)s: %(levelname)s: %(message)s')

config = toml.load(open('secret.toml'))

# slack bot settings
slack_app_token = config['slackbot']['token']
# user = hadacchi, this token grant as hadacchi to bot
slack_user_token = config['slackbot']['user_oauth_access_token']
# bot user = suisei, this token only grant as suisei to bot
slack_bot_token = config['slackbot']['bot_user_oauth_access_token']

# resources
data_dir_path = config['resource']['data_dir_path']
watch_list_filename = config['resource']['watch_list_filename']
watch_list_path = f'{data_dir_path}/{watch_list_filename}'

# this is keyword when this bot mentioned
client = WebClient(token=slack_bot_token)
bot_user_id = client.auth_test()['user_id']
del client

app = App(token=slack_bot_token)

# functions
def logger_setup(logger):
    '''setup logger

    Parameters
    ----------
    logger : logging.Logger

    Return
    ------
    logger : logging.Logger
    '''

    logger.setLevel(loglevel)
    fh = logging.FileHandler(logfile)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def clear_watch_list():
    '''check watch list channel existance
    '''

    #client = WebClient(token=slack_bot_token)
    pass


def get_watch_list_ids():
    '''get watch list
    '''

    return [r[0] for r in watch_list.get_watch_list()]


def get_file(url, dirpath):
    '''get web file

    Parameters
    ----------
    url : string
    dirpath : string
        directory path where the file will be stored
    '''

    try:
        with urllib.request.urlopen(url) as web_object:
            data = web_object.read()
            target_name = os.path.basename(url).split('?')[0]
            target_path = f'{dirpath}/{target_name}'
            if os.path.exists(target_path):
                logger.warn(f'{target_path} has existed already.')
            else:
                logger.debug(f'write {target_path}')
                os.makedirs(dirpath, exist_ok=True)
                with open(target_path, 'wb') as target_object:
                    target_object.write(data)
    except urllib.error.URLError as e:
        logger.error(str(e))


### event API ###

# slack message control
@app.message(re.compile(f'<@{bot_user_id}> *clear *([^ ]*)$'))
def clear_command(message, say, context):
    '''remove message in the channel

    `@BOTNAME clear [all|NUM]`

    where `NUM` is the number that you want to remove.

    If you type this command in a channel, bot remove channel messages.
    Target message has replies, this command also remove them.

    If you type this command in a thread, bot remove all replies in the thread and
    thread head message.
    In this case, any `OPTIONS` are ignored, and remove all replies.
    '''

    logger = logger_setup(logging.getLogger(__name__))

    logger.debug('clear_command called')

    matches = context['matches'][0]
    if matches == '':
        count = 100
    elif matches == 'all':
        count = 99999999
    elif matches.isdigit():
        count = int(matches)
    else:
        logger.error('Invalid number {matches}')
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
def return_joining_channels(say, context, message):
    '''tell channel names where the bot joins
    
    `@BOTNAME where`
    '''

    logger = logger_setup(logging.getLogger(__name__))

    logger.debug('return_joining_channels called')
    logger.debug(message['text'])

    client = WebClient(token=slack_bot_token)
    chlist = client.conversations_list()['channels']
    id_name = {ch['id']: ch['name'] for ch in chlist}

    channels = []

    if message['text'].find('watch') >= 0:
        watch_list_ids = get_watch_list_ids()

        for chid in watch_list_ids:
            if chid in id_name.keys():
                channels.append(id_name[chid])
        if len(channels) > 0:
            say(msgs.imin().format('\n'.join(channels)))
        else:
            say(msgs.noplace())

    else:
        # if you want only channels, ch['is_channel'] will be good filter
        for ch in chlist:
            members = client.conversations_members(channel=ch['id'])['members']
            if bot_user_id in members:
                channels.append(ch['name'])
        if len(channels) > 0:
            say(msgs.imin().format('\n'.join(channels)))
        else:
            say(msgs.noplace())


# register watch list
@app.message(re.compile(f'<@{bot_user_id}> *([W|w]atch)'))
def register_this_channel(message, say, context):
    '''register watch list to sqlite3 file
    '''

    logger = logger_setup(logging.getLogger(__name__))

    logger.debug('register_this_channel called')

    ch = message['channel']
    watch_list.add_watch_list(ch)

    # 監視開始のメッセージを出力する
    return


# unregister watch list
@app.message(re.compile(f'<@{bot_user_id}> *([U|u]nwatch)'))
def unregister_this_channel(message, say, context):
    '''remove channel from watch list
    '''

    logger = logger_setup(logging.getLogger(__name__))

    logger.debug('unregister_this_channel called')

    ch = message['channel']
    watch_list.rm_watch_list(ch)

    # 監視終了のメッセージを出力する
    return



# YouTube playlist handling
# For this bot, a thread is a playlist and replies of the thread are playlist
# items.
@app.message(re.compile(f'<@{bot_user_id}> *pick *([^ ]*)$'))
def read_playlist(message, say, context):
    '''read your playlist or public playlist
    
    `@BOTNAME pick URL`,  
    where `URL` is a playlist URL.
    
    Acceptable format is `https://youtube.com/playlist?list=PLAYLIST_ID`.
    Any other QUERY_STRING is not acceptable.
    
    Playlist items are written as replies of pick command.
    If you type this command in a thread, bot adds items to the thread.
    '''

    logger = logger_setup(logging.getLogger(__name__))
    logger.debug('read_playlist called')

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
def check_duplicate(message, say, context):
    '''check duplicate item in a thread

    `@BOTNAME check`

    If there are duplicate items in a thread, video ids and ordinal numbers of
    them are written in the thread. Then 1st items are not written.
    '''

    logger = logger_setup(logging.getLogger(__name__))
    logger.debug('check_duplicate called')

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
def mklist_message(message, say, context):
    '''make playlist with replies
    
    `@BOTNAME playlist`
    
    Make playlist. Name of it is thread head message. Items of it are replies of
    the thread.
    Acceptable video URL is
    `https://youtu.be/VIDEO_ID`
    or `https://www.youtube.com/watch?v=VIDEO_ID`.
    '''

    logger = logger_setup(logging.getLogger(__name__))
    logger.debug('mklist_message called')

    ch = message['channel']
    ts = message['ts']
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
    # this func needs user token scope
    msgp.rm_history(ch, ts, client, logger)


# message handling

#@app.event('message')
#def message_processing(message):
#    '''messageの内容に応じた処理を記述
#    '''
#
#    logger = logger_setup(logging.getLogger(__name__))
#    logger.debug('message_processing is called')
#
#    watch_list_ids = get_watch_list_ids()
#    if message['channel'] not in watch_list_ids:
#        return
#
#    logger.debug('this channel is monitored')
#    logger.debug(str(message))
#
#    #if 'attachments' in message:
#    #    # 添付ファイルつきの処理
#    #    dump_log(str(message), logger, 'debug')
#    #    #dump_log(str(message['attachments']), logger, 'debug')


# debug
@app.message(re.compile(f'<@{bot_user_id}> *scan *([^ ]*)$'))
def scan_messages(message, say, context):
    '''read slack message and perform debug action

    `@BOTNAME scan`
    '''

    logger.debug('scan_slack called')

    ch = message['channel']
    ts = message['ts']
    client = WebClient(token=slack_user_token)

    matches = context['matches'][0]
    if matches.isdigit():
        count = int(matches)

    if 'thread_ts' in message:
        # this is reply
        thread_ts = message['thread_ts']
    else:
        thread_ts = None

    # debug action: store attachment
    # scan history
    logger.info(f'scan {count}')
    msgs, has_more, cursor = msgp.get_history(
            ch,
            client,
            say,
            logger,
            count,
            latest=ts
            )

    # skip bot message
    history = [m for m in msgs if m['user'] != bot_user_id]

    targetlist = []
    for h in history:
        if 'attachments' in h:
            for a in h['attachments']:
                if 'image_url' in a:
                    # name, userid, image url
                    targetlist.append([a['author_name'], a['author_subname'], a['image_url']])
                if 'video_html' in a:
                    if a['video_html'].find('src="') > 0:
                        videosrc = a['video_html'].split('src="')[1].split('"')[0]
                    # name, userid, video src
                    targetlist.append([a['author_name'], a['author_subname'], videosrc])

    for author, author_id, url in targetlist:
        author_dir_name = f'{data_dir_path}/{author}({author_id})'
        logger.debug(f'store {url} to {author_dir_name}')
        get_file(url, author_dir_name)
    logger.debug('completed')

    #logger.debug(str([ch, ts, thread_ts]))
    #logger.debug(str(message))
    #say(str([ch, ts, thread_ts]))
    #msgp.rm_history(ch, ts, client, logger)


@app.message(re.compile(f'<@{bot_user_id}> *read$'))
def read_slack(message, say, context):
    '''read slack message and dump to log
    
    This is a command to debug bot program.
    It might be useless for general user.
    
    `@BOTNAME read`
    '''

    logger = logger_setup(logging.getLogger(__name__))
    logger.debug('read_slack called')

    ch = message['channel']
    ts = message['ts']
    client = WebClient(token=slack_user_token)
    if 'thread_ts' in message:
        thread_ts = message['thread_ts']
        msg = msgp.get_message(ch, client, thread_ts, say)
    else:
        thread_ts = None

    logger.debug(str([ch, ts, thread_ts]))
    logger.debug(str(message))
    say(str([ch, ts, thread_ts]))
    msgp.rm_history(ch, ts, client, logger)


@app.message(re.compile(f'<@{bot_user_id}> *users$'))
def dump_users(message, say, context):
    '''dump user list to log
    
    `@BOTNAME users`
    '''

    logger = logger_setup(logging.getLogger(__name__))
    logger.debug('dump_users called')

    client = WebClient(token=slack_bot_token)
    usrp.get_users(client, logger)


@app.message(re.compile(f'<@{bot_user_id}> *dm$'))
def send_dm(message, say, context):
    '''send DM
    
    `@BOTNAME dm`
    '''

    logger = logger_setup(logging.getLogger(__name__))
    logger.debug('send_dm called')

    user_id = message['user']
    msg = 'test message'
    client = WebClient(token=slack_user_token)
    msgp.dm_write(user_id, msg, client, logger)


if __name__ == "__main__":
    logger = logger_setup(logging.getLogger(__name__))

    # watch list db file
    watch_list = watch_list.watch_list_db(watch_list_path, logger)

    handler = SocketModeHandler(app, slack_app_token)
    handler.start()
