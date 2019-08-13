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
    routes = [
        ("/static/<filename:path>", handlers.static),
        ("/", handlers.index),
        ("/stream/signal", handlers.stream_signal(wxl_session_map)),
        ("/stream/wxl_sessions", handlers.stream_sessions(wxl_session_map)),
        ("/stream/logging", handlers.stream_logging(log_buffer)),
    ]
    for path, callback in routes:
        app.route(path=path, callback=callback)

    return app
