import os
import logging
import inspect
from datetime import datetime

# Custom handler
class CustomErrorHandler(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.INFO:  # Only trigger on errors
            print(record.getMessage())
            
class Logger:
    def __init__(self, current_file_name='route_plan_logger'):
        """
        The log file format is standardized and shared across all utilities.
        """
        try:
            if current_file_name is None:
                # Identify the calling module's file name
                frame = inspect.stack()[1]  # Get the caller frame
                module = inspect.getmodule(frame[0])
                current_file_name = os.path.splitext(os.path.basename(module.__file__))[0] if module else "default_log"

            log_file = f"logs/{current_file_name}.log"
            os.makedirs("logs", exist_ok=True)  # Ensure logs directory exists

            logging.basicConfig(
                filename=log_file,
                level=logging.INFO,
                format="%(asctime)s %(levelname)s %(filename)s : %(message)s",
                datefmt="%d-%m-%Y %H:%M:%S"
            )
            self.logger = logging.getLogger(current_file_name)
            custom_handler = CustomErrorHandler()
            self.logger.addHandler(custom_handler)
        except Exception as e:
            print(f"Error setting up logging: {e}")
            exit(1)

    def get_logger(self):
        return self.logger

# Initialize a global logger instance
logger = Logger().get_logger()