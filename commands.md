# Command Reference

This bot executes commands sent via mentions on Slack.

The basic format is as follows. `@BOTNAME` should be replaced with the actual name of the bot.

`@BOTNAME COMMAND [SUBCOMMAND] [OPTIONS]`

---

## General Commands

---

## Slack Commands (`slack`)

### List joined channels (`where`)

`@BOTNAME slack where`

Returns a list of channels the bot has joined.

### Clear channel messages (`clear`)

`@BOTNAME slack clear [all|number]`

Deletes messages in the channel where the command is issued.

- `all`: Deletes all messages in the channel.
- `number`: Deletes the specified number of recent messages.

**Example:**
`@BOTNAME slack clear 10`
This command deletes the 10 most recent messages.

---

## Home AP Commands (`ap`)

### List registered devices (`devices`)
`@BOTNAME ap devices`

### Add a device (`add`)
`@BOTNAME ap add <device_name>`

### Remove a device (`del`)
`@BOTNAME ap del <device_name>`