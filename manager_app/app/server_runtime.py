"""Manager 안에서 Flask/Waitress 서버를 백그라운드로 실행하는 모듈.

GUI가 멈추지 않도록 서버 수명 주기를 별도 스레드와 핸들로 관리한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock, Thread
from typing import Optional

try:
    from waitress.server import create_server  # type: ignore
except Exception:  # pragma: no cover
    create_server = None
from wsgiref.simple_server import make_server


@dataclass
class ServerHandle:
    """백그라운드 서버 스레드와 Waitress 서버 객체를 함께 보관한다."""
    thread: Thread
    server: object


class ServerRuntime:
    """GUI에서 서버 시작, 중지, 재시작을 안전하게 호출하기 위한 런타임."""
    def __init__(self, app_factory, host: str, port: int) -> None:
        """객체가 사용할 상태와 UI 구성 요소를 초기화한다."""
        self._app_factory = app_factory
        self._host = host
        self._port = port
        self._handle: Optional[ServerHandle] = None
        self._lock = Lock()

    def _build_server(self):
        """Waitress가 있으면 운영용 서버를 만들고 없으면 Flask 개발 서버로 대체한다."""
        app = self._app_factory()
        if create_server is not None:
            server = create_server(app, host=self._host, port=self._port)
            return server, server.run, getattr(server, "close", None)
        server = make_server(self._host, self._port, app)
        return server, server.serve_forever, getattr(server, "shutdown", None)

    def start(self) -> None:
        """서버가 실행 중이 아니면 백그라운드 스레드로 시작한다."""
        with self._lock:
            if self._handle is not None and self._handle.thread.is_alive():
                return
            server, run_callable, _ = self._build_server()

            def _run() -> None:
                """Flask 개발 서버 fallback을 별도 스레드에서 실행한다."""
                run_callable()

            thread = Thread(target=_run, daemon=True)
            thread.start()
            self._handle = ServerHandle(thread=thread, server=server)

    def stop(self, timeout: float = 3.0) -> None:
        """실행 중인 서버를 종료하고 스레드 상태를 정리한다."""
        with self._lock:
            handle = self._handle
            self._handle = None
        if handle is None:
            return
        server = handle.server
        close_fn = getattr(server, "close", None) or getattr(server, "shutdown", None)
        if callable(close_fn):
            try:
                close_fn()
            except Exception:
                pass
        handle.thread.join(timeout=timeout)

    def restart(self, host: str | None = None, port: int | None = None) -> None:
        """현재 바인딩 값으로 서버를 다시 시작한다."""
        if host is not None:
            self._host = host
        if port is not None:
            self._port = port
        self.stop()
        self.start()

    def update_binding(self, host: str, port: int) -> None:
        """다음 서버 시작에 사용할 host와 port를 갱신한다."""
        self._host = host
        self._port = port

    def is_running(self) -> bool:
        """서버 핸들이 살아 있는지 확인한다."""
        return self._handle is not None and self._handle.thread.is_alive()
