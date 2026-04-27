"""Windows 트레이 아이콘과 알림을 관리하는 모듈.

창을 닫아도 Manager가 계속 실행될 수 있게 하고, 종료 요청은 GUI와 같은 콜백으로 연결한다.
"""

from __future__ import annotations

from typing import Callable

try:
    import pystray  # type: ignore
    from pystray import MenuItem as Item  # type: ignore
    from PIL import Image, ImageDraw  # type: ignore
except Exception:  # pragma: no cover
    pystray = None
    Item = None
    Image = None
    ImageDraw = None


class TrayRuntime:
    """트레이 아이콘, 복원, 종료, 알림 기능을 GUI와 분리해 관리한다."""
    def __init__(
        self,
        show_callback: Callable[[], None],
        toggle_server_callback: Callable[[], None],
        status_callback: Callable[[], None],
        exit_callback: Callable[[], None],
        is_server_running: Callable[[], bool],
    ) -> None:
        """객체가 사용할 상태와 UI 구성 요소를 초기화한다."""
        self._show_callback = show_callback
        self._toggle_server_callback = toggle_server_callback
        self._status_callback = status_callback
        self._exit_callback = exit_callback
        self._is_server_running = is_server_running
        self._icon = None
        self.available = pystray is not None and Item is not None and Image is not None and ImageDraw is not None

    def _create_image(self):
        """트레이 아이콘에 사용할 이미지를 파일 또는 기본 도형으로 만든다."""
        image = Image.new("RGBA", (64, 64), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((8, 8, 56, 56), radius=12, fill=(40, 110, 210, 255))
        draw.rectangle((18, 18, 46, 46), outline=(255, 255, 255, 255), width=3)
        draw.line((22, 28, 42, 28), fill=(255, 255, 255, 255), width=3)
        draw.line((22, 36, 42, 36), fill=(255, 255, 255, 255), width=3)
        return image

    def _build_menu(self):
        """트레이 아이콘의 복원/종료 메뉴를 구성한다."""
        toggle_text = "서버 종료 / Stop server" if self._is_server_running() else "서버 시작 / Start server"
        return pystray.Menu(
            Item("창 열기 / Open", lambda *args: self._show_callback()),
            Item(toggle_text, lambda *args: self._toggle_server_callback()),
            Item("상태 보기 / Status", lambda *args: self._status_callback()),
            Item("종료 / Exit", lambda *args: self._exit_callback()),
        )

    def start(self) -> bool:
        """서버가 실행 중이 아니면 백그라운드 스레드로 시작한다."""
        if not self.available:
            return False
        if self._icon is not None:
            return True
        self._icon = pystray.Icon("sogang_print_manager", self._create_image(), "SOGANG Print Manager", self._build_menu())
        try:
            self._icon.run_detached()
            return True
        except Exception:
            self._icon = None
            return False

    def refresh(self) -> None:
        """트레이 아이콘의 표시 이름과 메뉴를 최신 상태로 갱신한다."""
        if not self._icon:
            return
        try:
            self._icon.menu = self._build_menu()
            self._icon.update_menu()
        except Exception:
            pass

    def notify(self, title: str, message: str) -> None:
        """운영 이벤트를 Windows 트레이 알림으로 표시한다."""
        if not self._icon:
            return
        try:
            self._icon.notify(message, title)
        except Exception:
            pass

    def stop(self) -> None:
        """실행 중인 서버를 종료하고 스레드 상태를 정리한다."""
        if not self._icon:
            return
        try:
            self._icon.stop()
        finally:
            self._icon = None
