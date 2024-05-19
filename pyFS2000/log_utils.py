import logging

from icecream import ic


def set_logger(level=logging.WARNING, fmt='%(asctime)s - %(levelname)s - %(message)s', stream=True, log_file=None):
    logger = logging.getLogger('FS2000')
    logger.handlers.clear()
    if stream:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(stream_handler)
    if (log_file is not None) and (log_file != ''):
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(file_handler)
    logger.setLevel(level)
    logger.propagate = False
