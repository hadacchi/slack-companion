import json
import time

import msgs
import pickle


def get_replies(ch, msg_list, client, logger=None):
    if logger is not None:
        logger.error('Now get replies')

    video_ids = []
    for i, msg in enumerate(msg_list):
        if 'reply_count' in msg:
            logger.error(f'reply_count is {msg["reply_count"]}')
            res = client.conversations_replies(channel=ch, ts=msg['ts'])
            if not res['ok']:
                if logger is not None:
                    logger.error(str(res))
                else:
                    print(res)
                say(msgs.fail())
                return None, [], False
            else:
                data = res['messages']
                listname = data[0]['text']
                for m in data[1:]:
                    if m['text'].find('www.youtube.com') > 0:
                        # youtube
                        video_ids.append(m['text'].replace(
                            '>', '').split('=')[-1])
                    elif m['text'].find('youtu.be') > 0:
                        # youtu.be
                        video_ids.append(m['text'].replace(
                            '>', '').split('/')[-1])
                    else:
                        logger.error(f"unknown url {m['text']}")
            pickle.dump(video_ids, open('res.pkl', 'wb'))
            return
            # logger.error(str(res))


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
