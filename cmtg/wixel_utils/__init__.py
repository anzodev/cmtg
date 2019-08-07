import itertools
import json
import os
import random
import re
import secrets
import time
from typing import List

from cmtg import wixel


class MockWixel(wixel.Wixel):
    def __init__(self):
        signal_path = os.path.join(os.path.dirname(__file__), "signal.json")
        with open(signal_path) as f:
            values = json.loads(f.read())
            random.shuffle(values)
            self._signal = itertools.cycle(values)

        serial_number = "-".join(
            re.findall(r".{2}", secrets.token_hex(4))
        ).upper()

        _, slave = os.openpty()
        device = os.ttyname(slave)

        super().__init__(serial_number, device)

    def get_signal_values(self) -> List[int]:
        time.sleep(0.5)
        return self._extract_signal_values()

    def _extract_signal_values(self) -> List[int]:
        return next(self._signal)


def patch_search_connected(mock_wxls_qty: int) -> None:
    wxls_pool = [MockWixel() for _ in range(mock_wxls_qty)]

    def search_connected_mock():
        return wxls_pool

    setattr(wixel, "search_connected", search_connected_mock)
