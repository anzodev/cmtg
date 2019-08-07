import os
import random
import re
import secrets

import pytest

from cmtg import wixel


@pytest.fixture
def make_serial_number():
    def _make_serial_number():
        return "-".join(re.findall(r".{2}", secrets.token_hex(4))).upper()

    return _make_serial_number


@pytest.fixture
def make_wxl(make_serial_number):
    def _make_wxl():
        master, slave = os.openpty()
        wxl = wixel.Wixel(make_serial_number(), os.ttyname(slave))
        return master, wxl

    return _make_wxl


@pytest.fixture
def make_signal_values():
    def _make_signal_values():
        return [random.randint(-110, -30) for _ in range(wixel.CHANNEL_QTY)]

    return _make_signal_values


@pytest.fixture
def make_signal_values_and_package(make_signal_values):
    def _make_signal_package():
        signal_values = make_signal_values()
        package_src = (
            "00-AB-CD-EF #10, 0x000044EE ms "
            f'[ {" ".join(map(str, signal_values))} ]\r\n\n'
        )
        return signal_values, package_src.encode("utf-8")

    return _make_signal_package
