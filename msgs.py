import random

CONFIRM_MSGS = [ 'ガリィにおまかせです:heart:'
               , 'りょーかーい．ガリィ、がんばりま～す:star:'
               , 'あぁ．．．ハイハイ，ガリィのお仕事ですよねぇ～'
               , 'めーんどくさいヤツですねぇ～'
               ]
FINISH_MSGS  = [ 'これでも頑張ったんですよ？ なるべく目立たずに，事を進めるのは大変だったんですからぁ～:star:'
               , '順調ですよ（ﾆﾔ'
               , 'さよなら～ ﾉｼ'
               ]
FAIL_MSGS    = [ 'でもミカちゃん、大食らいなので足りてませ～ん:sob:'
               , '何かが起きてうまくできません～:sob:'
               ]
NOCH_MSGS    = [ 'いやですよマスタぁ〜，そういうchを作らなかったのはマスターじゃありませんかぁ'
               , 'ありもしないchの名前を出すなんて．．．躾の程度が伺えちゃうわね．．．'
               ]
NOTIFY_MSGS  = [ 'そういえばマスター，何か見付かったみたいですよ？'
               ]
WAITING_MSGS = [ 'どうしました？マスター？'
               , 'そんな顔しないでくださいよぉ'
               ]
ERROR_MSGS   = [ 'マスタァ〜，何言ってるんですか？　ガリィには，分かりませ〜ん:sob:'
               ]
IMIN_MSGS    = [ 'いやですよマスタぁ〜\n私がいるのは，\n{0}\nじゃないですかぁ'
               ]
NOPLACE_MSGS = [ 'いやですよマスタぁ〜\n私をどこにも置かなかったのはマスターじゃありませんかぁ'
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
