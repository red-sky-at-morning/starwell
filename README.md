# STARWELL
*A discord bot for the Daybreak System*

(Based off of [Eclipsebot v2](https://github.com/red-sky-at-morning/discord_bot)'s code.)

Features (wip):
- Stores/displays member data (/webhooks/meta/members.json)
- Allows sending messages as webhooks
    - Allows reproxying, editing, replying, and deleting messages sent with webhooks
- Can globally disable and enable channels and servers
    - Uses a reciprocal blacklist/whitelist system, where a channel can't be in both at once
    - Can specify reasons for disabling channels/servers