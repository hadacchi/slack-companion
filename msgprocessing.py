import json
import time

import msgs


def get_video_ids_from_replies(ch, ts, client, logger=None):
    if logger is not None:
        logger.info('Now get replies')

    res = client.conversations_replies(channel=ch, ts=ts)
    logger.debug(str(res))

    if not res['ok']:
        if logger is not None:
            logger.error(str(res))
        else:
            print(res)
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


def retrieve_threads(ch, msg_list, client, logger=None):
    '''複数リストの処理．使いづらいからちゃんとテストできてないので，
    使う前に必ずテストしてから使うこと．
    呼び出し側はそもそも未実装．
    '''

    return

    if logger is not None:
        logger.info('Now retrieve threads')

    playlist_list = []
    for i, msg in enumerate(msg_list):
        if 'reply_count' in msg:
            listname, video_ids, dup = get_video_ids_from_replies(
                ch, msg['ts'], client, logger)

            playlist_list.append([listname, video_ids])

    return playlist_list


def clear_history(ch, msg_list, client, logger=None):
    if logger is not None:
        logger.debug('Now clear history')

    for i, msg in enumerate(msg_list):
        client.chat_delete(channel=ch, ts=msg['ts'])
        time.sleep(1)
    logger.info(f'{i+1} messages were deleted')
    return msgs.finish()


def get_history(ch, client, say, logger=None, limit=100, latest='now'):
    if logger is not None:
        logger.debug('Now get history')

    res = client.conversations_history(
        channel=ch,
        limit=limit,
        inclusive=True,
        latest=latest)
    if not res['ok']:
        if logger is not None:
            logger.error(str(res))
        else:
            print(res)
        say(msgs.fail())
        return None, [], False
    else:
        if logger is not None:
            logger.debug(f"get {len(res['messages'])} messages")
        return msgs.confirm(), res['messages'], res['has_more']


def rm_history(ch, ts, client, logger=None):
    if logger is not None:
        logger.debug('Now rm history')

    res = client.chat_delete(channel=ch, ts=ts)
    return msgs.finish()
