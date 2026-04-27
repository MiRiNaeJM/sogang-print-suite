"""Client가 Manager 서버와 통신하기 위한 HTTP API 래퍼 모듈.

GUI 코드가 requests 예외와 JSON 구조를 직접 다루지 않도록 통신 세부사항을 숨긴다.
"""

from __future__ import annotations

from typing import Any, Dict
import requests

from .api_models import HealthResponse, ClientConfigResponse, SearchResponse, RefillResponse, LogoutResponse


class ManagerApi:
    """ManagerApi 관련 상태와 동작을 하나의 책임 단위로 묶는다."""
    def __init__(self, base_url: str, timeout_seconds: int = 8) -> None:
        """객체가 사용할 상태와 UI 구성 요소를 초기화한다."""
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _get_json(self, path: str) -> Dict[str, Any]:
        """Manager의 GET 응답을 JSON dict로 읽고 HTTP 오류를 예외로 올린다."""
        response = requests.get(f"{self.base_url}{path}", timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Manager의 POST 응답을 JSON dict로 읽고 HTTP 오류를 예외로 올린다."""
        response = requests.post(f"{self.base_url}{path}", json=payload, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def health(self) -> HealthResponse:
        """Manager 서버 실행 여부와 설정 완료 상태를 확인한다."""
        data = self._get_json("/health")
        return HealthResponse(**data)

    def get_client_config(self) -> ClientConfigResponse:
        """Client가 사용할 공지와 프로그램 정보를 반환한다."""
        data = self._get_json("/client-config")
        return ClientConfigResponse(**data)

    def search(self, emp_id: str, pc_name: str) -> SearchResponse:
        """직원번호 조회 요청을 Manager에 전달한다."""
        data = self._post_json("/search", {"empId": emp_id, "pcName": pc_name})
        return SearchResponse(**data)

    def refill(self, emp_id: str, pc_name: str) -> RefillResponse:
        """직원번호 충전 요청을 Manager에 전달한다."""
        data = self._post_json("/refill", {"empId": emp_id, "pcName": pc_name})
        return RefillResponse(**data)

    def logout_user(self, emp_id: str, pc_name: str) -> LogoutResponse:
        """직원번호의 프린터 서버 로그아웃 요청을 Manager에 전달한다."""
        data = self._post_json("/logout-user", {"empId": emp_id, "pcName": pc_name})
        return LogoutResponse(**data)
