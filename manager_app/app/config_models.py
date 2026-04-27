"""Manager 설정과 로그 항목의 데이터 구조를 정의하는 모듈.

공개 설정과 WISDOM 비밀 설정을 분리해 저장 위치와 보안 처리를 다르게 적용한다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ManagerPublicConfig:
    """암호화 없이 저장해도 되는 Manager 운영 설정 모델."""
    manager_host: str = "0.0.0.0"
    manager_port: int = 8787
    announcement: str = ""
    admin_password_hash: str = ""


@dataclass
class ManagerSecrets:
    """암호화해 저장해야 하는 WISDOM 접속 정보 모델."""
    wisdom_base_url: str = ""
    wisdom_admin_id: str = ""
    wisdom_admin_pw: str = ""


@dataclass
class EffectiveManagerConfig:
    """공개 설정과 비밀 설정을 ManagerService에 한 번에 전달하기 위한 모델."""
    public: ManagerPublicConfig
    secrets: ManagerSecrets


@dataclass
class ManagerLogRecord:
    """GUI 로그 표에 한 줄로 표시할 운영 이벤트 모델."""
    timestamp: str
    pc_name: str
    emp_id: str
    action: str
    result: str
    reason: str
