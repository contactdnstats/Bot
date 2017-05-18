# DNStats bot
DNStats bot is a reddit bot whose sole purpose is to listen on
[/r/DNStats](https://www.reddit.com/r/DNStats/) and provide status
for DN markets.

## Invoking SchmeckleBot

Any comment with `is MARKETNAME down?` on the subreddit will invoke the bot

===

> Hey there! Is agora down?

    *Bot: Market agora is Down. With an uptime of 37.61%. The last time online was 1 year, 8 month

---

===

#### Requirements
The bot is build with python3.6. If you have that. Create and virtualenv
and install the requirements with `pip install -r requirements.txt`

#### Running it:
THe bot can be run with just python bot.py. If you want to run it daemonized
and store the logs you can run the sh script `run_bot.sh` with `sh run_bot.sh`# Bot
