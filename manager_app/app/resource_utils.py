"""공용 리소스 파일을 안전하게 로드하는 유틸리티 모듈.

Manager와 Client는 루트 assets/app_icon.ico 하나를 공유한다.
개발 환경과 PyInstaller 실행 환경의 기준 경로가 다르므로 이 모듈에서 실제 리소스 경로를 통일한다.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tkinter as tk

from PIL import Image, ImageTk


APP_ICON = Path("assets") / "app_icon.ico"


def resource_path(relative_path: str | Path) -> Path:
    """개발 환경과 PyInstaller 실행 환경에서 리소스 파일의 실제 경로를 반환한다."""

    if getattr(sys, "frozen", False):
        base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    else:
        base_path = Path(__file__).resolve().parents[2]

    return base_path / relative_path


def _load_photo_image(path: str | Path, *, width: int | None = None, height: int | None = None) -> ImageTk.PhotoImage | None:
    """ICO 파일을 Tkinter 라벨에 표시 가능한 PhotoImage로 변환한다.

    tk.PhotoImage는 ICO를 안정적으로 처리하지 못하므로 Pillow로 열어 ImageTk.PhotoImage로 변환한다.
    """

    icon_path = resource_path(path)

    if not icon_path.exists():
        return None

    try:
        image = Image.open(icon_path)
        image.load()

        if width or height:
            target_width = width or image.width
            target_height = height or image.height
            image.thumbnail((target_width, target_height), Image.LANCZOS)

        return ImageTk.PhotoImage(image)
    except Exception:
        return None


def _set_window_icon(window: tk.Misc) -> ImageTk.PhotoImage | None:
    """공용 ICO 파일을 창 아이콘으로 적용하고 실패해도 앱 실행을 계속한다."""

    icon_path = resource_path(APP_ICON)

    if icon_path.exists():
        try:
            window.iconbitmap(str(icon_path))
            return None
        except tk.TclError:
            pass

    image = _load_photo_image(APP_ICON, width=64, height=64)
    if image is not None:
        try:
            window.iconphoto(True, image)
        except tk.TclError:
            pass

    return image