from __future__ import annotations

from logging.config import dictConfig

from ops_agent.config import AppSettings


def configure_logging(settings: AppSettings) -> None:
    formatter = (
        '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
        if settings.logging.json_logs
        else "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"default": {"format": formatter}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {"level": settings.logging.level.upper(), "handlers": ["console"]},
        }
    )
