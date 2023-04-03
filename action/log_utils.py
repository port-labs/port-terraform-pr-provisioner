import sys
from clients.port import add_action_log_message
import logging

formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s')
log_stream_handler = logging.StreamHandler()
log_stream_handler.setLevel(logging.INFO)
log_stream_handler.setFormatter(formatter)


def log_and_add_action_log_line(logger: logging.Logger, run_id: str, message: str):
    logger.info(message)
    add_action_log_message(run_id=run_id, message=message)
