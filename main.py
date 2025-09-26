import os
import os.path
import time
import json
import toml
import logging
import re
import importlib
import pathlib
import pkgutil
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
#import tracemalloc

from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import mylogger
import msgprocessing as msgp
import msgs_allora as msgs

'''slack bot

Usage:
    @BOTNAME COMMAND [SUBCOMMAND] [OPTION]

Embeded commands:
    @BOTNAME slack  --  slack domain
                    clear   --  remove message in the channel
                        all --  remove all messages in the channel
                        n   --  remove n messages in the channel
                    where   --  output all channel names where BOT joins
    @BOTNAME cron   --  schedules a command for routine execution
                    daily   --  run daily
                    weekly  --  run weekly
                    list    --  show cron.d/daily and cron.d/weekly

Example:
    @BOTNAME slack clear all
    @BOTNAME slack cron daily slack clear all
'''

##################
# configurations #
##################

# load config file
config = toml.load('secret.toml')

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

################
# load plugins #
################

plugin_dir = pathlib.Path(config['resource']['plugin_dir_path'])

def load_all_plugins():
    """
    pluginsフォルダ内の全てのパッケージを読み込み、リストで返す
    """
    loaded_plugins = {}

    # pkgutil.iter_modulesを使って、プラグインディレクトリ内のモジュールを探索
    for finder, name, ispkg in pkgutil.iter_modules([plugin_dir]):
        # ispkgがTrueなら、それはパッケージ（ディレクトリ）
        if ispkg:
            # パッケージ名とモジュール名を結合して完全なパスを作成
            module_name = '.'.join(plugin_dir.joinpath(name).parts)
            logger.info(f"プラグイン '{module_name}' を読み込み中...")

            try:
                # importlib.import_module()でモジュールを動的にインポート
                loaded_plugins[name] = importlib.import_module(module_name)
                logger.info(f"プラグイン '{name}' の読み込みに成功しました。")

            except Exception as e:
                logger.error(f"エラー: プラグイン '{name}' の読み込みに失敗しました: {e}")

    return loaded_plugins

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

def return_joining_channels(bot_client, channel_id):
    '''tell channel names where the bot joins
    
    `@BOTNAME slack where`

    Parameters
    ----------
    bot_client: slack_sdk.WebClient
    channel_id: str
    '''

    logger.debug('return_joining_channels called')

    channels = []
    try:
        # publicチャンネルのリストを取得するよ
        chlist = bot_client.conversations_list()['channels']
        
        for ch in chlist:
            try:
                # チャンネルのメンバーリストを取得して、ボット自身がいるか確認するよ
                members = bot_client.conversations_members(channel=ch['id'])['members']
                if bot_user_id in members:
                    channels.append(ch['name'])
            except Exception as e:
                # メンバーリストが取得できないチャンネルはスキップするよ（権限不足など）
                logger.warning(f"チャンネル '{ch.get('name', ch['id'])}' のメンバーをチェックできませんでした: {e}")
    except Exception as e:
        logger.error(f"チャンネルリストの取得に失敗しました: {e}")
        bot_client.chat_postMessage(channel=channel_id, text=msgs.fail())
        return

    message_text = msgs.imin().format('\n'.join(channels)) if channels else msgs.noplace()
    bot_client.chat_postMessage(channel=channel_id, text=message_text)

