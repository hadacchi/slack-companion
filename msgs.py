import random

CONFIRM_MSGS = [
    'しゃーねーなー．やってやるよぉ:comet:',
    'Hi, honey〜:notes:',
    'ふぁ〜い:zzz:']
FINISH_MSGS = [
    'やったよ〜:star:',
    '全部消してやったぜ',
    'Have a nice day!\nおつまち！！']
FAIL_MSGS = ['うまく，できねーんだけどぉ！:sob:',
        'なーんでなーんでなーんでーーー！！！？？？'
        ]
NOCH_MSGS = ['は？ そんなん知らねーんだけど',
        ]
NOTIFY_MSGS = ['なんか，ゆってるよ？',
               ]
WAITING_MSGS = ['なになになに〜？',
                ]
WATCH_MSGS = ['じー',
              ]
UNWATCH_MSGS = ['ぷーい',
              ]
ERROR_MSGS = ['は？ そんなん知らねーんだけど',
        'なんか，間違ってね？',
        ]
IMIN_MSGS = ['ん？ あたしが見てるのは\n{0}\nだよ',
             ]
NOPLACE_MSGS = ['すいちゃん，居場所ねーんだけど？'
                ]
DUP_MSGS = ['ねぇねぇねぇ\nこいつらダブってんだけど？\n{0}'
            ]
DBG_MSGS = ['{0} received'
            ]


def watch():
    return random.choice(WATCH_MSGS)


def unwatch():
    return random.choice(UNWATCH_MSGS)


def confirm():
    return random.choice(CONFIRM_MSGS)


def noch():
    return random.choice(NOCH_MSGS)


def fail():
    return random.choice(FAIL_MSGS)


def finish():
    return random.choice(FINISH_MSGS)


def error():
    return random.choice(ERROR_MSGS)


def imin():
    return random.choice(IMIN_MSGS)


def noplace():
    return random.choice(NOPLACE_MSGS)


def dup():
    return random.choice(DUP_MSGS)


def dbgreply():
    return random.choice(DBG_MSGS)
