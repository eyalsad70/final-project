"""
Telegram BOT handlers
initialize the bot, listen on requests, and support responses through handlers
"""

import telebot
import time
from common_utils.local_logger import logger
from common_utils.telegram_bot import test_token, root_chat_id, bot_log_message, send_message
import user_session


# Create bot class
bot = telebot.TeleBot(test_token)


def start_bot():    
    # start listening
    bot.polling()

    
def send_welcome_message():
    current_time = time.localtime()
    time_string = time.strftime("%Y-%m-%d %H:%M:%S", current_time)

    text = f'Wake up!! Its {time_string}'
    send_message(root_chat_id, text)
        
def bot_send_start_message(message):
    bot.reply_to(message, "welcome to your Route Planner BOT")
    with open('./bot-service/route-icon.jpg', 'rb') as photo:
        bot.send_photo(message.from_user.id, photo)
    bot.reply_to(message, "press any key to start!!!")
    
    
## ---------------------------------------------------------------------------------
@bot.message_handler(commands=['start'])
def welcome(message):
    # get user session for this user. create it if not exists. Note that this 'start' command can be used also to restart session
    #userSession = user_session.get_user_session(message.from_user.id, True)
    #userSession.start()
    bot_send_start_message(message)
    

## ---------------------------------------------------------------------------------
@bot.message_handler(content_types=['text'])
def handle_response(message):
   
    bot_log_message(message)

    my_user:user_session.UserInfo = user_session.get_user(message.from_user.id)
    if not my_user:
        user_id = message.from_user.id
        user_name = message.from_user.full_name
        my_user = user_session.create_user(user_id, user_name)
        # TBD - Start bot interaction for new user, getting its details
        # for now, use stub
        bot.reply_to(message, f"Hello {user_name}")
        bot.reply_to(message, "press /start to begin!!")
        return
    
    userSession, is_new_route = user_session.get_user_active_route(my_user.user_id)
    
    if userSession:        
        response = userSession.handle_user_message(message)
        if response:
            bot.reply_to(message, response)
    #     response = userSession.next_bot_action()
    #     if response:
    #         bot.reply_to(message, response)
    else:
        bot.reply_to(message, "press /start to begin!!")


if __name__ == "__main__":
    send_welcome_message()
