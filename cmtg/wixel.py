import re
import time
from typing import List, Optional, Tuple

import serial as pyserial
from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo


VID = 8187
PID = 8704

CHANNEL_QTY = 256
FREQUENCIES = [round(2403.47 + (i * 0.2864), 2) for i in range(CHANNEL_QTY)]


class Wixel:
    def __init__(self, serial_number: str, device: str):
        self._serial_number = serial_number
        self._ser = pyserial.Serial()
        self._ser.port = device

    @property
    def serial_number(self):
        return self._serial_number

    @property
    def serial(self) -> pyserial.Serial:
        return self._ser

    @property
    def device(self):
        return self._ser.port

    def get_signal_values(self, timeout: float = 1.5) -> Optional[List[int]]:
        if not self.serial.is_open:
            raise RuntimeError("the Wixel serial port is closed;")

        cached_timeout = self.serial.timeout
        self.serial.timeout = timeout

        start_at = time.time()
        result = None
        while not result and ((time.time() - start_at) < timeout):
            try:
                b = self.serial.read(1)
            finally:
                self.serial.timeout = cached_timeout
            time.sleep(0.4)
            package = b"".join([b, self.serial.read(self.serial.in_waiting)])
            result = self._extract_signal_values(package)
        return result

    def _extract_signal_values(self, package: bytes) -> List[int]:
        s = package.decode("utf-8", errors="replace")
        match = re.match(r"^.*\[ ([0-9\-\ ]+) \]\r\n\n$", s)
        if match:
            return list(map(int, match.group(1).split()))
        return

    def __repr__(self):
        return (
            f'Wixel(serial_number="{self.serial_number}", '
            f"device={self.device}, serial={self.serial})"
        )

    def __hash__(self) -> int:
        return int(
            "".join(re.findall(r"[0-9A-Fa-f]", str(self.serial_number))),
            base=16,
        )

    def __eq__(self, other: "Wixel") -> bool:
        return self.__class__ == other.__class__ and hash(self) == hash(other)


def is_wixel_port(device: ListPortInfo) -> bool:
    return device.vid == VID and device.pid == PID


def search_connected() -> List[Wixel]:
    result = []
    for cp in filter(is_wixel_port, comports()):
        result.append(Wixel(cp.serial_number, cp.device))
    return result


class ConnectionStorage:
    def __init__(self):
        self.connected = []

    def update(self, wxls: List[Wixel]) -> Tuple[List[Wixel], List[Wixel]]:
        new_conn = list(set(wxls).difference(self.connected))
        disconn = list(set(self.connected).difference(wxls))
        self.connected = wxls
        return new_conn, disconn
