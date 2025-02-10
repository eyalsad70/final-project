import os
import logging
import inspect
from datetime import datetime

class Logger:
    def __init__(self, current_file_name=None):
        """
        Set up logging with a log file named based on the given module name.
        If no name is provided, it defaults to the calling module.
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
                format="%(asctime)s %(levelname)s: %(message)s",
                datefmt="%d-%m-%Y %H:%M:%S"
            )
            self.logger = logging.getLogger(current_file_name)
        except Exception as e:
            print(f"Error setting up logging: {e}")
            exit(1)

    def get_logger(self):
        return self.logger

# Initialize a global logger instance
logger = Logger().get_logger()