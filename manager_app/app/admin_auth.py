"""관리자 비밀번호 해시 생성과 검증을 담당하는 모듈.

평문 비밀번호를 설정 파일에 저장하지 않고 PBKDF2 해시만 비교하기 위해 사용한다.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

PBKDF2_ITERATIONS = 240_000


def hash_password(password: str) -> str:
    """관리자 비밀번호를 salt가 포함된 PBKDF2 해시 문자열로 변환한다."""
    if not password:
        raise ValueError("관리자 비밀번호는 비워둘 수 없습니다.")
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${iterations}${salt}${digest}".format(
        iterations=PBKDF2_ITERATIONS,
        salt=base64.b64encode(salt).decode("ascii"),
        digest=base64.b64encode(derived).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    """입력 비밀번호가 저장된 PBKDF2 해시와 일치하는지 확인한다."""
    if not encoded:
        return False
    try:
        algorithm, iterations_str, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
    except Exception:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def normalize_password_hash(existing_hash: str | None) -> str:
    """설정 파일에서 읽은 비밀번호 해시 문자열의 공백을 정리한다."""
    return existing_hash or ""
