import logging
import queue
from logging import Handler, LogRecord
from typing import Optional

class QueueLogHandler(Handler):
    """A logging handler that pushes log records into a Queue for GUI consumption."""
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: LogRecord) -> None:
        try:
            msg = self.format(record)
            self.log_queue.put((record.levelname, msg))
        except Exception:
            # Never raise in logging
            pass


def setup_gui_logging(log_queue: queue.Queue, level: int = logging.INFO, fmt: Optional[str] = None) -> QueueLogHandler:
    """Attach a QueueLogHandler to root logger and return it.

    This keeps existing file/console handlers intact, just adds a GUI sink.
    """
    handler = QueueLogHandler(log_queue)
    formatter = logging.Formatter(fmt or "[%(asctime)s] %(levelname)s - %(message)s", "%H:%M:%S")
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)
    return handler
