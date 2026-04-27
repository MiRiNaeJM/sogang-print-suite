"""Manager 설정 파일과 프로그램 정보 파일의 저장 경로를 계산하는 모듈.

관리자 PC 전체에서 공유되는 운영 설정을 ProgramData 아래에 모아 둔다.
"""

from __future__ import annotations

from pathlib import Path
import os

APP_NAME = "SOGANG Print Manager"
"""ProgramData 아래 설정 폴더 이름으로 사용하는 Manager 앱 이름."""


def get_app_data_dir() -> Path:
    """설정 파일을 저장할 앱 전용 데이터 디렉터리를 만들고 반환한다."""
    root = Path(os.environ.get("PROGRAMDATA", str(Path.home() / "AppData" / "Local")))
    path = root / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


APP_DATA_DIR = get_app_data_dir()
PUBLIC_CONFIG_PATH = APP_DATA_DIR / "manager_public_config.json"
SECRETS_PATH = APP_DATA_DIR / "manager_secrets.enc.json"
CLIENT_ABOUT_CONTENT_PATH = APP_DATA_DIR / "client_about_content.json"
MANAGER_ABOUT_CONTENT_PATH = APP_DATA_DIR / "manager_about_content.json"
