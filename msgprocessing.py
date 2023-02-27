import json
import time
import urllib.parse
import re
import logging

import msgs
from dump_log import dump_log

urlpat = re.compile('https?://[^\s>]+')

def get_video_ids_from_replies(ch, ts, client, logger=None):
    '''read url from replies of the thread where suichan called

    Parameters
    ----------
    ch : string
        channel id
    ts : float
        time of the thread message
    client : slack_sdk.WebClient
    logger : logging.Logger

    Result
    ------
    listname : string
        name of playlist
    video_ids : list
        list of vids
    dup : list
        list of dupplicated vids
    '''

    logger = logging.getLogger(__name__)
    dump_log('get_video_ids_from_replies called', logger, 'debug')

    res = client.conversations_replies(channel=ch, ts=ts)
    #dump_log(str(res), logger, 'debug')

    if not res['ok']:
        dump_log(str(res), logger, 'error')
        say(msgs.fail())
        return []
    else:
        data = res['messages']
        listname = data[0]['text']

        video_ids = []
        dup = []
        dump_log('seek vid in the thread', logger)
        for i, m in enumerate(data[1:]):
            urls = urlpat.findall(m['text'])
            dump_log(str(urls), logger, 'debug')
            vids = []
            for url in urls:
                dump_log(url, logger, 'debug')
                if url.find('youtube.com') > 0:
                    dump_log('youtube.com is found', logger, 'debug')
                    # www.youtube.com or music.youtube.com
                    qstring = urllib.parse.urlparse(url).query
                    params = urllib.parse.parse_qs(qstring)
                    if 'v' in params:
                        vids += params['v']
                elif url.find('youtu.be') > 0:
                    dump_log('youtu.be is found', logger, 'debug')
                    vids += [urllib.parse.urlparse(url).path[1:],]
                else:
                    dump_log('both youtube.com and youtu.be are not found',
                             logger, 'debug')
            for vid in vids:
                if vid in video_ids:
                    dup.append([vid, i])
                else:
                    video_ids.append(vid)

    dump_log(f'{dup} are dupplicated', logger, 'debug')
    dump_log(f'videos are {video_ids}', logger, 'debug')
    return listname, video_ids, dup


def remove_messages(ch, ts_list, client, logger=None):
    '''remove messages

    Parameters
    ----------
    ch : string
        channel id
    ts_list : list
        list of ts to delete
    client : slack_sdk.WebClient
    logger : logging.Logger

    Results
    -------
    void
    '''

    dump_log('remove_messages is called', logger, 'debug')

    for i, ts in enumerate(ts_list):
        client.chat_delete(channel=ch, ts=ts)
        time.sleep(1)
    dump_log(f'{i+1} messages were deleted', logger)


def clear_history(ch, msg_list, client, logger=None):
    '''delete messages. if the message has replies, delete them

    Parameters
    ----------
    ch : string
        channel id
    msg_list : list
        list of message object to delete
    client : slack_sdk.WebClient
    logger : logging.Logger

    Results
    -------
    void
    '''

    dump_log('clear_history is called', logger, 'debug')

    for i, msg in enumerate(msg_list):
        if 'thread_ts' in msg:
            clear_replies(ch, msg['thread_ts'], 999, client, logger)
        client.chat_delete(channel=ch, ts=msg['ts'])
        time.sleep(1)
    dump_log(f'{i+1} messages were deleted', logger)


def get_history(ch, client, say, logger=None, limit=100, cursor=None, latest='now'):
    '''get channel history

    Parameters
    ----------
    ch : string
        channel id
    client : slack_sdk.WebClient

    '''

    dump_log('get_history is called', logger, 'debug')

    if latest == 'now':
        res = client.conversations_history(
                channel=ch,
                limit=limit,
                inclusive=True,
                cursor=cursor
        )
    else:
        res = client.conversations_history(
                channel=ch,
                limit=limit,
                inclusive=True,
                latest=latest
        )
    if not res['ok']:
        dump_log(str(res), logger, 'error')
        say(msgs.fail())
        return [], False
    else:
        dump_log(f"get {len(res['messages'])} messages", logger)
        cursor = res['response_metadata']['next_cursor'] \
                    if res['has_more'] else None
        return res['messages'], res['has_more'], cursor


def get_message(ch, client, ts, say, logger=None, limit=1, cursor=None):
    dump_log('get_message is called', logger, 'debug')

    res = client.conversations_history(channel=ch, limit=limit, inclusive=True, latest=ts)
    if not res['ok']:
        dump_log(str(res), logger, 'error')
        say(msgs.fail())
        return [], False
    else:
        dump_log(f"get message", logger, 'debug')
        dump_log(str(res['messages']), logger)
        return res['messages']


def clear_replies(ch, thread_ts, count, client, logger=None):
    dump_log('clear_replies', logger)

    msg_list = get_replies(ch, thread_ts, client, logger, count)

    ts_list = [msg['ts'] for msg in msg_list[1:] if 'ts' in msg]
    remove_messages(ch, ts_list[-count:], client, logger)


def get_replies(ch, thread_ts, client, logger=None, limit=999):
    dump_log('get_replies', logger)

    replies = []
    has_more = True
    cursor = None

    while has_more:
        res = client.conversations_replies(channel=ch, ts=thread_ts, limit=limit, cursor=cursor)
        if not res['ok']:
            dump_log(str(res), logger, 'error')
            say(msgs.fail())
            return
        else:
           replies += res['messages']
           has_more = res['has_more']
           cursor = res['response_metadata']['next_cursor'] if has_more else None

    return replies


def rm_history(ch, ts, client, logger=None):
    dump_log('rm_history', logger)

    res = client.chat_delete(channel=ch, ts=ts)
    return msgs.finish()


def dm_write(user_id, msg, client, logger=None):
    dump_log('dm_write', logger)

    res = client.conversations_open(users=user_id)
    dm_id = res['channel']['id']

    client.chat_postMessage(channel=dm_id, text=msg)

