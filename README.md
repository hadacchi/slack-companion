# slack-companion

slack上のメッセージを見て，コマンドを解釈し，実行するbot

## How to Use

1. `@BOTNAME clear 10` で発言した channel の発言を最新10件削除
1. `@BOTNAME clear all` で発言した channel の発言を全件削除
1. `@BOTNAME where` で BOT の参加する channel list を返却

## Manual

### 1. アプリの作成

アプリをインストールしたいslackのワークスペースに接続したセッションで https://api.slack.com/apps へアクセス

1. Create New App  
   App Name は好きなおにゃの子の名前でも入れとけ  
   Development Slack Workspace はアプリ開発用 Workspace の設定だが，インストールしたい Workspace を入れておけばOK
1. Settings -> Socket Mode でソケットモードを有効化  
   Enable Socket Mode を ON  
   Token Name は何でもいい  
   Scope は `connections:write` だけあればOK  
   Generate する
1. 表示された Token は，`secret.toml` の `token` に設定  
   bot の SocketModeHandler が slack にアクセスする際に使用
1. Features -> Event Subscriptions で Events を使えるようにする  
   Enable Events を ON
    1. Add Bot User Event で `message.channels` を追加  
       channel 内の message event を受け取るため
1. Features -> OAuth & Permissions で Scope を設定  
   User OAuth Token を `secret.toml` の `user_oauth_access_token` に設定  
   Bot User OAuth Token を `secret.toml` の `bot_user_oauth_access_token` に設定  
   前者は，あなたの権限で処理する場合に使用 (bot 以外の書き込みの削除)  
   後者は，bot の権限で十分な処理の場合に使用 (参加 channel の history 取得など)
    1. Redirect URLs は有効な自分で持っているURLを記入しておく  
       Add to Slack ボタンを使わないので，実際には不要
    1. Bot Token Scopes も，User Token Scopes も，`channels:history`, `channels:read`, `chat:write` をつけておく  
       bot の権限で履歴取得と結果を示す発言の書き込みをする  
       user の権限で任意の書き込みを削除する．
1. Settings -> Install App でアプリをインストール  
   workspaceにアカウント追加するだけ．プログラムは自分のサーバで実行させる必要あり．
1. Settings -> Basic Information でアプリの動作するアカウントの名前とかアイコンを
   設定する．  
   好みの見た目にしとけ．

### 2. アプリのデプロイ
#### 2.1 run with python command

1. bot を動作させるサーバに python と pipenv をインストールする
2. `Pipfile` のあるディレクトリで `pipenv install` で必要なパッケージをインストール
3. `pipenv shell` で作った環境に入る
4. `python gariechan.py` で実行
5. うまく動作することを確認できたら，`tmux` を使うなりなんなりして，サーバからログアウトしても動作するようにする (なんちゃって常駐化)

#### 2.2 run as docker container

1. `docker build -t gariechan:latest .` などのコマンドでコンテナ作成
2. `docker-compose up -d` で実行
3. log は docker-compose logs で確認

### 3. bot を動作させたい channel に参加/除名させる

1. slack のワークスペースに接続して，参加させたい ch で `/invite @BOTNAME` の形式で BOT の名前を入れたらOK  
   除名させたい場合は，その ch で `/kick @BOTNAME`
2. 動作確認
    1. bot を追加したchannel で `@BOTNAME clear 1` と発言する
    2. bot が応答メッセージを発言したあと，`@BOTNAME clear 1` の発言だけ削除して，bot が完了メッセージを発言する
    3. 以上の動作を確認できれば完了  
       だめなら頑張れ

## TODO

次に実装する機能

- 古い順にN件削除
    - oldestで何とかなりそうだが，以前のAPIだとcountに上限があったので，その場合は前から探索していかないとoldestが見付けられないかも知れない
- Pending
    - OAuth認証
        - アプリで配信しないので，いらないか…?
        - 各自，コードをデプロイして使ってくれ
- Finished
    - 常駐
        - Finished. I use Bolt for Python.
        - Finished. I use docker container. -> デーモンぽく動作するように起動スクリプトと終了スクリプトを作る
    - bug fix
        - 完了メッセージが1回だけ出るように修正する
    - 参加チャネルの出力
        - アプリをchに追加する場合，membersに表示されないのでどのchにアプリが参加しているかわからない
            - 参加しているch名のリストを/コマンドへのリアクションか，where are youへの回答で出力させる


## 注意

- このスクリプトは発言者の権限を確認しないので，勝手に発言を消されて困る channel には追加しないこと

