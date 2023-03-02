import sys
from loguru import logger


def init_logging(debug=False):
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time}</green> <level>{message}</level>",
        level="DEBUG" if debug else "INFO",
    )
