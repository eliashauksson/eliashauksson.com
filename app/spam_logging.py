import logging
import os

from flask import request

SPAM_LOGGER_NAME = "eliashaukssoncom.spam"


def configure_spam_logger(project_root: str) -> None:
    log_dir = os.path.join(project_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "spam.log")

    logger = logging.getLogger(SPAM_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == log_path:
            return

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s\t%(message)s"))
    logger.addHandler(handler)


def log_spam(reason: str, email: str = "") -> None:
    logging.getLogger(SPAM_LOGGER_NAME).info(
        "ip=%s\treason=%s\temail=%s",
        _clean(request.remote_addr or "-"),
        _clean(reason),
        _clean(email),
    )


def _clean(value: str) -> str:
    return " ".join((value or "").split())[:254]
