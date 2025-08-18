import os
import os.path
import time
import toml
import logging
import re
import importlib
#import tracemalloc

from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import mylogger
import msgprocessing as msgp
import msgs_allora as msgs

# plugins
## 思ったより専有メモリが小さいので，ずっとインポートしておく
import plugins.ap as ap

'''slack bot

Usage:
    @BOTNAME COMMAND [SUBCOMMAND] [OPTION]

Example:
    @BOTNAME slack  --  slack domain
                    clear  --  remove message in the channel
                          all  --  remove all messages in the channel
                          n    --  remove n messages in the channel
                    where  --  output all channel names where BOT joins
'''

##################
# configurations #
##################

# load config file
config = toml.load(open('secret.toml'))

# tokens
## slack bot settings
slack_app_token = config['slackbot']['token']
## user = hadacchi, this token grant as hadacchi to bot
slack_user_token = config['slackbot']['user_oauth_access_token']
## bot user , this token only grant to bot
slack_bot_token = config['slackbot']['bot_user_oauth_access_token']

# bot user id
client = WebClient(token=slack_bot_token)
bot_user_id = client.auth_test()['user_id']
del client

# loggerのセットアップは起動時に一度だけ行う
mylogger.setup_logging(logging.INFO)  # DEBUG, INFO, ERROR
logger = logging.getLogger(__name__)

####################
# common functions #
####################

splitter = re.compile(r'\s+')

app = App(token=slack_bot_token)

def escape_filename(filename):
    '''change chars for '-' which cannot use for filename
    '''
    # WindowsやLinux/macOSでファイル名として使えない文字を置換するよ！
    # \ / : * ? " < > | と、制御文字(0x00-0x1f)が対象だよ。
    return re.sub(r'[\\/:"*?<>|\x00-\x1f]', '-', filename)

###########################
# embeded slack functions #
###########################

def get_chname_from_id(idlist):
    '''return channel name from id list
    '''

    client = WebClient(token=slack_bot_token)
    chlist = client.conversations_list()['channels']
    id_name = {ch['id']: ch['name'] for ch in chlist}
    return {chid: id_name[chid] for chid in idlist if chid in id_name.keys()}

def return_joining_channels(message, say):
    '''tell channel names where the bot joins
    
    `@BOTNAME slack where`

    Parameters
    ----------
    message: Object
    say: Object
    '''

    logger.debug('return_joining_channels called')

    client = WebClient(token=slack_bot_token)
    chlist = client.conversations_list()['channels']
    id_name = {ch['id']: ch['name'] for ch in chlist}

    channels = []

    # if you want only channels, ch['is_channel'] will be good filter
    for ch in chlist:
        members = client.conversations_members(channel=ch['id'])['members']
        if bot_user_id in members:
            channels.append(ch['name'])
    if len(channels) > 0:
        say(msgs.imin().format('\n'.join(channels)))
    else:
        say(msgs.noplace())

def clear_command(message, say, attrs):
    '''remove message in the channel

    `@BOTNAME slack clear [all|NUM]`

    where `NUM` is the number that you want to remove.

    If you type this command in a channel, bot remove channel messages.
    Target message has replies, this command also remove them.

    If you type this command in a thread, bot remove all replies in the thread and
    thread head message.
    In this case, any `OPTIONS` are ignored, and remove all replies.

    Parameters
    ----------
    message: Object
    say: Object
    attrs: list
    '''

    logger.debug('clear_command called')

    if len(attrs) == 1:
        count = 100
    else:
        if attrs[1] == 'all':
            count = 99999999
        elif attrs[1].isdigit():
            count = int(attrs[1])
        else:
            logger.error('Invalid number {attrs[1]}')
            say(msgs.error())
            return

    ch = message['channel']
    client = WebClient(token=slack_user_token)

    if 'thread_ts' in message:
        # this command called in reply
        msgp.clear_replies(ch, message['thread_ts'], count, client, logger)
        # thread_tsは現状では残る
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

# slack command control
@app.message(re.compile(f'<@{bot_user_id}> *slack *(.*)$'))
def handle_slack_command(message, say, context):
    '''parse slack command
    '''
    if 'matches' not in context:
        logger.debug(context)
        say(msgs.error())
        return

    logger.debug(context['matches'])
    match = context['matches'][0]
    attrs = splitter.split(match)

    if match.find('clear') >= 0:
        # clear
        logger.debug('subcommand is clear, ' + ','.join(attrs))
        clear_command(message, say, attrs)
    elif match.find('where') >= 0:
        # where
        logger.debug('subcommand is watch, ' + ','.join(attrs))
        return_joining_channels(message, say)
    else:
        logger.warning('unknown subcommand, ' + ','.join(attrs))
        say(msgs.error())

##################
# import plugins #
##################

def execute_plugins(plugin_name, attrs, say, config):
    try:
        # インポートしたモジュール内の 'run' 関数を呼び出す
        result = ap.run(attrs, say, config)
        logger.info(f"コマンド '{plugin_name}' の実行結果: {result}")
        return True
        
    except ModuleNotFoundError:
        logger.error(f"エラー: コマンド '{plugin_name}' が見つかりませんでした。")
        say(msgs.error())
    except AttributeError:
        logger.error(f"エラー: コマンド '{plugin_name}' に 'run' 関数がありません。")
        say(msgs.error())
    return False

@app.message(re.compile(f'<@{bot_user_id}>\s+(.*)'))
def dispatch_command(message, say, context):
    '''組み込み以外のコマンドをディスパッチするよ！
    コマンドはpluginsディレクトリにコードが用意されていれば、動的に読み込んで動作するよ！
    用意されてない場合はエラーを返すよ！

    @BOTNAME COMMAND [SUBCOMMAND] [OPTION]

    Parameters
    ----------
    message: Object
    say: Object
    context: Object
    '''
    
    if 'matches' not in context:
        logger.error(str(context))
        say(msgs.error())
        return

    logger.debug(context['matches'])

    matches = context['matches'][0].split()
    command = matches[0]
    # attrs includes no COMMAND but SUBCOMMAND and OPTIONs
    attrs = None if len(matches) == 1 else matches[1:]

    if not execute_plugins(command, attrs, say, config[command]):

        # debug
        say(f'command={command}\n' + f'matches={matches}')

        logger.warning(f"知らないコマンドが来たみたい！: {message['text']}")
        say(f"知らないコマンドが来たみたい！: {message['text']}")

if __name__ == "__main__":
    logger.info("アローラ、起動するよー！")
    handler = SocketModeHandler(app, slack_app_token)
    handler.start()