def clear_command(bot_client, user_token_client, channel_id, thread_ts, attrs, latest='now'):
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
    bot_client: slack_sdk.WebClient (for posting messages)
    user_token_client: slack_sdk.WebClient (for deleting messages)
    channel_id: str
    thread_ts: str or None
    latest: str
        The timestamp of the message to start deleting from.
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
            logger.error(f'Invalid number {attrs[1]}')
            bot_client.chat_postMessage(channel=channel_id, text=msgs.error())
            return

    if thread_ts:
        # this command called in reply
        msgp.clear_replies(channel_id, thread_ts, count, user_token_client, logger)
        # thread_tsは現状では残る
    else:
        bot_client.chat_postMessage(channel=channel_id, text=msgs.confirm())
        has_more = True
        cursor = None

        while has_more:
            if count <= 0:
                break

            paramdict = {'limit': min(count, 100), 'latest': latest}
            if cursor:
                paramdict['cursor'] = cursor

            # get_historyのsay引数はオプショナルに変更済み
            msg_list, has_more, cursor = msgp.get_history(channel_id, user_token_client, logger=logger, **paramdict)

            if not msg_list and has_more is False and cursor is None: # エラーの可能性
                logger.error(f"Failed to get history for channel {channel_id}")
                bot_client.chat_postMessage(channel=channel_id, text=msgs.fail())
                return

            msgp.clear_history(channel_id, msg_list, user_token_client, logger)
            count -= len(msg_list)
        bot_client.chat_postMessage(channel=channel_id, text=msgs.finish())

def execute_slack_command(bot_client, command_string, channel_id, thread_ts=None, latest='now'):
    """slackコマンドを実行するよ！"""
    logger.debug(f"Executing slack command: '{command_string}' in channel {channel_id}")
    attrs = splitter.split(command_string)

    if not attrs or not attrs[0]:
        logger.warning(f"Empty slack command received.")
        return False

    command = attrs[0]

    if command == 'clear':
        logger.debug('subcommand is clear, ' + ','.join(attrs))
        user_token_client = WebClient(token=slack_user_token)
        clear_command(
            bot_client=bot_client,
            user_token_client=user_token_client,
            channel_id=channel_id,
            thread_ts=thread_ts,
            attrs=attrs,
            latest=latest
        )
        return True
    elif command == 'where':
        logger.debug('subcommand is where, ' + ','.join(attrs))
        return_joining_channels(
            bot_client=bot_client,
            channel_id=channel_id
        )
        return True
    else:
        logger.warning('unknown subcommand, ' + ','.join(attrs))
        return False

# slack command control
@app.message(re.compile(rf'<@{bot_user_id}>\s*slack\s*(.*)$'))
def handle_slack_command(message, say, context):
    '''parse slack command
    '''
    # contextからコマンド文字列を取得するよ。なかったら空文字にするね！
    command_string = context.get('matches', [''])[0].strip()

    # コマンドが空だったり、実行に失敗したらエラーメッセージを返すよ
    if not command_string or not execute_slack_command(
        bot_client=app.client,
        command_string=command_string,
        channel_id=message['channel'],
        thread_ts=message.get('thread_ts'),
        latest=message['ts']
    ):
        say(msgs.error())

########
# cron #
########

