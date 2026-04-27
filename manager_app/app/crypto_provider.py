"""Manager 비밀 설정을 암호화하고 복호화하는 모듈.

WISDOM 계정 정보가 평문 JSON으로 남지 않도록 DPAPI와 AES-GCM을 조합해 저장한다.
"""

from __future__ import annotations

import base64
import json
import os
import platform
from typing import Any, Dict

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    import win32crypt  # type: ignore
except Exception:  # pragma: no cover
    win32crypt = None


class CryptoProvider:
    """DPAPI로 AES 키를 감싸고 AES-GCM으로 secrets JSON을 암호화한다.

    설치된 Windows PC에서는 같은 장비의 Manager 프로세스가 복호화할 수 있게 하고,
    비 Windows 개발 환경에서는 테스트 흐름을 유지하기 위한 fallback만 제공한다.
    """

    CRYPTPROTECT_LOCAL_MACHINE = 0x4

    def _wrap_key(self, raw_key: bytes) -> bytes:
        """AES 키를 Windows DPAPI 또는 개발용 fallback 방식으로 감싼다."""
        if platform.system() == "Windows" and win32crypt is not None:
            return win32crypt.CryptProtectData(raw_key, None, None, None, None, self.CRYPTPROTECT_LOCAL_MACHINE)
        # 개발 환경에서만 사용하는 단순 fallback이며 운영 보안 용도로 쓰지 않는다.
        marker = os.environ.get("WINDOWS_PRINT_SUITE_DEV_WRAP_KEY", "dev-wrap-key").encode("utf-8")
        return bytes(b ^ marker[i % len(marker)] for i, b in enumerate(raw_key))

    def _unwrap_key(self, wrapped: bytes) -> bytes:
        """저장된 wrapped key를 복호화해 AES 키를 복원한다."""
        if platform.system() == "Windows" and win32crypt is not None:
            return win32crypt.CryptUnprotectData(wrapped, None, None, None, 0)[1]
        marker = os.environ.get("WINDOWS_PRINT_SUITE_DEV_WRAP_KEY", "dev-wrap-key").encode("utf-8")
        return bytes(b ^ marker[i % len(marker)] for i, b in enumerate(wrapped))

    def encrypt_json(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """비밀 설정 dict를 AES-GCM으로 암호화해 JSON 저장 가능한 dict로 만든다."""
        raw_key = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(12)
        aes = AESGCM(raw_key)
        plaintext = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        ciphertext = aes.encrypt(nonce, plaintext, None)
        wrapped_key = self._wrap_key(raw_key)
        return {
            "scheme": "dpapi-machine-aesgcm",
            "wrapped_key_b64": base64.b64encode(wrapped_key).decode("ascii"),
            "nonce_b64": base64.b64encode(nonce).decode("ascii"),
            "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
        }

    def decrypt_json(self, payload: Dict[str, str]) -> Dict[str, Any]:
        """암호화된 비밀 설정 dict를 복호화해 원래 JSON dict로 되돌린다."""
        wrapped_key = base64.b64decode(payload["wrapped_key_b64"])
        nonce = base64.b64decode(payload["nonce_b64"])
        ciphertext = base64.b64decode(payload["ciphertext_b64"])
        raw_key = self._unwrap_key(wrapped_key)
        aes = AESGCM(raw_key)
        plaintext = aes.decrypt(nonce, ciphertext, None)
        return json.loads(plaintext.decode("utf-8"))
