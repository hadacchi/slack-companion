import os
import toml
import logging
import re

from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import msgprocessing as msgp
import msgs

# set log level at main function
# if program will be completed, change to logging.ERROR
# when program should be debugged, change to logging.DEBUG
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

# イベント API


@app.message(re.compile(f'<@{bot_user_id}> *pick$'))
def pick_message(message, say, logger, context):
    '''pick message from the ch
    '''

    ch = message['channel']
    ts = message['ts']
    #client = WebClient(token=slack_bot_token)
    client = WebClient(token=slack_user_token)

    logger.error(str(message))
    #say(msgs.confirm())


    count = 5

    while True:
        if count <= 0:
            break
        limit = min(count, 100)
        respond, msg_list, has_more = msgp.get_history(
            ch, client, say, logger, latest=ts, limit=limit)
        if respond is None:
            break

        #logger.debug(str(msg_list))
        replies = msgp.get_replies(message['channel'], msg_list, client, logger)
        #logger.debug(str(replies))
        count -= len(msg_list)

        if has_more:
            continue
        break

    msgp.rm_history(ch, ts, client, logger)


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
    elif matches[1:].isnumeric():
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
    #logger.setLevel(logging.INFO)
    logger.setLevel(logging.DEBUG)

    # log file
    #fh = logging.FileHandler('garie.log')
    #logger.addHandler(fh)

    handler = SocketModeHandler(app, slack_app_token)
    handler.start()