# run
def daily_job():
    logger.info('デイリータスクをスキャンして実行するよ！')

    try:
        cron_dir_path = pathlib.Path(config['cron']['cron_dir_path'])
        filepath = cron_dir_path / 'daily'

        if not filepath.is_file():
            logger.info("dailyのcronファイルが見つからなかったから、今日のタスクはスキップするね。")
            app.client.chat_postMessage(channel="#general", text="dailyのcronファイルが見つからなかったから、今日のタスクはスキップするね。")
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    job_info = json.loads(line)
                    command_text = job_info.get('command_text', '')
                    channel_id = job_info.get('channel_id')
                    thread_ts = job_info.get('thread_ts')

                    if not command_text or not channel_id:
                        logger.warning(f"無効なcronジョブだからスキップするね: {line}")
                        app.client.chat_postMessage(channel="#general", text=f"無効なcronジョブだからスキップするね: {line}")
                        continue

                    # コマンドをパースするよ！
                    command_parts = splitter.split(command_text)
                    if not command_parts:
                        logger.warning(f"空のcronジョブだからスキップするね: {line}")
                        app.client.chat_postMessage(channel="#general", text=f"空のcronジョブだからスキップするね: {line}")
                        continue

                    main_command = command_parts[0]
                    attrs = command_parts[1:]

                    if main_command == 'slack':
                        sub_command_string = ' '.join(attrs)
                        logger.info(f"デイリーのslackコマンドを実行するよ: '{sub_command_string}' in channel {channel_id}")
                        app.client.chat_postMessage(channel="#general", text=f"デイリーのslackコマンドを実行するよ: '{sub_command_string}' in channel {channel_id}")
                        execute_slack_command(
                            bot_client=app.client,
                            command_string=sub_command_string,
                            channel_id=channel_id,
                            thread_ts=thread_ts,
                            latest='now'
                        )
                    else:
                        logger.info(f"デイリーのプラグインコマンドを実行するよ: '{command_text}' in channel {channel_id}")
                        app.client.chat_postMessage(channel="#general", text=f"デイリーのプラグインコマンドを実行するよ: '{command_text}' in channel {channel_id}")
                        execute_plugins(
                            main_command,
                            attrs,
                            app.client,
                            channel_id,
                        )
                except json.JSONDecodeError:
                    logger.error(f"cronジョブの行がパースできなかったよ: {line}")
                    app.client.chat_postMessage(channel="#general", text=f"cronジョブの行がパースできなかったよ: {line}")
                except Exception as e:
                    logger.error(f"cronジョブの実行中にエラーが出ちゃった: '{line}', error: {e}")
                    app.client.chat_postMessage(channel="#general", text=f"cronジョブの実行中にエラーが出ちゃった: '{line}', error: {e}")
        
        # 終わったらメッセージを投稿するよ！
        app.client.chat_postMessage(channel="#general", text=msgs.daily_task_finish())

    except KeyError:
        logger.error("`cron.cron_dir_path` が secret.toml に設定されてないみたい。")
    except Exception as e:
        logger.error(f"デイリージョブの実行に失敗しちゃった: {e}")

# run weekly
def weekly_job():
    logger.info('ウィークリータスクをスキャンして実行するよ！')

    try:
        cron_dir_path = pathlib.Path(config['cron']['cron_dir_path'])
        filepath = cron_dir_path / 'weekly'

        if not filepath.is_file():
            logger.info("weeklyのcronファイルが見つからなかったから、今週のタスクはスキップするね。")
            app.client.chat_postMessage(channel="#general", text="weeklyのcronファイルが見つからなかったから、今週のタスクはスキップするね。")
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    job_info = json.loads(line)
                    command_text = job_info.get('command_text', '')
                    channel_id = job_info.get('channel_id')
                    thread_ts = job_info.get('thread_ts')

                    if not command_text or not channel_id:
                        logger.warning(f"無効なcronジョブだからスキップするね: {line}")
                        app.client.chat_postMessage(channel="#general", text=f"無効なcronジョブだからスキップするね: {line}")
                        continue

                    # コマンドをパースするよ！
                    command_parts = splitter.split(command_text)
                    if not command_parts:
                        logger.warning(f"空のcronジョブだからスキップするね: {line}")
                        app.client.chat_postMessage(channel="#general", text=f"空のcronジョブだからスキップするね: {line}")
                        continue

                    main_command = command_parts[0]
                    attrs = command_parts[1:]

                    if main_command == 'slack':
                        sub_command_string = ' '.join(attrs)
                        logger.info(f"ウィークリーのslackコマンドを実行するよ: '{sub_command_string}' in channel {channel_id}")
                        app.client.chat_postMessage(channel="#general", text=f"ウィークリーのslackコマンドを実行するよ: '{sub_command_string}' in channel {channel_id}")
                        execute_slack_command(
                            bot_client=app.client,
                            command_string=sub_command_string,
                            channel_id=channel_id,
                            thread_ts=thread_ts,
                            latest='now'
                        )
                    else:
                        logger.info(f"ウィークリーのプラグインコマンドを実行するよ: '{command_text}' in channel {channel_id}")
                        app.client.chat_postMessage(channel="#general", text=f"ウィークリーのプラグインコマンドを実行するよ: '{command_text}' in channel {channel_id}")
                        execute_plugins(
                            main_command,
                            attrs,
                            app.client,
                            channel_id,
                        )
                except json.JSONDecodeError:
                    logger.error(f"cronジョブの行がパースできなかったよ: {line}")
                    app.client.chat_postMessage(channel="#general", text=f"cronジョブの行がパースできなかったよ: {line}")
                except Exception as e:
                    logger.error(f"cronジョブの実行中にエラーが出ちゃった: '{line}', error: {e}")
                    app.client.chat_postMessage(channel="#general", text=f"cronジョブの実行中にエラーが出ちゃった: '{line}', error: {e}")
        
        # 終わったらメッセージを投稿するよ！
        app.client.chat_postMessage(channel="#general", text=msgs.weekly_task_finish())

    except KeyError:
        logger.error("`cron.cron_dir_path` が secret.toml に設定されてないみたい。")
    except Exception as e:
        logger.error(f"ウィークリージョブの実行に失敗しちゃった: {e}")

