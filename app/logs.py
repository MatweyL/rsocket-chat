import logging.config


LOGGER_NAME = "service_logger"

FORMAT = f"%(asctime)s : %(levelname)s : %(module)s : %(funcName)s : %(lineno)d : %(message)s"

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class CustomFormatter(logging.Formatter):

    grey = "\033[92m"
    yellow = "\033[33;20m"
    red = "\033[31m"
    blue = "\033[34m"
    green = "\033[32m"
    bold_red = "\033[1;31m"
    reset = "\x1b[0m"
    format = FORMAT
    datefmt = DATE_FORMAT

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


LOG_CONFIG = {
    "version": 1,
    'disable_existing_loggers': True,
    "formatters": {
        "default_formatter": {
            '()': CustomFormatter
        }
    },
    "handlers": {
        "stream_handler": {
            "class": "logging.StreamHandler",
            "formatter": "default_formatter"
        }
    },
    "loggers": {
        LOGGER_NAME: {
            "handlers": ["stream_handler"],
            "level": "DEBUG",
        }
    }
}

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger(LOGGER_NAME)
