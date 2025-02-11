"""
Telegram BOT handlers
initialize the bot, listen on requests, and support responses through handlers
"""

import requests
import json
from common_utils.local_logger import logger
import os
import telebot

test_token = os.getenv('TELEGRAM_BOT_TOKEN') # keys_loader.load_private_key("telebot") 
if not test_token:
    logger.error("Error: test_token not found")
    raise ValueError("test_token not found!")

bot_name = "route-planner-101-bot"
root_chat_id = 6550133750  # int(keys_loader.load_private_key("telebot_id"))


# Get url for updates - run this once from Browser (not from here) to get chat id
# if you get empty list enter some text in the bot itself and
bot_url_get_updates = f'https://api.telegram.org/bot{test_token}/getUpdates'
#print(bot_url_get_updates)

def send_message(chat_id, text):
    # put your chat id and send a message
    bot_url = f'https://api.telegram.org/bot{test_token}/'

    url = bot_url + f'sendMessage?chat_id={chat_id}&text={text}'
    print(url)
    logger.info(url)
    
    # # Print the get request
    resp = requests.get(url)
    #print(resp.text)

    if resp.status_code == 200:
        message = json.loads(resp.text)['result']
        #print(message)
        logger.info(message)
        return True
    else:
        logger.error(f"failed to send text of len {len(text)} to BOT. error {resp.status_code}")
        return False
        

def bot_log_message(message):
        logger.info(f"Message ID: {message.message_id} From User ID: {message.from_user.id} ; Message Text: {message.text}")

