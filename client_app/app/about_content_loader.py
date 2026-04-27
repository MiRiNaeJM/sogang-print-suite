"""Client 프로그램 정보 데이터를 기본값과 병합하는 모듈.

Client는 정보를 직접 저장하지 않고, 로컬 기본값이나 Manager가 내려준 aboutContent를 표시 가능한 형태로 정규화한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .about_content import DEFAULT_ABOUT_CONTENT
from .paths import ABOUT_CONTENT_PATH

ABOUT_CONTENT_KEYS = tuple(DEFAULT_ABOUT_CONTENT.keys())
"""외부 aboutContent에서 허용할 키 목록.

예상하지 못한 키가 화면 표시 구조를 흔들지 않도록 기본값에 정의된 항목만 받아들인다.
"""


def normalize_about_content(data: Mapping[str, Any] | None) -> dict[str, str]:
    """외부에서 받은 프로그램 정보 dict를 기본값과 병합해 표시 가능한 문자열 dict로 만든다."""
    content = dict(DEFAULT_ABOUT_CONTENT)
    if not isinstance(data, Mapping):
        return content

    for key in ABOUT_CONTENT_KEYS:
        value = data.get(key)
        if isinstance(value, str):
            content[key] = value.strip()
    return content


def load_about_content(path: Path = ABOUT_CONTENT_PATH) -> dict[str, str]:
    """Client 로컬 프로그램 정보 파일을 읽고 실패 시 기본값을 반환한다."""
    try:
        if not path.exists():
            return dict(DEFAULT_ABOUT_CONTENT)
        data = json.loads(path.read_text(encoding="utf-8"))
        return normalize_about_content(data)
    except Exception:
        return dict(DEFAULT_ABOUT_CONTENT)
