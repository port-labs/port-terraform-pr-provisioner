import logging
import sys

formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s')
# log_stream_handler = logging.StreamHandler(sys.stdout)
log_stream_handler = logging.StreamHandler()
log_stream_handler.setLevel(logging.INFO)
log_stream_handler.setFormatter(formatter)
