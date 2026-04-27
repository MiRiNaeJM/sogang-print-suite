"""Manager API 응답을 Client GUI가 다루기 쉬운 모델로 표현하는 모듈.

dict를 그대로 넘기지 않고 필드 이름을 고정해 GUI 코드가 응답 구조 변화에 덜 취약하게 한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class HealthResponse:
    """Manager /health 응답을 Client가 고정 필드로 다루기 위한 모델."""
    ok: bool
    message: str
    configured: bool


@dataclass
class ClientConfigResponse:
    """Client가 공지와 프로그램 정보를 갱신할 때 사용하는 설정 응답 모델."""
    ok: bool
    announcement: str
    managerVersion: str
    aboutContent: dict[str, Any] | None = None


@dataclass
class SearchResponse:
    """직원번호 조회 결과와 충전 가능 여부를 Client 화면에 전달하는 응답 모델."""
    ok: bool
    found: bool
    empId: str
    currentCredit: int
    refillAmount: int
    canRefill: bool
    serverLoginStatus: str
    canLogout: bool
    message: str
    reasonCode: str


@dataclass
class RefillResponse:
    """충전 처리 결과와 재조회 검증값을 Client 화면에 전달하는 응답 모델."""
    ok: bool
    empId: str
    beforeCredit: int
    refillAmount: int
    afterCredit: int
    logoutDone: bool
    serverLoginStatus: str
    canLogout: bool
    message: str
    reasonCode: str


@dataclass
class LogoutResponse:
    """프린터 서버 로그아웃 처리 결과를 Client 화면에 전달하는 응답 모델."""
    ok: bool
    empId: str
    serverLoginStatus: str
    canLogout: bool
    message: str
    reasonCode: str
