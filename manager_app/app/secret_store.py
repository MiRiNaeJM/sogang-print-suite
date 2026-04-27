"""Manager의 WISDOM 비밀 설정을 암호화 파일로 저장하는 모듈.

계정 정보와 관리자 비밀번호 같은 민감한 값을 공개 설정과 분리해 관리한다.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from .paths import SECRETS_PATH
from .config_models import ManagerSecrets
from .crypto_provider import CryptoProvider


class SecretStore:
    """WISDOM 비밀 설정을 암호화 Provider를 통해 읽고 저장한다."""
    def __init__(self) -> None:
        """객체가 사용할 상태와 UI 구성 요소를 초기화한다."""
        self.crypto = CryptoProvider()

    def load(self) -> ManagerSecrets:
        """설정 파일을 읽고 누락된 값은 기본값으로 보완한다."""
        if not SECRETS_PATH.exists():
            return ManagerSecrets()
        data = json.loads(SECRETS_PATH.read_text(encoding="utf-8"))
        secret_dict = self.crypto.decrypt_json(data)
        return ManagerSecrets(**secret_dict)

    def save(self, secrets: ManagerSecrets) -> None:
        """현재 설정 값을 JSON 또는 암호화 파일로 저장한다."""
        encrypted = self.crypto.encrypt_json(asdict(secrets))
        SECRETS_PATH.write_text(
            json.dumps(encrypted, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
