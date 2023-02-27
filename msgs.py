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
ERROR_MSGS = ['は？ そんなん知らねーんだけど',
        ]
IMIN_MSGS = ['ん？ あたしが見てるのは\n{0}\nだよ',
             ]
NOPLACE_MSGS = ['すいちゃん，居場所ねーんだけど？'
                ]
DUP_MSGS = ['ねぇねぇねぇ\nこいつらダブってんだけど？\n{0}'
            ]


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
