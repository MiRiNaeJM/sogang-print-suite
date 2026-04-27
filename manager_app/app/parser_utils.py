"""WISDOM HTML 응답을 검색 결과 객체로 변환하는 파서 모듈.

외부 웹 화면 구조에서 직원번호, 잔여 매수, 서버 로그인 상태를 추출한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from bs4 import BeautifulSoup


@dataclass
class SearchResult:
    """WISDOM HTML 파싱 결과를 업무 로직이 사용하기 쉬운 형태로 담는다."""
    found: bool
    emp_id: str
    current_credit: Optional[int] = None
    message: str = ""
    raw_text: str = ""
    server_login_status: str = "확인불가"
    can_logout: bool = False


def normalize_text(text: str) -> str:
    """HTML에서 추출한 텍스트의 공백과 줄바꿈을 파싱하기 좋은 형태로 정리한다."""
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def is_login_page(html: str) -> bool:
    """WISDOM 응답이 검색 결과가 아니라 로그인 화면인지 판정한다."""
    lowered = html.lower()
    indicators = [
        'name="empid"',
        "name='empid'",
        'name="password"',
        "name='password'",
        "login.do",
    ]
    return any(token in lowered for token in indicators)


def extract_alert_messages(html: str) -> list[str]:
    """WISDOM HTML 안의 alert 문구 중 사용자에게 의미 있는 메시지만 추출한다."""
    messages: list[str] = []
    pattern = re.compile(r'alert\s*\(\s*(["\'])([^"\']*?)\1\s*\)', re.IGNORECASE | re.DOTALL)
    for match in pattern.finditer(html):
        msg = normalize_text(match.group(2))
        if not msg:
            continue
        if any(token in msg for token in ["+", "split(", "mycredit", "document.", "form.", ";"]):
            continue
        messages.append(msg)
    return messages


def _parse_credit_number(text: str) -> Optional[int]:
    """잔여 매수 텍스트에서 숫자 credit 값을 추출한다."""
    cleaned = text.replace(",", "")
    match = re.search(r"(\d{1,9})\s*매", cleaned)
    if match:
        return int(match.group(1))
    match = re.search(r"\b(\d{1,9})\b", cleaned)
    if match:
        return int(match.group(1))
    return None


def _iter_user_rows(soup: BeautifulSoup):
    """WISDOM 결과 테이블에서 사용자 row와 직원번호를 순회한다."""
    for tr in soup.select("tr.userRow"):
        user_id_cell = tr.select_one(".userId")
        if not user_id_cell:
            continue
        row_emp_id = normalize_text(user_id_cell.get_text(" ", strip=True))
        yield tr, row_emp_id


def _get_exact_user_row(soup: BeautifulSoup, emp_id: str):
    """요청한 직원번호와 정확히 일치하는 row를 찾는다."""
    for tr, row_emp_id in _iter_user_rows(soup):
        if row_emp_id == emp_id:
            return tr
    return None


def _extract_credit_from_row(tr) -> Optional[int]:
    """사용자 row의 myCredit 셀에서 현재 매수를 추출한다."""
    credit_cell = tr.select_one(".myCredit")
    if not credit_cell:
        return None
    credit_text = normalize_text(credit_cell.get_text(" ", strip=True))
    return _parse_credit_number(credit_text)


def _extract_server_login_state_from_row(tr) -> tuple[str, bool]:
    """사용자 row의 로그아웃 영역으로 서버 로그인 상태를 판정한다."""
    logout_cell = None
    tds = tr.find_all("td")
    if len(tds) >= 9:
        logout_cell = tds[8]
    elif tds:
        logout_cell = tds[-1]

    if logout_cell is None:
        return "확인불가", False

    logout_text = normalize_text(logout_cell.get_text(" ", strip=True))
    logout_html = str(logout_cell).lower()
    has_logout_action = any(
        token in logout_html
        for token in ["iwslogout", "logout", "javascript:", "onclick", "href", "button", "input"]
    )

    if has_logout_action or (logout_text and logout_text != "-"):
        return "로그인됨", True
    if logout_text == "-":
        return "로그아웃됨", False
    return "확인불가", False


def parse_search_result(html: str, emp_id: str) -> SearchResult:
    """WISDOM 검색 HTML을 SearchResult로 변환한다.

    외부 HTML 구조를 ManagerService가 직접 알지 않도록, 직원번호 일치 여부와 credit 파싱,
    서버 로그인 상태를 이 함수에서 SearchResult 하나로 압축한다.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = normalize_text(soup.get_text("\n", strip=True))

    if is_login_page(html):
        return SearchResult(False, emp_id, None, "세션이 만료되었거나 로그인 페이지로 이동했습니다.", text)

    not_found_markers = [
        "조회 결과가 없습니다",
        "검색 결과가 없습니다",
        "일치하는 사용자가 없습니다",
        "대상이 없습니다",
        "해당 사용자가 없습니다",
        "검색된 사용자가 없습니다",
    ]
    if any(marker in text for marker in not_found_markers):
        return SearchResult(False, emp_id, None, "해당 학번/사번의 조회 결과가 없습니다.", text)

    # 같은 직원 row를 한 번만 찾고, 그 row에서 credit과 서버 로그인 상태를 함께 읽는다.
    # WISDOM HTML 테이블 순회를 줄이고 파싱 기준을 한 곳에 고정하기 위함이다.
    exact_row = _get_exact_user_row(soup, emp_id)
    if exact_row is None:
        return SearchResult(False, emp_id, None, "해당 학번/사번의 조회 결과가 없습니다.", text)

    server_login_status, can_logout = _extract_server_login_state_from_row(exact_row)
    credit = _extract_credit_from_row(exact_row)
    if credit is not None:
        return SearchResult(True, emp_id, credit, "정상 조회", text, server_login_status, can_logout)

    alerts = extract_alert_messages(html)
    msg = alerts[0] if alerts else "조회는 되었으나 현재 매수를 파싱하지 못했습니다."
    return SearchResult(True, emp_id, None, msg, text, server_login_status, can_logout)
