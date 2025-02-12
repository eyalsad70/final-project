""" 
MAIN Handler of travel app project
"""
import sys
import os
from common_utils.local_logger import logger
import common_utils.kafka_common as kfk
from common_utils.kafka_consumer import poll_and_process_messages
from message_handler import process_message

# Add the parent folder to sys.path
#sys.path.append(os.path.abspath("../common_utils"))
sys.path.append(os.path.abspath("."))
#print(sys.path)


if __name__ == "__main__":
   logger.info("Starting Results Service")
   poll_and_process_messages(kfk.RESULTS_TOPIC_NAME, process_message)
   