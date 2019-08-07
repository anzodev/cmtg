import os

import bottle

from cmtg import structures
from cmtg.web import handlers


PATH_ROOT = os.path.dirname(__file__)
PATH_VIEWS = os.path.join(PATH_ROOT, "views")
PATH_STATIC = os.path.join(PATH_ROOT, "static")


def create_app(
    wxl_session_map: structures.WixelSessionMap,
    log_buffer: structures.LogBuffer,
) -> bottle.Bottle:
    bottle.TEMPLATE_PATH.insert(0, PATH_VIEWS)

    app = bottle.Bottle()

    app.route(path="/static/<filename:path>", callback=handlers.static)
    app.route(path="/", callback=handlers.index)
    app.route(
        path="/stream/signal", callback=handlers.stream_signal(wxl_session_map)
    )
    app.route(
        path="/stream/wxl_sessions",
        callback=handlers.stream_wixel_sessions(wxl_session_map),
    )
    app.route(
        path="/stream/logging", callback=handlers.stream_logging(log_buffer)
    )

    return app