# manage routine tasks
@app.message(re.compile(rf'<@{bot_user_id}>\s*cron\s*(.*)$'))
def handle_cron_command(message, say, context):
    '''cronジョブを管理するよ！

    `@BOTNAME cron [daily|weekly] コマンド`
    `@BOTNAME cron list`
    '''
    if 'matches' not in context:
        logger.error(str(context))
        say(msgs.error())
        return

    logger.debug(context['matches'])
    match = context['matches'][0]
    attrs = splitter.split(match)

    if not attrs or not attrs[0]:
        logger.warning(f'Invalid cron command: {match}')
        say(f"cronコマンドの形式が正しくないみたい…\n`@BOTNAME cron [daily|weekly|list] ...` のように指定してね。")
        return

    command = attrs[0]

    if command == 'list':
        try:
            cron_dir_path = pathlib.Path(config['cron']['cron_dir_path'])
            response_text = "📝 今登録されてるcronジョブはこんな感じだよ！\n"

            schedules_to_list = ['daily', 'weekly']
            
            for schedule in schedules_to_list:
                filepath = cron_dir_path / schedule
                response_text += f"\n--- 🗓️ {schedule} ---\n"
                
                if not filepath.is_file():
                    response_text += "登録されてるジョブはないみたい。\n"
                    continue

                commands = []
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f, 1):
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                job_info = json.loads(line)
                                command_text = job_info.get('command_text', 'N/A')
                                commands.append(f"`{command_text}`")
                            except json.JSONDecodeError:
                                logger.warning(f"cronファイル '{filepath}' の行(L{i})がパースできなかったよ: {line}")
                                commands.append(f"_(パースできないジョブ: `{line}`)_")
                except Exception as e:
                    logger.error(f"cronファイル '{filepath}' の読み込み中にエラーが出ちゃった: {e}")
                    response_text += "ファイルの読み込みでエラーが起きちゃった…ごめんね😢\n"
                    continue
                
                if commands:
                    for i, cmd_info in enumerate(commands, 1):
                        response_text += f"{i}. {cmd_info}\n"
                else:
                    response_text += "登録されてるジョブはないみたい。\n"

            say(response_text)

        except KeyError:
            logger.error("`cron.cron_dir_path` が secret.toml に設定されてないみたい。")
            say("cron機能の設定が `secret.toml` に見つかりません。")
        except Exception as e:
            logger.error(f"cronジョブのリスト表示に失敗しちゃった: {e}")
            say(msgs.fail())
        return

    elif command in ['daily', 'weekly']:
        if len(attrs) < 2:
            logger.warning(f'Invalid cron command: {match}')
            say(f"cronコマンドの形式が正しくありません。\n`@BOTNAME cron {command} コマンド` のように指定してください。")
            return

        schedule_type = command
        routine_command = ' '.join(attrs[1:])

        try:
            cron_dir_path = pathlib.Path(config['cron']['cron_dir_path'])
            # cronジョブを保存するディレクトリがなければ作成する
            cron_dir_path.mkdir(parents=True, exist_ok=True)

            filepath = cron_dir_path / schedule_type

            # 保存するジョブ情報を作成するよ
            job_info = {
                'channel_id': message['channel'],
                'user_id': message['user'],
                'thread_ts': message.get('thread_ts'), # スレッドで実行された場合も考慮
                'command_text': routine_command,
                'schedule_type': schedule_type,
            }

            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(job_info) + '\n')
            
            logger.info(f"Cron job saved: '{routine_command}' to {filepath}")
            say(f"`{schedule_type}` のスケジュールに `{routine_command}` を追加しました！")
        except KeyError:
            logger.error("`cron.cron_dir_path` is not configured in secret.toml")
            say("cron機能の設定が `secret.toml` に見つかりません。")
        except Exception as e:
            logger.error(f"Failed to save cron job: {e}")
            say(msgs.error())
    else:
        logger.warning(f'Unknown cron schedule type: {command}')
        say(f"`{command}` は知らないスケジュールだよ。`daily`、`weekly`、`list` のどれかを指定してね。")

