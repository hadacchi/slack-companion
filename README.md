# slack-companion

slack上のメッセージを見て，コマンドを解釈し，実行するbot

## How to Use

see [command references](command_references.md) for details.

1. `@BOTNAME clear 10` で発言した channel の発言を最新10件削除
1. `@BOTNAME clear all` で発言した channel の発言を全件削除
1. `@BOTNAME where` で BOT の参加する channel list を返却
1. youtube のプレイリストの自動作成
    1. botの参加するchで，作成したいプレイリスト名を入れて発言
    1. プレイリスト名のスレッドに返信でyoutubeの動画URLを発言
        - 1発言に1URL，他に余分な文字列はつけないこと
        - 短縮URL youtu.be もOK
    1. プレイリストに入れたいURLを全て発言し終えたら，`@BOTNAME playlist` と発言すると完成
    1. 重複チェックしたい時は `@BOTNAME check`

## Installation

### 1. slack アプリの作成

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

### 2. slack アプリのデプロイ
#### 2.1 run with python command

1. bot を動作させるサーバに python と pipenv をインストールする
2. `Pipfile` のあるディレクトリで `pipenv install` で必要なパッケージをインストール
3. `pipenv shell` で作った環境に入る
4. `python sui-chan.py` で実行
5. うまく動作することを確認できたら，`tmux` を使うなりなんなりして，サーバからログアウトしても動作するようにする (なんちゃって常駐化)

#### 2.2 run as docker container

1. `docker build -t suichan:latest .` などのコマンドでコンテナ作成
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

### 4. youtube Data API v3 クライアントの作成

#### 4.1 GCP のアカウント・プロジェクトの作成

GCPアカウント・プロジェクトは既にあるものとする．

#### 4.2 Youtube Data API v3 の OAuth クライアント ID を作成するための OAuth 同意画面の作成

1. GCPのプロジェクト内で「Youtube Data API」を検索し，有効化されてなければ有効化する
1. YouTube Data API v3の管理画面の左のメニューから「認証情報」を選択
1. 認証情報を作成
    - OAuthクライアントIDを選択
    - 画面に従って進めようとすると同意画面の作成をさせられるので，画面に従って作成
    - User Type は外部
    - スコープの設定は不要
    - テストユーザーには操作したいYoutubeアカウントにしているgoogleアカウントを設定
1. 保存して次へ

#### 4.3 Youtube Data API v3 の OAuth クライアント ID の作成

1. 再度，YouTube Data API v3の管理画面の左のメニューから「認証情報」を選択
1. 認証情報を作成
    - OAuthクライアントIDを選択
    - デスクトップアプリを選択し名前をつける

#### 4.4 Youtube Data API v3 の OAuth クライアント ID と クライアントシークレット の JSON を保存

1. OAuthクライアントIDを作成した画面または認証情報の画面から，JSONをダウンロード
1. 適当な名前にリネームしファイルを保存

#### 4.5 secret.toml の youtube-client テーブルのファイル名を指定

1. 設定したファイル名を secret.toml の youtube-client の CLIENT_SECRET_FILE へ指定
1. OAUTH_TOKEN_JSON は，適当なJSONファイル名を指定 (ファイルはなくても良い)

#### 4.6 OAuth トークンの取得

1. `python youtu.py` を実行し，画面に従ってOAuth認証を完了させる


### 5. ログレベル

| log level | description                                |
|-----------|--------------------------------------------|
| ERROR     | 本番環境でも出力・監視すべきエラー         |
| INFO      | 本番ではなくても良い，関数の開始などの通知 |
| DEBUG     | デバッグ用の詳細情報                       |

# TODO

次に実装する機能

issue へ記述。

- 動的ロード機能
    - [design.md]
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

