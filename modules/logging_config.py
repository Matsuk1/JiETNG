"""Application logging setup."""

import logging

import urllib3


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"
    GRAY = "\033[90m"

    def format(self, record):
        original_levelname = record.levelname
        try:
            color = self.COLORS.get(original_levelname)
            if color:
                record.levelname = f"{color}{original_levelname}{self.RESET}"
            formatted = super().format(record)
            return formatted.replace(
                record.asctime,
                f"{self.GRAY}{record.asctime}{self.RESET}",
                1,
            )
        finally:
            record.levelname = original_levelname


def configure_logging(log_file, logger_name=None):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
    )
    return logging.getLogger(logger_name)
