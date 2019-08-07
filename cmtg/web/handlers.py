import json
import platform
import re
import socket
import uuid

import bottle

from cmtg import structures, web
from cmtg.web import utils as web_utils


def static(filename: str):
    return bottle.static_file(filename, root=web.PATH_STATIC)


def index():
    hostname = socket.gethostname()
    addr_hw = ":".join(re.findall(r"[0-9a-f]{2}", hex(uuid.getnode())[2:]))
    system = " ".join([platform.system(), platform.release()])
    return bottle.template(
        "index.html", hostname=hostname, addr_hw=addr_hw, system=system
    )


def stream_wixel_sessions(wxl_session_map: structures.WixelSessionMap):
    @web_utils.sse_response()
    def _stream():
        while True:
            data = []
            for wxl_session in wxl_session_map.sessions:
                wxl = wxl_session.wxl
                stats = wxl_session.stats
                data.append(
                    {
                        "serial_number": wxl.serial_number,
                        "port": wxl.device,
                        "stats": {
                            "connected": web_utils.convert_time(
                                int(stats["connected"])
                            ),
                            "packages": stats["packages"],
                        },
                    }
                )
            yield json.dumps(data)

    return _stream


def stream_signal(wxl_session_map: structures.WixelSessionMap):
    @web_utils.sse_response()
    def _stream():
        while True:
            data = {}
            for wxl_session in wxl_session_map.sessions:
                wxl, signal = wxl_session.wxl, wxl_session.signal
                data[wxl.serial_number] = {
                    "last": signal.get_last(),
                    "avg_last_10": signal.get_avg_last_10(),
                    "avg_last_100": signal.get_avg_last_100(),
                    "avg_all": signal.get_avg_all(),
                }
            yield json.dumps(data)

    return _stream


def stream_logging(log_buffer: structures.LogBuffer):
    @web_utils.sse_response()
    def _stream():
        tick = None
        while True:
            logs = log_buffer.get_after(tick)
            tick = log_buffer.tick
            data = []
            for record in logs:
                data.append(log_buffer.handler.format(record))
            yield json.dumps(data)

    return _stream