# APScheduler を設定
scheduler = BackgroundScheduler(timezone=ZoneInfo("Asia/Tokyo"))

# 毎日特定の時間に実行する例 (例: 午前2時10分)
scheduler.add_job(daily_job, 'cron', hour=2, minute=10)
# 毎週月曜日の午前2時20分に実行する例
scheduler.add_job(weekly_job, 'cron', day_of_week='sat', hour=2, minute=20)
# または、インターバルで実行する例 (例: 10分ごと)
# scheduler.add_job(scheduled_job, 'interval', minutes=10)

# スケジューラーを開始
scheduler.start()

##################
# import plugins #
##################

def execute_plugins(plugin_name, attrs, bot_client, channel_id):
    try:
        # インポートしたモジュール内の 'run' 関数を呼び出す
        # プラグインのrun関数は run(attrs, bot_client, channel_id) の形式を期待するよ
        configfile = os.path.join(config['resource']['plugin_dir_path'], plugin_name + '_config.toml')

        result = plugins[plugin_name].run(attrs, bot_client, channel_id, configfile)
        logger.info(f"コマンド '{plugin_name}' の実行結果: {result}")
        bot_client.chat_postMessage(channel=channel_id, text=msgs.finish())
        return True
    except KeyError:
        logger.error(f"エラー: コマンド '{plugin_name}' がありません．")
        bot_client.chat_postMessage(channel=channel_id, text=msgs.error())
    except ModuleNotFoundError:
        logger.error(f"エラー: コマンド '{plugin_name}' が見つかりませんでした。")
        bot_client.chat_postMessage(channel=channel_id, text=msgs.error())
    except AttributeError as e:
        logger.error(f"エラー: コマンド '{plugin_name}' に 'run' 関数がありません。")
        bot_client.chat_postMessage(channel=channel_id, text=f'{e}')
        bot_client.chat_postMessage(channel=channel_id, text=msgs.error())
    return False

@app.message(re.compile(rf'<@{bot_user_id}>\s+(.*)'))
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

    if not execute_plugins(
        command,
        attrs,
        app.client,
        message['channel']
    ):

        # debug
        say(f'command={command}\n' + f'matches={matches}')

        logger.warning(f"知らないコマンドが来たみたい！: {message['text']}")
        say(f"知らないコマンドが来たみたい！: {message['text']}")

if __name__ == "__main__":
    logger.info("アローラ、起動するよー！")

    logger.info("プラグインを検索・読み込みします。")
    plugins = load_all_plugins()

    if plugins:
        logger.info("--- 読み込まれたプラグイン ---")
        for plugin in plugins.keys():
            logger.info(f"プラグイン名: {plugin}")
    else:
        logger.info("プラグインは見つかりませんでした。")

    handler = SocketModeHandler(app, slack_app_token)
    handler.start()
