import logging
import sys
from app.core.config import settings

SENSITIVE_PATTERNS = ["api_key", "token", "password", "secret"]


class SensitiveFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage().lower()
        for pattern in SENSITIVE_PATTERNS:
            if pattern in msg:
                record.msg = "[REDACTED - sensitive content]"
                record.args = ()
                break
        return True


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("ai_perf_platform")
    logger.setLevel(logging.DEBUG if settings.app_env == "development" else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveFilter())

    if not logger.handlers:
        logger.addHandler(handler)

    return logger


logger = setup_logging()
