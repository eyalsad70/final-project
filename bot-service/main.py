""" 
MAIN Handler of travel app project
"""
import sys
import os
from common_utils.local_logger import logger
from common_utils import utils
import my_bot

# Add the parent folder to sys.path
#sys.path.append(os.path.abspath("../common_utils"))
sys.path.append(os.path.abspath(".."))


if __name__ == "__main__":
   #my_logger.init_logger()
   logger.info("Staring BOT Service")
 #   init_keys()
   utils.load_israeli_cities()
    
   # my_bot.send_welcome_message()
   my_bot.start_bot()