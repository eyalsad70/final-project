""" 
MAIN Handler of travel app project
"""
import sys
import os
from common_utils.local_logger import logger
from kafka_consumer import poll_messages

# Add the parent folder to sys.path
#sys.path.append(os.path.abspath("../common_utils"))
sys.path.append(os.path.abspath("."))
#print(sys.path)


if __name__ == "__main__":
   logger.info("Staring API Service")
   poll_messages()
   