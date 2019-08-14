import logging
import logging.handlers
from typing import List


class ExtBufferingHandler(logging.handlers.BufferingHandler):
    def flush(self) -> List[logging.LogRecord]:
        buffer = self.buffer
        super().flush()
        return buffer
