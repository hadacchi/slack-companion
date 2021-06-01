import json
import time

import msgs

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

    res = client.conversations_history( channel=ch
                                      , limit=limit
                                      , inclusive=True
                                      , latest=latest
                                      )
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
