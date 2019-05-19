# Connectionbot

This bot will check if some host connects to your private network and notify you with Telegram.
It uses telnet to communicate with your router.
You have to modify it to work with your router. This version is working with a TG588v router.

## Getting Started

To use this bot you have to configure some parameters inside the script. These are the following:

- TOKEN: it's the token provided by @BotFather on Telegram.
- OWNER_ID: it's the ID of the account which will get the notifications. You can get your id using @get_id_bot.
- TIME_TO_SLEEP: time between observations of connected devices.
- ROUTER_IP: ip of the router.
- ROUTER_PORT: port of the telnet interface of the router.
- ROUTER_USERNAME: telnet username to access the router.
- ROUTER_PASSWORD: telnet password to access the router.
- LOGGING_FILE: filepath and filename of the logging file.

## Available functions

This is a description of available commands that you can send via Telegram.

    /ping

This function will reply "pong" just to check the bot is alive.

    /connected

This function will reply "pong" just to check the bot is alive

    /ex add [ip|mac|host] <value>
    
You can add exceptions to notifications sent. You can ignore a client connected by IP, Mac address or Hostname.


    /ex list

This function will send you a list of all exceptions you added.

    /ex rem [ip|mac|host] <value>

You can remove exceptions using this command.

