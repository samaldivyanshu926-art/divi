"""Centralised logging configuration.

Every script/module in this repository calls :func:`get_logger` instead of
calling ``logging.basicConfig`` itself. That keeps log formatting consistent
and means the format/level can be changed in exactly one place — a small
thing, but it is the difference between a package and a pile of scripts.
"""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def configure_root_logging(level: int = logging.INFO) -> None:
    """Configure the root logger once, idempotently.

    Safe to call from every module's import path — a second call is a
    no-op, so import order never causes duplicate log handlers.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger, configuring root logging if needed."""
    configure_root_logging()
    return logging.getLogger(name)
