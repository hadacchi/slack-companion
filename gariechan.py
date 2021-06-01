import os
import toml
import logging
import re

from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import msgprocessing as msgp
import msgs

# if program will be completed, change to logging.ERROR
# when program should be debugged, change to logging.DEBUG
logging.basicConfig(level=logging.INFO)
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

# イベント API
@app.message(re.compile('^clear ([^ ]*)$'))
def handle_message_events(message, say, logger, context):
    '''clear all histories
    '''
    ts = message['ts']
    matches = context['matches'][0]
    if matches == '':
        count = 100
    elif matches == ' all':
        count = 99999999
    elif matches[1:].isnumeric():
        count = int(matches)
    else:
        logging.error('Invalid number {matches}')
        say(msgs.error())
        return

    client = WebClient(token=slack_user_token)

    while True:
        if count <= 0:
            break

        limit = min(count,100)
        respond, msg_list, has_more = msgp.get_history( message['channel']
                                                    , client
                                                    , logger
                                                    , latest=ts
                                                    , limit=limit
                                                    )
        say(respond)

        respond = msgp.clear_history( message['channel']
                                    , msg_list
                                    , client
                                    , logger
                                    )
        say(respond)
        count -= len(msg_list)
        if has_more:
            continue
        break

    if respond is not None:
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
    if len(channels)>1:
        say('\n'.join(channels))
    elif len(channels) == 1:
        say(channels[0])
    else:
        say('No')

@app.event('message')
def nop(message, logger):
    logger.debug(str(message))

if __name__ == "__main__":
    handler = SocketModeHandler(app, slack_app_token)
    handler.start()
