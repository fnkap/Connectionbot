import json
import logging
import re
import time
from telnetlib import Telnet

import telegram
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import Updater

# Configuration
TOKEN = ""  # The token of the Telegram bot
OWNER_ID = 123456  # Your Telegram personal id
TIME_TO_SLEEP = 10  # Time between observations of the connected devices
ROUTER_IP = ''
ROUTER_PORT = 23
ROUTER_USERNAME = ""
ROUTER_PASSWORD = ""
LOGGING_FILE = ""  # Logging file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGGING_FILE),
        logging.StreamHandler()
    ])

# This dictionary will contain every device info
devices = {}

# Initialize the bot, the updater and the dispatcher
bot = telegram.Bot(token=TOKEN)
updater = Updater(token=TOKEN)

dispatcher = updater.dispatcher

try:
    with open('connection_bot.json', 'r') as json_file:
        exceptions = json.load(json_file)
except FileNotFoundError:
    exceptions = {}
except Exception as e:
    logging.exception(e, exc_info=True)
    exceptions = {}

print(exceptions)


def save_exceptions_to_file():
    with open('connection_bot.json', 'w') as outfile:
        json.dump(exceptions, outfile)


# This function will reply "pong" just to check the bot is alive
def ping(bot, update):
    logging.info("Requested function: ping")
    update.message.reply_text("pong")


# This function will reply with the list of connected devices
def connected(bot, update):
    logging.info("Requested function: connected")
    str_to_send = ""
    for device in devices:
        if "C" in devices[device]["flags"]:
            str_to_send += f"Mac Address: {devices[device]['mac']}\n" \
                f"IP Address: {devices[device]['ipv4']}\n" \
                f"Hostname: {devices[device]['hostname']}\n\n"
    if str_to_send == "":
        update.message.reply_text("No devices connected")
    else:
        update.message.reply_text(str_to_send)


# Function to add exceptions for notifications
def ex(bot, update, args):
    if args[0] == "add":
        if args[1] == "ip" or args[1] == "mac" or args[1] == "host":
            try:
                if args[2] not in exceptions[args[1]]:
                    exceptions[args[1]].append(args[2])
                    update.message.reply_text("Exception added.")
                else:
                    update.message.reply_text("Exception already there.")
                args[0] = "list"  # Continuing the code, sends the list
            except KeyError:
                exceptions[args[1]] = [args[2]]
                update.message.reply_text("Exception added.")
                args[0] = "list"  # Continuing the code, sends the list

    if args[0] == "rem":
        if args[1] == "ip" or args[1] == "mac" or args[1] == "host":
            try:
                exceptions[args[1]].remove(args[2])
            except KeyError:
                pass
        if args[1] == "all":
            exceptions.clear()
            args[0] = "list"  # Continuing the code, sends the list

    if args[0] == "list":
        str_to_send = ""
        for i in exceptions:
            for j in exceptions[i]:
                str_to_send += f"{i} {j}\n"
        if str_to_send:
            str_to_send = "Exceptions:\n" + str_to_send
            update.message.reply_text(str_to_send)
        else:
            update.message.reply_text("No exceptions found.")
    save_exceptions_to_file()


dispatcher.add_handler(CommandHandler('ping', ping, Filters.user(user_id=OWNER_ID)))
dispatcher.add_handler(CommandHandler('connected', connected, Filters.user(user_id=OWNER_ID)))
dispatcher.add_handler(CommandHandler('ex', ex, Filters.user(user_id=OWNER_ID), pass_args=True))

updater.start_polling()

# Sends a message to the owner when the bot is started.
while True:
    try:

        bot.send_message(OWNER_ID, "Started")
        break

    except telegram.error.NetworkError:

        time.sleep(TIME_TO_SLEEP)
        continue

# Checks for devices status every TIME_TO_SLEEP seconds.
# Sends a message to OWNER_ID if a device connects.
# The following code is actually specific for each different router model.
while True:
    try:
        # Connection to telnet
        with Telnet(ROUTER_IP, ROUTER_PORT) as tn:
            tn.read_until(b'Username : ', 15)
            tn.write(bytes(ROUTER_USERNAME, "utf-8") + b"\r")
            tn.read_until(b'r\r\nPassword : ')
            tn.write(bytes(ROUTER_PASSWORD, "utf-8") + b"\r")
            tn.read_until(b'Administrator}=>')
            tn.write(b"hostmgr list\r")
            tn.read_until(b' --------            \r\n')

            end = False
            while not end:
                line = tn.read_until(b"\r\n", 2).replace(b"\r\n", b"").decode('utf-8')

                if line == "{Administrator}=>":
                    end = True
                    continue

                found = re.split(" +", line)

                if len(found) > 8:
                    found = found[:8]

                if len(found) == 7:
                    found.insert(3, "-")

                mac, ipv4, ipv6, flags, mtype, intf, hwintf, hostname = found

                # Check if I've already seen this device
                if mac in devices:
                    # If it wasn't connected, and now it is, notify me
                    if ("C" not in devices[mac]["flags"]) and ("C" in flags):
                        ex_ip = exceptions.get("ip", [])
                        ex_mac = exceptions.get("mac", [])
                        ex_host = exceptions.get("host", [])
                        if not (ipv4 in ex_ip or mac in ex_mac or hostname in ex_host):
                            logging.info(f"Connected: {mac}")
                            string_to_send = "⚠️New connection:\n" \
                                f"Mac Address: {mac}\n" \
                                f"IP Address: {ipv4}\n" \
                                f"Hostname: {hostname}"
                            while True:
                                try:
                                    bot.send_message(OWNER_ID, string_to_send)
                                    break

                                except telegram.error.NetworkError as e:
                                    logging.exception(e, exc_info=True)
                                    logging.info("NetworkError, sleeping {} seconds.".format(TIME_TO_SLEEP))
                                    time.sleep(TIME_TO_SLEEP)
                                    continue

                devices[mac] = {"mac": mac,
                                "ipv4": ipv4,
                                "ipv6": ipv6,
                                "flags": flags,
                                "mtype": mtype,
                                "intf": intf,
                                "hwintf": hwintf,
                                "hostname": hostname}
    except OSError as e:
        logging.exception(e, exc_info=True)
        pass
    except Exception as e:
        logging.exception(e, exc_info=True)
        pass

    time.sleep(TIME_TO_SLEEP)
