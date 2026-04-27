"""관리자 비밀번호 해시를 명령행에서 생성하는 도구.

설치 전 또는 배포 준비 시 Manager와 같은 해시 함수를 사용해 초기 비밀번호 값을 만들 수 있다.
"""

from __future__ import annotations

from getpass import getpass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "manager_app"))

from app.admin_auth import hash_password  # noqa: E402


def main() -> int:
    """명령행 인자를 처리하고 도구의 핵심 작업을 실행한다."""
    password = getpass("Password: ")
    confirm = getpass("Confirm: ")
    if password != confirm:
        print("Passwords do not match.", file=sys.stderr)
        return 1
    print(hash_password(password))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
