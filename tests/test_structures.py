from collections import deque

from cmtg import structures, wixel


def test_signal(make_signal_values):
    signal = structures.Signal()
    assert isinstance(signal.buffer, deque)
    assert signal.buffer.maxlen == 100
    assert bool(signal.buffer) == False
    assert signal.channel_qty == wixel.CHANNEL_QTY
    assert signal.total_qty == 0
    assert signal.total == [0] * wixel.CHANNEL_QTY

    signal.append(make_signal_values())
    assert bool(signal.buffer) == True

    assert signal.get_last() == signal.buffer[0]
    assert signal.get_avg_last_10() is None
    assert signal.get_avg_last_100() is None
    assert signal.get_avg_all() == signal.buffer[0]

    for _ in range(9):
        signal.append(make_signal_values())
    assert signal.get_last() == signal.buffer[-1]
    avg_last_10 = signal.get_avg_last_10()
    assert avg_last_10 is not None
    assert avg_last_10[0] == next(map(sum, zip(*signal.buffer))) // 10
    assert signal.get_avg_last_100() is None
    assert signal.get_avg_all() == list(
        map(lambda i: sum(i) // 10, zip(*signal.buffer))
    )

    for _ in range(90):
        signal.append(make_signal_values())
    avg_last_100 = signal.get_avg_last_100()
    assert avg_last_100 is not None
    assert avg_last_100[0] == next(map(sum, zip(*signal.buffer))) // 100

    for _ in range(10):
        signal.append(make_signal_values())
    avg_last_all = signal.get_avg_all()
    assert avg_last_all[0] == signal.total[0] // signal.total_qty


def test_wixel_session(make_wxl):
    _, wxl = make_wxl()
    wxl_session = structures.WixelSession(wxl)
    assert wxl_session.wxl is wxl
    assert isinstance(wxl_session.conn_time, float)
    assert isinstance(wxl_session.signal, structures.Signal)


def test_wixel_session_map(make_wxl):
    _, wxl = make_wxl()
    wxl_session_map = structures.WixelSessionMap()
    wxl_session_map.register(wxl)
    assert (wxl.serial_number in wxl_session_map) == True
    wxl_session = list(wxl_session_map.sessions)[0]
    assert isinstance(wxl_session, structures.WixelSession)
    wxl_session_map.remove(wxl)
    assert (wxl.serial_number in wxl_session_map) == False
