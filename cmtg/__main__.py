import gevent
from gevent import monkey

monkey.patch_all()

import argparse
import ipaddress
import logging
import logging.handlers
import signal
from traceback import format_exc

from cmtg import structures, utils, web, wixel_utils, workers


parser = argparse.ArgumentParser(
    prog="cmtg",
    description="Pololu Wixel Spectrum Analysis (monitoring system).",
)
parser.add_argument(
    "--log",
    metavar="string",
    type=str,
    default="INFO",
    choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    help="system logs level",
)
parser.add_argument(
    "--host",
    metavar="string",
    type=ipaddress.IPv4Address,
    default="0.0.0.0",
    help="web service host",
)
parser.add_argument(
    "--port", metavar="int", type=int, default=5000, help="web service port"
)
parser.add_argument(
    "--wxls",
    metavar="int",
    type=int,
    default=0,
    help="quantity of emulated Pololu Wixel connections",
)
args = parser.parse_args()

log_level = args.log
host = args.host
port = args.port
mock_wxls = args.wxls


if mock_wxls > 0:
    wixel_utils.patch_search_connected(mock_wxls)


logger = logging.getLogger("cmtg")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s [%(process)d:%(thread)d][%(levelname)s] %(threadName)s "
    "- %(message)s"
)

log_stream_handler = logging.StreamHandler()
log_stream_handler.setFormatter(formatter)
log_stream_handler.setLevel(getattr(logging, log_level))

log_buffer_handler = utils.ExtBufferingHandler(100)
log_buffer_handler.setFormatter(formatter)
log_buffer_handler.setLevel(getattr(logging, log_level))

logger.addHandler(log_stream_handler)
logger.addHandler(log_buffer_handler)


wxl_session_map = structures.WixelSessionMap()
log_buffer = structures.LogBuffer(log_buffer_handler)

wsm = workers.WixelSessionMonitor(wxl_session_map)
wsm.daemon = True
scm = workers.SignalCollectorMonitor(wxl_session_map)
scm.daemon = True
lbu = workers.LogBufferUpdater(log_buffer)
lbu.daemon = True
web_app = web.create_app(wxl_session_map, log_buffer)


def app_exit(*args):
    global wsm, scm, lbu
    wsm.terminate()
    scm.terminate()
    lbu.terminate()
    wsm.join()
    scm.join()
    lbu.join()
    exit()


gevent.signal(signal.SIGTERM, app_exit)
gevent.signal(signal.SIGINT, app_exit)


try:
    logger.info("WixelSessionMonitor start;")
    logger.info("SignalCollectorMonitor start;")
    logger.info(f"Web service start, listening on http://{host}:{port}/")

    wsm.start()
    scm.start()
    lbu.start()
    web_app.run(host=str(host), port=port, server="gevent", quiet=True)

except Exception:
    logger.critical(
        f"unexpected error occured ({repr(format_exc())}), service exit;"
    )

app_exit()
