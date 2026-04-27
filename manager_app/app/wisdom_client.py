"""WISDOM 웹 시스템과 HTTP로 통신하는 클라이언트 모듈.

로그인, 사용자 검색, 매수 증가, 서버 로그아웃 요청을 ManagerService가 호출할 수 있게 캡슐화한다.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

from .config_models import ManagerSecrets
from .parser_utils import SearchResult, is_login_page, parse_search_result


class WisdomClientError(Exception):
    """WISDOM 통신 계층에서 발생한 일반 오류를 나타내는 예외."""
    pass


class WisdomAuthError(WisdomClientError):
    """WISDOM 로그인 또는 인증 상태가 올바르지 않을 때 사용하는 예외."""
    pass


@dataclass
class RequestResult:
    """WISDOM 요청의 HTML과 파싱 결과를 함께 전달하기 위한 모델."""
    success: bool
    message: str
    html: str
    search_result: SearchResult | None = None


class WisdomClient:
    """WISDOM 웹 요청을 하나의 requests 세션으로 수행하는 클라이언트.

    ManagerService가 요청 단위로 이 객체를 만들기 때문에 각 검색/충전/로그아웃 흐름은
    독립된 로그인 세션에서 실행된다.
    """
    def __init__(self, secrets: ManagerSecrets, timeout_seconds: int = 15) -> None:
        """객체가 사용할 상태와 UI 구성 요소를 초기화한다."""
        self.secrets = secrets
        self.timeout_seconds = timeout_seconds
        self.base_url = (self.secrets.wisdom_base_url or "").strip().rstrip("/")
        self.admin_id = (self.secrets.wisdom_admin_id or "").strip()
        self.admin_pw = self.secrets.wisdom_admin_pw or ""
        self.session = requests.Session()
        if self.base_url:
            referer = f"{self.base_url}/login.do"
        else:
            referer = ""
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/135.0.0.0 Safari/537.36"
                ),
                "Referer": referer,
            }
        )

    def _ensure_configured(self) -> None:
        """WISDOM 요청에 필요한 base_url과 관리자 계정 정보가 있는지 확인한다."""
        missing = []
        if not self.base_url:
            missing.append("WISDOM Base URL")
        if not self.admin_id:
            missing.append("WISDOM Admin ID")
        if not self.admin_pw:
            missing.append("WISDOM Admin PW")
        if missing:
            raise ValueError("다음 설정값이 비어 있습니다: " + ", ".join(missing))

    def _url(self, path: str) -> str:
        """WISDOM 상대 경로를 base_url과 결합해 전체 URL로 만든다."""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """WISDOM HTTP 요청을 보내고 인증 만료 여부를 공통으로 검사한다."""
        self._ensure_configured()
        response = self.session.request(
            method=method,
            url=self._url(path),
            timeout=self.timeout_seconds,
            allow_redirects=True,
            **kwargs,
        )
        response.raise_for_status()
        return response

    def login(self) -> None:
        """WISDOM 관리자 계정으로 로그인한다."""
        payload = {"empid": self.admin_id, "password": self.admin_pw, "x": "0", "y": "0"}
        self._request("POST", "/login.do", data=payload)
        check = self._request("GET", "/creditInfo.do")
        if is_login_page(check.text):
            raise WisdomAuthError("로그인에 실패했거나 세션이 생성되지 않았습니다.")

    def search_user(self, emp_id: str, retry_on_auth: bool = True) -> SearchResult:
        """WISDOM에서 직원번호를 검색하고 HTML 결과를 파싱한다."""
        payload = {"searchParameter": "2", "searchParameterValue": emp_id, "isSearch": "Y"}
        response = self._request("POST", "/creditInfo.do", data=payload)
        if is_login_page(response.text):
            if retry_on_auth:
                self.login()
                return self.search_user(emp_id, False)
            raise WisdomAuthError("조회 중 세션이 만료되었습니다.")
        return parse_search_result(response.text, emp_id)

    def increase_credit(self, emp_id: str, amount: int, retry_on_auth: bool = True) -> RequestResult:
        """WISDOM에 현재 매수 증가 요청을 보낸다."""
        if amount <= 0:
            raise ValueError("증가 수량은 1 이상이어야 합니다.")
        payload = {
            "actionFlag": "setIncrease",
            "maxCredit": "50000",
            "searchParameter": "2",
            "searchParameterValue": emp_id,
            "userIdPara": emp_id,
            "creditPara": str(amount),
            "typePara": "CASH",
            "checkedUserId": emp_id,
            f"{emp_id}_type": "CASH",
            f"{emp_id}_increaseCredit": str(amount),
        }
        response = self._request("POST", "/creditInfo.do", data=payload)
        if is_login_page(response.text):
            if retry_on_auth:
                self.login()
                return self.increase_credit(emp_id, amount, False)
            raise WisdomAuthError("추가 처리 중 세션이 만료되었습니다.")
        return RequestResult(True, "추가 요청이 전송되었습니다. 재조회로 반영 여부를 확인하세요.", response.text)

    def logout_user(self, emp_id: str, retry_on_auth: bool = True) -> RequestResult:
        """직원번호의 프린터 서버 로그아웃 요청을 Manager에 전달한다."""
        response = self._request("POST", f"/iwsLogout.do?userId={emp_id}")
        if is_login_page(response.text):
            if retry_on_auth:
                self.login()
                return self.logout_user(emp_id, False)
            raise WisdomAuthError("로그아웃 처리 중 세션이 만료되었습니다.")

        parsed = parse_search_result(response.text, emp_id)
        if not parsed.found:
            try:
                parsed = self.search_user(emp_id, retry_on_auth=False)
            except Exception:
                parsed = parse_search_result(response.text, emp_id)

        return RequestResult(True, "서버 로그아웃 요청이 전송되었습니다.", response.text, parsed)

    def close(self) -> None:
        """requests 세션을 닫아 네트워크 리소스를 정리한다."""
        self.session.close()
