"""Standardized logging configuration."""

import logging
from rich.logging import RichHandler
from rich.text import Text
from rich.console import Console
from rich.theme import Theme
from datetime import datetime

from beartype.typing import Optional


class __CustomHandler(RichHandler):

    def get_level_text(self, record: logging.LogRecord) -> Text:
        """Get level name."""
        return Text.styled(
            record.levelname,
            style=f"logging.level.{record.levelname.lower()}",
            justify="left"
        ).append(":" + record.name.ljust(8), style="bold white")


def configure_log(log: Optional[str] = None, level: int = 20) -> None:
    """Configure SilverLine logging.

    Parameters
    ----------
    log: File to save log to (if not None). Will save to `{log}-{date}.log`.
    verbose: Logging level to use (python convension; 0 is most verbose).
    """
    console = Console(theme=Theme({
        "logging.level.cri": "bold red",
        "logging.level.err": "bold bright_red",
        "logging.level.wrn": "bold bright_yellow",
        "logging.level.inf": "bold green",
        "logging.level.dbg": "bold cyan"
    }))

    handlers = [__CustomHandler(console=console, rich_tracebacks=True)]
    if log is not None:
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        handlers.append(logging.FileHandler("{}{}.log".format(log, date)))

    logging.addLevelName(logging.CRITICAL, 'CRI')
    logging.addLevelName(logging.ERROR, 'ERR')
    logging.addLevelName(logging.WARNING, 'WRN')
    logging.addLevelName(logging.INFO, 'INF')
    logging.addLevelName(logging.DEBUG, 'DBG')

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers)


def __fmt(x):
    if isinstance(x, int):
        return "x{:02x}".format(x)
    elif isinstance(x, str):
        return "u{}..{}".format(x[:2], x[-4:])
    return x


def format_message(msg, *ctx) -> str:
    """Format message with context."""
    if len(ctx) == 0:
        return msg
    return "[{}] {}".format(".".join([__fmt(x) for x in ctx]), msg)
