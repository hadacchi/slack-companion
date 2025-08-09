import random

'''メッセージリスト

CONFIRM_MSGS: slackbotがメンションを受けた時，コマンドを理解して了解の意味を回答する場合の文をリストで2～3個並べる
FINISH_MSGS: slackbotがコマンドを実行完了した後，完了したことを告げる場合の文をリストで2～3個並べる
ERROR_MSGS: slackbotがコマンドを受けた時，コマンドが定義されてない場合に言及する文をリストで2～3個並べる
FAIL_MSGS: slackbotがコマンドを実行する時，失敗したことを告げる場合の文をリストで2～3個並べる
NOMATCH_MSGS: slackbotが対象を指定するコマンドを受けた時，その対象が見つからないことを告げる場合の文をリストで2～3個並べる
'''

CONFIRM_MSGS = [
    "了解だよー！任せてね！😊",
    "おっけー！ちゃんと分かったよ！",
    "りょーかい！張り切ってやっちゃうね！💪"
]

FINISH_MSGS = [
    "終わったよー！どうかな？✨",
    "ばっちり完了！ちゃんとできたよ！",
    "ふっふーん、終わらせちゃったもんね！😉"
]

ERROR_MSGS = [
    "えへへ…ごめんね、そのコマンドはまだ分からないんだ🙏",
    "うーん、その言葉、初めて聞いたかも…？",
    "ごめんね、そのコマンドはあたしの辞書にないみたい！💦"
]

FAIL_MSGS = [
    "あちゃー…うまくできなかったみたい…ごめんね😢",
    "うーん、何かがおかしくなっちゃったみたい…",
    "えーん、失敗しちゃった…また試してみてもいいかな？🥺"
]

NOMATCH_MSGS = [
    "あれれ？その人、見つからないみたい…",
    "ごめんね、探してみたんだけど、いなかったよ…",
    "うーん、その対象はどこにいっちゃったのかな？🤔"
]

IMIN_MSGS = [
    "ふむふむ…このチャンネルは、\n{0}\nだよ！",
    "えっとね、このチャンネルはね、\n{0}\nっていうリストに入ってるよ！",
    "はーい！このチャンネルは、じゃじゃーん！\n{0}\nですっ！",
    "このチャンネルの情報は、\n{0}\nにまとまっているよ！😊"
]

NOPLACE_MSGS = [
    "あれれ？どこにも参加してないみたい…(´・ω・｀)",
    "うーん…どのチャンネルにもいないみたいだよ？",
    "ごめんね、まだどこにもお邪魔してないみたいなんだ…",
    "しーん…あたし、どこにいるんだろう？(；´∀｀)"
]

def confirm():
    return random.choice(CONFIRM_MSGS)

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
