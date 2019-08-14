import os
import time

from cmtg import structures, wixel, workers


def test_terminated_thread():
    class TestTerminatedThread(workers.TerminatedThread):
        def run(self):
            self.check_var = None
            self.wait_term()

    thread = TestTerminatedThread()
    assert thread.is_terminated == False
    thread.start()
    assert thread.is_alive() == True
    thread.terminate()
    thread.join()
    assert thread.is_alive() == False
    assert thread.is_terminated == True
    assert hasattr(thread, "check_var")


def test_signal_collector(make_wxl, make_signal_values_and_package):
    master, wxl = make_wxl()
    signal = structures.Signal()
    signal_values, package = make_signal_values_and_package()
    sc = workers.SignalCollector(wxl, signal)
    sc.start()
    time.sleep(0.4)
    os.write(master, package)
    sc.terminate()
    sc.join()
    assert wxl.serial.is_open == False
    assert bool(signal.buffer) == True


def test_wixel_session_monitor(monkeypatch, make_wxl):
    wxls_pool = [make_wxl()[1] for _ in range(3)]

    def mock_search_connected():
        return wxls_pool

    monkeypatch.setattr(wixel, "search_connected", mock_search_connected)

    wxl_session_map = structures.WixelSessionMap()
    wsm = workers.WixelSessionMonitor(wxl_session_map)
    wsm.start()

    time.sleep(0.2)

    assert len(wxl_session_map) == 3
    assert set(ws.wxl.serial_number for ws in wxl_session_map.sessions) == set(
        wxl.serial_number for wxl in wxls_pool
    )

    wxls_pool = wxls_pool[:2]
    time.sleep(2)

    wsm.terminate()
    wsm.join()

    assert len(wxl_session_map) == 2
    assert set(ws.wxl.serial_number for ws in wxl_session_map.sessions) == set(
        wxl.serial_number for wxl in wxls_pool[:2]
    )


def test_signal_collector_monitor(monkeypatch, make_wxl):
    wxls_pool = [make_wxl()[1] for _ in range(3)]

    def mock_search_connected():
        return wxls_pool

    monkeypatch.setattr(wixel, "search_connected", mock_search_connected)

    wxl_session_map = structures.WixelSessionMap()
    wsm = workers.WixelSessionMonitor(wxl_session_map)
    scm = workers.SignalCollectorMonitor(wxl_session_map)
    wsm.start()
    scm.start()

    time.sleep(1.1)

    assert len(scm.collector_map) == 3
    assert all(map(lambda c: c.is_alive(), scm.collector_map.values())) == True

    wxls_pool = wxls_pool[:2]
    time.sleep(2.1)

    wsm.terminate()
    scm.terminate()
    wsm.join()
    scm.join()

    assert len(scm.collector_map) == 2
