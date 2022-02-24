import os
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
# logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)

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

# event API

@app.message(re.compile(f'<@{bot_user_id}> *check$'))
def check_duplicate(message, say, logger, context):
    '''search thread for duplicated items.

    this function work only if called from conversation reply.
    '''


    if 'thread_ts' in message:
        ch = message['channel']
        client = WebClient(token=slack_user_token)
        thread_ts = message['thread_ts']
        listname, video_ids, dup = msgp.get_video_ids_from_replies(
            ch, thread_ts, client, logger)

        if len(dup) > 0:
            say(msgs.dup().format('\n'.join([f'No.{i+1}: `{vid}`' for vid, i in dup])), thread_ts=thread_ts)

    # delete command message
    #msgp.rm_history(ch, ts, client, logger)


@app.message(re.compile(f'<@{bot_user_id}> *playlist$'))
def pick_message(message, say, logger, context):
    '''pick message from the ch
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
    #msgp.rm_history(ch, ts, client, logger)


@app.message(re.compile(f'<@{bot_user_id}> *clear *([^ ]*)$'))
def handle_message_events(message, say, logger, context):
    '''clear all histories
    '''
    ts = message['ts']
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
    say(msgs.confirm())

    client = WebClient(token=slack_user_token)

    while True:
        if count <= 0:
            break

        limit = min(count, 100)
        respond, msg_list, has_more = msgp.get_history(
            message['channel'], client, say, logger, latest=ts, limit=limit)
        if respond is None:
            break

        respond = msgp.clear_history(
            message['channel'], msg_list, client, logger)
        count -= len(msg_list)

        if has_more:
            continue
        break

    if respond is not None:
        # last respond is output
        say(respond)


@app.message(re.compile(f'<@{bot_user_id}> *([W|w]here)'))
def return_joining_channels(say, logger, context):
    '''return channels where gariechan joins
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


@app.event('message')
def nop(message, logger):
    logger.debug(str(message))


if __name__ == "__main__":
    # if program will be completed, change to logging.ERROR
    # when program should be debugged, change to logging.DEBUG
    logger = logging.getLogger()
    # logger.setLevel(logging.INFO)
    # logger.setLevel(logging.DEBUG)

    # log file
    fh = logging.FileHandler('garie.log')
    logger.addHandler(fh)

    handler = SocketModeHandler(app, slack_app_token)
    handler.start()
