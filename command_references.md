# command references

This is a bot program that monitors message on joining slack and work according
to command in the message.


Let botname be `BOTNAME`, then you can mention bot by typing `@BOTNAME`.
You can order bot to various command by typing `@BOTNAME COMMAND [OPTIONS]`.

## slack message control
### remove message in the channel

`@BOTNAME clear [all|NUM]`,  
where `NUM` is the number that you want to remove.

If you type this command in a channel, bot remove channel messages.
Target message has replies, this command also remove them.

If you type this command in a thread, bot remove all replies in the thread and
thread head message.
In this case, any `OPTIONS` are ignored, and remove all replies.

## bot status
### tell channel names where the bot joins

`@BOTNAME where`

## YouTube playlist handling

For this bot, a thread is a playlist and replies of the thread are playlist
items.

### read your playlist or public playlist

`@BOTNAME pick URL`,  
where `URL` is a playlist URL.

Acceptable format is `https://youtube.com/playlist?list=PLAYLIST_ID`.
Any other QUERY_STRING is not acceptable.

Playlist items are written as replies of pick command.
If you type this command in a thread, bot adds items to the thread.

### check duplicate item in a thread

`@BOTNAME check`

If there are duplicate items in a thread, video ids and ordinal numbers of
them are written in the thread. Then 1st items are not written.

### make playlist with replies

`@BOTNAME playlist`

Make playlist. Name of it is thread head message. Items of it are replies of
the thread.
Acceptable video URL is
`https://youtu.be/VIDEO_ID`
or `https://www.youtube.com/watch?v=VIDEO_ID`.

## debug
### read slack message and dump to log

This is a command to debug bot program.
It might be useless for general user.

`@BOTNAME read`

