from __future__ import annotations

import contextlib
import threading
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


@dataclass
class StaticServer:
    server: ThreadingHTTPServer
    thread: threading.Thread
    url: str

    def close(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        with contextlib.suppress(Exception):
            self.server.server_close()


def create_static_server(root_dir: str | Path, *, port: int = 0) -> StaticServer:
    root = Path(root_dir).resolve()
    handler = partial(QuietStaticHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    actual_port = server.server_address[1]
    return StaticServer(
        server=server,
        thread=thread,
        url=f"http://127.0.0.1:{actual_port}",
    )
