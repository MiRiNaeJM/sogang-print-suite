"""Manager 리소스 파일을 안전하게 로드하는 유틸리티 모듈.

PyInstaller 실행 환경과 개발 환경 모두에서 아이콘 파일을 찾고, 실패해도 Manager 실행을 막지 않는다.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk


ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
APP_ICON_PNG = ASSETS_DIR / "app_icon.png"
APP_ICON_ICO = ASSETS_DIR / "app_icon.ico"


def _load_photo_image(path: Path, *, width: int | None = None, height: int | None = None) -> tk.PhotoImage | None:
    """아이콘 이미지를 Tkinter PhotoImage로 읽되 실패하면 None을 반환한다."""
    if not path.exists():
        return None

    try:
        image = tk.PhotoImage(file=str(path))
    except tk.TclError:
        return None

    if width and image.width() > width:
        image = image.subsample(max(1, image.width() // width))
    if height and image.height() > height:
        image = image.subsample(max(1, image.height() // height))

    return image


def _set_window_icon(window: tk.Misc) -> tk.PhotoImage | None:
    """창 아이콘을 설정하고 실패해도 앱 실행을 계속한다."""
    if APP_ICON_ICO.exists():
        try:
            window.iconbitmap(str(APP_ICON_ICO))
            return None
        except tk.TclError:
            pass

    image = _load_photo_image(APP_ICON_PNG, width=64, height=64)
    if image is not None:
        try:
            window.iconphoto(True, image)
        except tk.TclError:
            pass
    return image
