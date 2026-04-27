"""Manager 공개 설정 JSON을 읽고 저장하는 모듈.

서버 host/port, 공지, 관리자 비밀번호 해시처럼 암호화가 필요 없는 값을 관리한다.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from .admin_auth import normalize_password_hash
from .config_models import ManagerPublicConfig
from .paths import PUBLIC_CONFIG_PATH


class PublicConfigStore:
    """Manager 공개 설정 JSON을 기본값 보완과 함께 읽고 저장한다."""
    def load(self) -> ManagerPublicConfig:
        """설정 파일을 읽고 누락된 값은 기본값으로 보완한다."""
        if not PUBLIC_CONFIG_PATH.exists():
            config = ManagerPublicConfig()
            self.save(config)
            return config
        data = json.loads(PUBLIC_CONFIG_PATH.read_text(encoding="utf-8"))
        data["admin_password_hash"] = normalize_password_hash(data.get("admin_password_hash"))
        return ManagerPublicConfig(
            manager_host=data.get("manager_host", "0.0.0.0"),
            manager_port=int(data.get("manager_port", 8787)),
            announcement=data.get("announcement", ""),
            admin_password_hash=data.get("admin_password_hash", ""),
        )

    def save(self, config: ManagerPublicConfig) -> None:
        """현재 설정 값을 JSON 또는 암호화 파일로 저장한다."""
        PUBLIC_CONFIG_PATH.write_text(
            json.dumps(asdict(config), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
