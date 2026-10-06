"""Logs estructurados en JSON, sin contraseñas, tokens ni datos personales."""

import json
import logging
import sys
from datetime import UTC, datetime

_RESERVED_ATTRS = set(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {"message", "asctime"}
_SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "cookie",
    "secret",
    "email",
    "phone",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _RESERVED_ATTRS or key.startswith("_"):
                continue
            payload[key] = "[REDACTED]" if key.lower() in _SENSITIVE_KEYS else value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    app_logger = logging.getLogger("bazarnimal")
    app_logger.handlers = [handler]
    app_logger.setLevel(level)
    app_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"bazarnimal.{name}")


# Eventos de seguridad: logins fallidos, accesos denegados, bloqueos por rate limit.
security_logger = get_logger("security")
