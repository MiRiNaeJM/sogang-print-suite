"""Client 설치 설정을 읽는 모듈.

Client는 설정을 저장하지 않고, 설치 시 생성된 manager_base_url만 읽어 Manager 접속 위치를 결정한다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .paths import CLIENT_CONFIG_PATH


DEFAULT_MANAGER_BASE_URL = ""
"""설치 설정이 없을 때 사용하는 빈 Manager 주소.

Client에서 주소를 임의 저장하지 않기 때문에 값이 비어 있으면 사용자에게 설정 누락으로 안내한다.
"""


@dataclass
class ClientConfig:
    """Client가 접속할 Manager 주소를 담는 설치 설정 모델."""
    manager_base_url: str = DEFAULT_MANAGER_BASE_URL


class ClientConfigStore:
    """Client 설정 파일을 읽어 GUI 시작 시 Manager 접속 위치를 제공한다."""
    def load(self) -> ClientConfig:
        """설정 파일을 읽고 누락된 값은 기본값으로 보완한다."""
        if not CLIENT_CONFIG_PATH.exists():
            return ClientConfig()
        data = json.loads(CLIENT_CONFIG_PATH.read_text(encoding="utf-8"))
        return ClientConfig(
            manager_base_url=data.get("manager_base_url", DEFAULT_MANAGER_BASE_URL),
        )
