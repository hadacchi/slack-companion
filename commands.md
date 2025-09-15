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

## Cron Commands (`cron`)

Schedules a command for routine execution.

### Add a job (`daily` or `weekly`)

`@BOTNAME cron [daily|weekly] <command_to_schedule>`

Schedules a command to be executed daily or weekly. The command will be executed in the channel where this scheduling command is issued.

**Example:**
`@BOTNAME cron daily slack clear all`
This command schedules `@BOTNAME slack clear all` to be run daily.

### List jobs (`list`)

`@BOTNAME cron list`

Lists all registered daily and weekly jobs.