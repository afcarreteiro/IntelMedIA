import logging


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def redact(value: str) -> str:
    return "[redacted]" if value else ""
