import itertools
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional

from cmtg import utils, wixel


@dataclass
class Signal:
    channel_qty: int = wixel.CHANNEL_QTY
    total_qty: int = 0
    total: List[int] = field(init=False)
    buffer: deque = field(init=False)

    def __post_init__(self):
        self.total = [0] * self.channel_qty
        self.buffer = deque(maxlen=100)

    def append(self, values: List[int]) -> None:
        self.buffer.append(values)
        self.total = list(map(sum, zip(self.total, values)))
        self.total_qty += 1

    def get_last(self) -> Optional[List[int]]:
        if bool(self.buffer):
            return self.buffer[-1]
        return

    def get_avg_last_10(self) -> Optional[List[int]]:
        if len(self.buffer) >= 10:
            values_range = list(self.buffer)[-10:]
            sum_ = map(sum, zip(*values_range))
            divmods = map(divmod, sum_, itertools.repeat(10, self.channel_qty))
            avg_values, _ = zip(*divmods)
            return list(avg_values)
        return

    def get_avg_last_100(self) -> Optional[List[int]]:
        if len(self.buffer) == 100:
            sum_ = map(sum, zip(*self.buffer))
            divmods = map(
                divmod, sum_, itertools.repeat(100, self.channel_qty)
            )
            avg_values, _ = zip(*divmods)
            return list(avg_values)
        return

    def get_avg_all(self) -> Optional[List[int]]:
        if self.total_qty > 0:
            divmods = map(
                divmod,
                self.total,
                itertools.repeat(self.total_qty, self.channel_qty),
            )
            avg_values, _ = zip(*divmods)
            return list(avg_values)
        return


@dataclass
class WixelSession:
    wxl: wixel.Wixel
    conn_time: float = field(init=False)
    signal: Signal = field(init=False)

    def __post_init__(self):
        self.conn_time = time.time()
        self.signal = Signal()

    @property
    def stats(self) -> dict:
        return {
            "connected": time.time() - self.conn_time,
            "packages": self.signal.total_qty,
        }


class WixelSessionMap(dict):
    @property
    def sessions(self) -> List[WixelSession]:
        return list(self.values())  # Prevented RunTime error by view object.

    def register(self, wxl: wixel.Wixel) -> None:
        self[wxl.serial_number] = WixelSession(wxl)
        return

    def remove(self, wxl: wixel.Wixel) -> None:
        self.pop(wxl.serial_number, None)
        return


@dataclass
class LogBuffer:
    handler: utils.ExtBufferingHandler
    buffer: deque = field(init=False)
    _tick: int = field(init=False)

    def __post_init__(self):
        self.buffer = deque(maxlen=100)
        self._tick = 0

    @property
    def tick(self):
        return self._tick

    def update(self) -> None:
        logs = self.handler.flush()
        if not logs:
            return

        self.buffer.append(logs)
        self._tick += 1

    def get_after(self, tick: Optional[int] = None) -> List[logging.LogRecord]:
        if not self.buffer:
            return []

        if not tick:
            return sum(self.buffer, [])

        if tick <= 0 or tick >= self._tick:
            return []

        pos = self._tick - tick
        return sum(list(self.buffer)[-pos:], [])
