# slack-companion

slack上のメッセージを見て，コマンドを解釈し，実行するbot

## How to Use

see [commands](commands.md) for details.

1. `@BOTNAME slack clear 10` で発言した channel の発言を最新10件削除
1. `@BOTNAME slack clear all` で発言した channel の発言を全件削除
1. `@BOTNAME slack where` で BOT の参加する channel list を返却

## Installation

### 1. Create a Slack App

First, you need to create a Slack app and configure it with the necessary permissions.

1.  **Go to https://api.slack.com/apps** and click "Create New App".
    *   Choose an **App Name** and select the **Development Slack Workspace**. You can name your bot whatever you like!
2.  **Enable Socket Mode**: Go to **Settings > Socket Mode**, enable it, and generate an app-level token with the `connections:write` scope. Copy this token.
3.  **Set OAuth & Permissions**: Go to **Features > OAuth & Permissions**.
    *   Add the following **Bot Token Scopes**:
        *   `channels:history`
        *   `channels:read`
        *   `chat:write`
    *   Add the same scopes to **User Token Scopes**.
4.  **Subscribe to Bot Events**: Go to **Features > Event Subscriptions**, enable it, and add the `message.channels` bot event.
5.  **Install App**: Go to **Settings > Install App** and install the app to your workspace.
6.  **Get Tokens**: After installation, go back to **Features > OAuth & Permissions** to get your tokens.
    *   **Bot User OAuth Token** (starts with `xoxb-`)
    *   **User OAuth Token** (starts with `xoxp-`)
7.  **Customize Display**: Go to **Settings > Basic Information** to set a custom name and icon for your bot.

Finally, create a `secret.toml` file in the project's root directory and add the tokens you've collected.

```toml
[slackbot]
# App-Level Token for Socket Mode (starts with xapp-)
token = "YOUR_APP_LEVEL_TOKEN"
# User OAuth Token (starts with xoxp-)
user_oauth_access_token = "YOUR_USER_OAUTH_TOKEN"
# Bot User OAuth Token (starts with xoxb-)
bot_user_oauth_access_token = "YOUR_BOT_OAUTH_TOKEN"
```

### 2. Deploy the Bot

This bot is designed to be run using Docker and Docker Compose.

#### 2.1. Build the Docker Image

Build the Docker image for the bot. We'll tag it as `slack-companion:latest`.

```bash
docker build -t slack-companion:latest .
```

#### 2.2. Run the Bot

With the `docker-compose.yml` file updated, start the services in detached mode.

```bash
docker-compose up -d
```

#### 2.3. Check Logs

You can follow the bot's logs to ensure it's running correctly.

```bash
docker-compose logs -f slack-companion
```


### 3. Add/Remove the Bot from Channels

1. **Invite**: In the channel where you want the bot to operate, type `/invite @BOTNAME` (replace `BOTNAME` with your bot's actual name).
2. **Remove**: To remove the bot from a channel, type `/kick @BOTNAME`.
3. **Verify**: Test the bot by sending a command like `@BOTNAME slack where`. If it responds with a list of channels it's in, the setup is successful.

### 4. ログレベル

| log level | description                                |
|-----------|--------------------------------------------|
| ERROR     | 本番環境でも出力・監視すべきエラー         |
| INFO      | 本番ではなくても良い，関数の開始などの通知 |
| DEBUG     | デバッグ用の詳細情報                       |

# TODO

次に実装する機能

issue へ記述。

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
