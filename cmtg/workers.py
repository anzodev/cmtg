import errno
import logging
import threading
from typing import Optional

import serial as pyserial

from cmtg import structures, wixel


def log_worker_run(f) -> None:
    logger = logging.getLogger("cmtg")

    def wrapper(self, *args, **kwargs):
        logger.debug("the worker is started;")
        f(self, logger, *args, **kwargs)
        logger.debug("the worker is terminated;")

    return wrapper


class TerminatedThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event_term = threading.Event()

    @property
    def is_terminated(self) -> bool:
        return self._event_term.is_set()

    def terminate(self) -> None:
        self._event_term.set()

    def wait_term(self, timeout: Optional[float] = None):
        self._event_term.wait(timeout)


class SignalCollector(TerminatedThread):
    def __init__(self, wxl: wixel.Wixel, signal: structures.Signal):
        super().__init__(
            name=f'{self.__class__.__name__}("{wxl.serial_number}")'
        )
        self.wxl = wxl
        self.signal = signal

    @log_worker_run
    def run(self, logger: logging.Logger):
        while not self.is_terminated:
            try:
                if not self.wxl.serial.is_open:
                    self.wxl.serial.open()
            except OSError as e:
                if e.errno == errno.EBUSY:
                    logger.warning(
                        "Wixel serial is busy, please wait; new try after 4s;"
                    )
                    self.wait_term(4.0)
                    continue
                else:
                    logger.error(f'serial open error ("{str(e)}");')
                    return
            except Exception as e:
                logger.error(f'serial open error ("{str(e)}");')
                return
            else:
                break

        try:
            with self.wxl.serial:
                while not self.is_terminated:
                    try:
                        signal_values = self.wxl.get_signal_values()
                    except (pyserial.SerialException, IOError) as e:
                        logger.error(f'serial read error ("{str(e)}");')
                        break

                    if not signal_values:
                        logger.warning(f"the package is corrupted;")
                        continue
                    self.signal.append(signal_values)
        except Exception as e:
            logger.error(f'serial error ("{str(e)}");')


class SignalCollectorMonitor(TerminatedThread):
    def __init__(self, wxl_session_map: structures.WixelSessionMap):
        super().__init__(name=self.__class__.__name__)
        self.wxl_session_map = wxl_session_map
        self.collector_map = {}

    @log_worker_run
    def run(self, logger: logging.Logger):
        while not self.is_terminated:
            serial_numbers = list(self.collector_map.keys())
            for serial_number in serial_numbers:
                if serial_number not in self.wxl_session_map:
                    collector = self.collector_map[serial_number]
                    collector.terminate()
                    collector.join()
                    self.collector_map.pop(serial_number, None)
                    logger.debug(
                        f'the signal collector ("{serial_number}") '
                        "is removed;"
                    )

            for wxl_session in self.wxl_session_map.sessions:
                wxl = wxl_session.wxl
                signal = wxl_session.signal
                collector = self.collector_map.get(wxl.serial_number)
                if not collector or not collector.is_alive():
                    collector = SignalCollector(wxl, signal)
                    collector.start()
                    self.collector_map[wxl.serial_number] = collector
                    logger.debug(
                        f'new signal collector ("{wxl.serial_number}") '
                        "is started;"
                    )
                    continue

            self.wait_term(1.0)

        for collector in self.collector_map.values():
            if collector.is_alive():
                collector.terminate()
                collector.join()
                logger.debug(
                    f'the signal collector ("{collector.wxl.serial_number}") '
                    "is terminated;"
                )
            else:
                logger.debug(
                    f'the signal collector ("{collector.wxl.serial_number}") '
                    "is terminated already;"
                )


class WixelSessionMonitor(TerminatedThread):
    def __init__(self, wxl_session_map: structures.WixelSessionMap):
        super().__init__(name=self.__class__.__name__)
        self.wxl_session_map = wxl_session_map
        self.conn_sto = wixel.ConnectionStorage()

    @log_worker_run
    def run(self, logger: logging.Logger):
        while not self.is_terminated:
            connected = wixel.search_connected()
            new_conn, disconn = self.conn_sto.update(connected)

            for wxl in new_conn:
                self.wxl_session_map.register(wxl)
                logger.info(
                    f'new Wixel ("{wxl.serial_number}") session is '
                    "registrated;"
                )

            for wxl in disconn:
                self.wxl_session_map.remove(wxl)
                logger.info(
                    f'the Wixel ("{wxl.serial_number}") session is finished;'
                )

            self.wait_term(2.0)


class LogBufferUpdater(TerminatedThread):
    def __init__(self, log_buffer: structures.LogBuffer):
        super().__init__(name=self.__class__.__name__)
        self.log_buffer = log_buffer

    def run(self):
        while not self.is_terminated:
            self.log_buffer.update()
            self.wait_term(1.0)
