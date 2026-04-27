"""Client 설정 및 리소스 경로를 계산하는 모듈.

설치 환경과 개발 환경에서 같은 코드가 AppData와 로컬 asset 경로를 찾도록 한다.
"""

from __future__ import annotations

from pathlib import Path
import os

APP_NAME = "SOGANG Print Client"


def get_app_data_dir() -> Path:
    """설정 파일을 저장할 앱 전용 데이터 디렉터리를 만들고 반환한다."""
    root = Path(os.environ.get("PROGRAMDATA", str(Path.home() / "AppData" / "Local")))
    path = root / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


APP_DATA_DIR = get_app_data_dir()
CLIENT_CONFIG_PATH = APP_DATA_DIR / "client_config.json"

ABOUT_CONTENT_PATH = APP_DATA_DIR / "about_content.json"
