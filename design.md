# 設計書

v2で動的ロード機能をつけるために機能整理が必要

## coding rules

- 本書は、Visual Studio Codeで記述する。
- UML図は、PlantUMLによって作成する。
- プラグインは少なくとも以下の2つを導入する
   - plantuml
   - markdown preview enhanced
- PlantUMLで表示するためには、brewで以下のソフトを導入する
   - `brew install plantuml`
   - `brew install graphviz`
- PDF出力のためにはGoogle Chromeを導入する
- markdown preview enhancedで埋め込みUMLを表示するには、
  `Markdown-preview-enhanced: Plantuml Jar Path`へ`plantuml.jar`を指定する

## classes

```plantuml
@startuml scale 0.5
left to right direction
skinparam actorStyle awesome
package bot {
   package ctl_slack {
      usecase "delete messages" as del_msg
      usecase "delete reply" as del_reply
      usecase "listen messages" as listen_msg
   }
   usecase "order bot" as order_bot
   usecase "control youtube" as ctl_youtube
   usecase "control watchlist" as ctl_watchlist
}
del_msg -> del_reply
order_bot -> listen_msg
order_bot -> del_msg
order_bot -> ctl_youtube
order_bot -> ctl_watchlist
package plugins.fileio{
   usecase "store pictures" as get_pic
}
listen_msg --> get_pic
package plugins.watchlist{
   usecase follow_ch as "start to watch the channel logs
   ----
   join channel (manual)
   insert channel_id
   set true as watch flag to channel_id
   "
   usecase show_following as "show watching channel
   ----
   select channel_id where watch flag is true
   say channel_id
   "
   usecase unfollow_ch as "finish to watch the channel
   ----
   select channel_id where watch flag is true
   set false as watch flag to channel_id
   "
}
package plugins.youtube {
   usecase get_schedule as "get stream schedule
   ----
   access to youtube as me
   scan target channels
   extract scheduled attributes
   "
   usecase manage_playlist as "manage playlist
   ----
   get playlist items
   create playlist
   add items to playlist
   del items from playlist
   "
}
actor me
me --> order_bot
ctl_youtube --> get_schedule
ctl_youtube --> manage_playlist
ctl_watchlist --> follow_ch
ctl_watchlist --> show_following
ctl_watchlist --> unfollow_ch
@enduml
```

## ファイル構成

release-1.0 時点

```
/sui-chan.py             --- main 
   |
   +-- msgs.py           --- セリフと乱択
   |
   +-- msgprocessing.py  --- slackのmsg処理
   |
   +-- watch_list.py     --- 監視対象chの管理
   |
   +-- youtu.py          --- youtubeのAPI処理
   |
   +-- userprocessing.py
   |
   +-- dump_log.py       --- ログ出力関数
   |
   +-- mylogger.py       --- ロガー定義
```

## 新ファイル構成案

```
/sui-chan.py
   |
   +-- plugins/    --- ここの *.py をロード
```
