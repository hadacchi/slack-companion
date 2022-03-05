import json
import time

import msgs
from dump_log import dump_log


def get_video_ids_from_replies(ch, ts, client, logger=None):
    dump_log('get_video_ids_From_replies', logger)

    res = client.conversations_replies(channel=ch, ts=ts)
    logger.debug(str(res))

    if not res['ok']:
        dump_log(str(res), logger, 'error')
        say(msgs.fail())
        return []
    else:
        data = res['messages']
        listname = data[0]['text']

        video_ids = []
        dup = []
        for i, m in enumerate(data[1:]):
            if m['text'].find('www.youtube.com') > 0:
                # youtube
                vid = m['text'].replace('>', '').split('=')[-1]
            elif m['text'].find('youtu.be') > 0:
                # youtu.be
                vid = m['text'].replace('>', '').split('/')[-1]
            else:
                logger.info(f"unknown url {m['text']}")
                vid = None
            if vid in video_ids:
                dup.append([vid, i])
            elif vid is not None:
                video_ids.append(vid)

    return listname, video_ids, dup


def remove_messages(ch, ts_list, client, logger=None):
    dump_log('remove_messages', logger)

    for i, ts in enumerate(ts_list):
        client.chat_delete(channel=ch, ts=ts)
        time.sleep(1)
    dump_log(f'{i+1} messages were deleted', logger, 'debug')


def clear_history(ch, msg_list, client, logger=None):
    dump_log('clear_history', logger)

    for i, msg in enumerate(msg_list):
        if 'thread_ts' in msg:
            clear_replies(ch, msg['thread_ts'], 999, client, logger)
        client.chat_delete(channel=ch, ts=msg['ts'])
        time.sleep(1)
    dump_log(f'{i+1} messages were deleted', logger, 'debug')


def get_history(ch, client, say, logger=None, limit=100, cursor=None, latest='now'):
    dump_log('get_history', logger)

    if latest == 'now':
        res = client.conversations_history(channel=ch, limit=limit, inclusive=True, cursor=cursor)
    else:
        res = client.conversations_history(channel=ch, limit=limit, inclusive=True, latest=latest)
    if not res['ok']:
        dump_log(str(res), logger, 'error')
        say(msgs.fail())
        return [], False
    else:
        dump_log(f"get {len(res['messages'])} messages", logger, 'debug')
        cursor = res['response_metadata']['next_cursor'] if res['has_more'] else None
        return res['messages'], res['has_more'], cursor


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
            error_msg(logger, str(res), 'error')
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
