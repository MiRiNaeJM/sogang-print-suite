"""Manager와 Client 프로그램 정보 JSON을 로드하고 저장하는 모듈.

관리자는 Manager 안에서 양쪽 정보를 편집하고, Client용 정보는 /client-config 응답으로 배포된다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .about_content import DEFAULT_ABOUT_CONTENT, DEFAULT_CLIENT_ABOUT_CONTENT
from .paths import CLIENT_ABOUT_CONTENT_PATH, MANAGER_ABOUT_CONTENT_PATH


def _normalize(data: Mapping[str, Any] | None, defaults: Mapping[str, str]) -> dict[str, str]:
    """프로그램 정보 dict에서 허용된 키만 골라 기본값과 병합한다."""
    content = dict(defaults)
    if not isinstance(data, Mapping):
        return content

    for key in defaults.keys():
        value = data.get(key)
        if isinstance(value, str):
            content[key] = value.strip()
    return content


def _load(path: Path, defaults: Mapping[str, str]) -> dict[str, str]:
    """지정된 프로그램 정보 JSON 파일을 읽고 유효하지 않으면 기본값으로 대체한다."""
    try:
        if not path.exists():
            return dict(defaults)
        data = json.loads(path.read_text(encoding="utf-8"))
        return _normalize(data, defaults)
    except Exception:
        return dict(defaults)


def load_manager_about_content() -> dict[str, str]:
    """Manager 정보 창에 표시할 프로그램 정보 JSON을 읽는다."""
    return _load(MANAGER_ABOUT_CONTENT_PATH, DEFAULT_ABOUT_CONTENT)


def load_client_about_content() -> dict[str, str]:
    """Client에 배포할 프로그램 정보 JSON을 읽는다."""
    return _load(CLIENT_ABOUT_CONTENT_PATH, DEFAULT_CLIENT_ABOUT_CONTENT)


def save_manager_about_content(content: Mapping[str, Any]) -> None:
    """관리자가 편집한 Manager 프로그램 정보를 JSON 파일에 저장한다."""
    MANAGER_ABOUT_CONTENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    normalized = _normalize(content, DEFAULT_ABOUT_CONTENT)
    MANAGER_ABOUT_CONTENT_PATH.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def save_client_about_content(content: Mapping[str, Any]) -> None:
    """관리자가 편집한 Client 프로그램 정보를 JSON 파일에 저장한다."""
    CLIENT_ABOUT_CONTENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    normalized = _normalize(content, DEFAULT_CLIENT_ABOUT_CONTENT)
    CLIENT_ABOUT_CONTENT_PATH.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
