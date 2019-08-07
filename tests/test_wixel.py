import os
import re
import time

import serial as pyserial
from serial.tools.list_ports_common import ListPortInfo

from cmtg import wixel


def test_wixel_init(make_serial_number):
    serial_number = make_serial_number()
    device = os.devnull
    wxl = wixel.Wixel(serial_number, device)
    assert wxl.serial_number == serial_number
    assert wxl.device == device
    assert isinstance(wxl.serial, pyserial.Serial)
    assert wxl.serial is wxl._ser
    assert wxl.serial.port == device


def test_wixel_init_port_opening(make_serial_number):
    device = os.ttyname(os.openpty()[1])
    ser = pyserial.Serial(port=device)
    assert ser.is_open == True
    ser.close()

    serial_number = make_serial_number()
    wxl = wixel.Wixel(serial_number, device)
    assert wxl.serial.is_open == False


def test_wixel_extract_signal_values(make_wxl, make_signal_values_and_package):
    _, wxl = make_wxl()
    signal_values, package = make_signal_values_and_package()
    result_values = wxl._extract_signal_values(package)
    assert result_values == signal_values


def test_wixel_get_signal_values(make_wxl, make_signal_values_and_package):
    master, wxl = make_wxl()
    signal_values, package = make_signal_values_and_package()
    with wxl.serial:
        os.write(master, package)
        result_values = wxl.get_signal_values()
    assert result_values == signal_values

    with wxl.serial:
        result_values = wxl.get_signal_values(timeout=0.5)
    assert result_values is None


def test_wixel_get_signal_values_timeout(make_wxl):
    _, wxl = make_wxl()
    wxl.serial.timeout = 4
    with wxl.serial:
        start_at = time.time()
        wxl.get_signal_values(timeout=1)
        finish_at = time.time()
    assert round(finish_at - start_at, 1) == 1.4


def test_wixel_hash(make_wxl):
    _, wxl = make_wxl()
    serial_number = wxl.serial_number
    hash_ = int(
        "".join(re.findall(r"[0-9A-Fa-f]", str(serial_number))), base=16
    )
    assert hash_ == hash(wxl)


def test_wixel_equality(make_serial_number):
    serial_number_a = make_serial_number()
    serial_number_b = make_serial_number()
    device_a = os.ttyname(os.openpty()[1])
    device_b = os.ttyname(os.openpty()[1])
    assert wixel.Wixel(serial_number_a, device_a) == wixel.Wixel(
        serial_number_a, device_b
    )
    assert wixel.Wixel(serial_number_a, device_a) != wixel.Wixel(
        serial_number_b, device_a
    )
    assert wixel.Wixel(serial_number_a, device_a) != pyserial.Serial()


def test_wixel_context_port_opening(make_wxl):
    _, wxl = make_wxl()
    with wxl.serial:
        assert wxl.serial.is_open == True
    assert wxl.serial.is_open == False


def test_is_wixel_port():
    port = ListPortInfo()
    port.vid = 4321
    port.pid = 5678
    assert wixel.is_wixel_port(port) == False
    port.vid = wixel.VID
    port.pid = wixel.PID
    assert wixel.is_wixel_port(port) == True


def test_connection_storage(make_wxl):
    wxls_pool = [make_wxl() for _ in range(5)]
    conn_sto = wixel.ConnectionStorage()
    new_conn, disconn = conn_sto.update(wxls_pool[:3])
    assert set(new_conn) == set(wxls_pool[:3])
    assert set(disconn) == set()
    new_conn, disconn = conn_sto.update(wxls_pool[:4])
    assert set(new_conn) == set([wxls_pool[3]])
    assert set(disconn) == set()
    new_conn, disconn = conn_sto.update(wxls_pool[1:3])
    assert set(new_conn) == set()
    assert set(disconn) == set([wxls_pool[0], wxls_pool[3]])
    new_conn, disconn = conn_sto.update(wxls_pool[2:5])
    assert set(new_conn) == set(wxls_pool[3:])
    assert set(disconn) == set([wxls_pool[1]])
    assert set(conn_sto.connected) == set(wxls_pool[2:5])
