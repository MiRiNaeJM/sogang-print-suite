"""Client PC의 운영 컨텍스트를 수집하는 모듈.

Manager 로그에 어떤 PC에서 요청했는지 남기기 위해 PC 이름과 앱 버전을 함께 전달한다.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass


@dataclass
class ClientContext:
    """Client 요청을 Manager 로그에서 식별하기 위한 PC 정보 모델."""
    pc_name: str
    app_version: str


def build_client_context() -> ClientContext:
    """현재 PC 이름과 앱 버전을 Manager 요청에 포함할 컨텍스트로 만든다."""
    return ClientContext(
        pc_name=platform.node() or "UNKNOWN-PC",
        app_version="1.0.0",
    )
