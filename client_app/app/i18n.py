"""Client 화면에 표시할 한국어/영어 상태 문구를 생성하는 모듈.

Manager의 긴 message 문자열이 아니라 reasonCode와 수치 필드를 기준으로 사용자 문구를 만든다.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


# Manager 연결 전에도 Client 화면이 비어 보이지 않도록 하는 기본 공지다.
DEFAULT_ANNOUNCEMENT = (
    "등록된 정보가 없거나 매니저에 연결할 수 없습니다\n"
    "No configuration is available or the manager cannot be reached"
)


@dataclass(frozen=True)
class StatusPresentation:
    """Client 화면에 표시할 한국어/영어 문구와 표시 등급을 묶는 모델."""
    main_ko: str
    main_en: str
    severity: str
    contact_required: bool = False


@dataclass(frozen=True)
class MessageSpec:
    """정적 메시지의 영어 번역과 표시 등급을 함께 보관하는 모델."""
    en: str
    severity: str = "normal"
    contact_required: bool = False


def two_line(ko: str, en: str) -> str:
    """한국어와 영어 문장을 같은 상태 영역에 두 줄로 표시하기 위해 결합한다."""
    return f"{ko}\n{en}"


def _clean_display_text(text: str) -> str:
    """사용자 표시 문구에서 불필요한 마침표와 공백을 정리한다."""
    cleaned = (text or "").strip()
    cleaned = cleaned.replace("...", "…")
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n[ \t]+", "\n", cleaned)
    cleaned = re.sub(r"\.([ \t]*\))", r"\1", cleaned)
    cleaned = re.sub(r"\.(?=\n|$)", "", cleaned)
    return cleaned.strip()


def _value(obj: Any, name: str, default: Any = None) -> Any:
    """dict와 dataclass 응답을 같은 방식으로 읽기 위한 보조 함수."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _int_value(obj: Any, name: str, default: int = 0) -> int:
    """응답 필드를 정수로 읽고 실패하면 기본값을 반환한다."""
    try:
        return int(_value(obj, name, default) or 0)
    except (TypeError, ValueError):
        return default


def _code(obj: Any) -> str:
    """Manager 응답에서 상태 판단 기준인 reasonCode를 추출한다."""
    return str(_value(obj, "reasonCode", "") or "").strip()


# Manager 응답과 무관하게 Client 내부 상태 전환에서 사용하는 고정 문구다.
STATIC_MESSAGES: dict[str, MessageSpec] = {
    "충전중…": MessageSpec("Refilling…"),
    "로그아웃중…": MessageSpec("Logging out…"),
    "대기 중": MessageSpec("Ready"),
    "매니저 연결 성공": MessageSpec("Connected to the manager", "success"),
    "매니저 상태 이상": MessageSpec("The manager responded, but its status is abnormal", "error", True),
    "매니저 연결 실패": MessageSpec("Failed to connect to the manager", "error", True),
    "매니저 주소가 설정되지 않았습니다": MessageSpec("Manager address is not configured", "error", True),
    "매니저에 연결할 수 없습니다": MessageSpec("The manager cannot be reached", "error", True),
    "매니저 응답이 올바르지 않습니다": MessageSpec("The manager response is invalid", "error", True),
    "문제가 발생했습니다": MessageSpec("A problem occurred", "error", True),
    "조회 처리 중 문제가 발생했습니다": MessageSpec("A problem occurred while processing the search", "error", True),
    "충전 처리 중 문제가 발생했습니다": MessageSpec("A problem occurred while processing the refill", "error", True),
    "로그아웃 처리 중 문제가 발생했습니다": MessageSpec("A problem occurred while processing the logout", "error", True),
    "매니저에는 연결되었지만 설정이 아직 완료되지 않았습니다": MessageSpec(
        "Connected to the manager, but its configuration is incomplete",
        "error",
        True,
    ),
    "먼저 조회하세요": MessageSpec("Please search first", "error", False),
    "학번/사번을 입력하세요": MessageSpec("Please enter your ID or employee number", "error", False),
    "학번/사번이 비어 있습니다": MessageSpec("The ID or employee number is empty", "error", False),
}


PREFIX_MESSAGES: list[tuple[str, MessageSpec]] = [
    ("조회 실패:", MessageSpec("Search failed", "error", True)),
    ("충전 실패:", MessageSpec("Refill failed", "error", True)),
    ("로그아웃 실패:", MessageSpec("Logout failed", "error", True)),
    ("WISDOM 로그인 실패:", MessageSpec("WISDOM login failed", "error", True)),
    ("WISDOM 인증 실패:", MessageSpec("WISDOM authentication failed", "error", True)),
    ("WISDOM 통신 실패:", MessageSpec("WISDOM communication failed", "error", True)),
    ("WISDOM 로그아웃 실패:", MessageSpec("WISDOM logout failed", "error", True)),
    ("충전 처리 실패:", MessageSpec("Refill processing failed", "error", True)),
]


# API 통신의 기준은 message 문장이 아니라 reasonCode다.
# 이 매핑이 Client 사용자 문구의 1차 출처가 된다.
REASON_MESSAGES: dict[str, StatusPresentation] = {
    "INVALID_INPUT": StatusPresentation(
        "학번/사번을 입력하세요",
        "Please enter your ID or employee number",
        "error",
        False,
    ),
    "NOT_FOUND": StatusPresentation(
        "해당 학번/사번의 조회 결과가 없습니다",
        "No matching user was found for this ID or employee number",
        "error",
        False,
    ),
    "PARSE_FAILED": StatusPresentation(
        "조회는 되었으나 현재 매수를 확인하지 못했습니다",
        "The search completed, but the current balance could not be parsed",
        "error",
        True,
    ),
    "CONFIG_INVALID": StatusPresentation(
        "매니저 설정이 완료되지 않았습니다",
        "The manager configuration is incomplete",
        "error",
        True,
    ),
    "AUTH_ERROR": StatusPresentation(
        "WISDOM 인증에 실패했습니다",
        "WISDOM authentication failed",
        "error",
        True,
    ),
    "NETWORK_ERROR": StatusPresentation(
        "WISDOM 통신에 실패했습니다",
        "WISDOM communication failed",
        "error",
        True,
    ),
    "SEARCH_ERROR": StatusPresentation(
        "조회 처리 중 문제가 발생했습니다",
        "A problem occurred while processing the search",
        "error",
        True,
    ),
    "REFILL_ERROR": StatusPresentation(
        "충전 처리 중 문제가 발생했습니다",
        "A problem occurred while processing the refill",
        "error",
        True,
    ),
    "LOGOUT_ERROR": StatusPresentation(
        "로그아웃 처리 중 문제가 발생했습니다",
        "A problem occurred while processing the logout",
        "error",
        True,
    ),
    "ALREADY_REFILLED_IN_SESSION": StatusPresentation(
        "이미 이번 운영 세션에서 충전했습니다",
        "This user has already been refilled during the current operating session",
        "error",
        True,
    ),
    "REFILL_NOT_NEEDED": StatusPresentation(
        "현재 잔여 매수가 충분하여 충전이 필요하지 않습니다",
        "The current balance is sufficient, so refill is not needed",
        "normal",
        False,
    ),
    "LOGOUT_FAILED": StatusPresentation(
        "충전은 반영되었지만 서버 로그아웃에 실패했습니다",
        "The refill was applied, but the server logout failed",
        "error",
        True,
    ),
    "VERIFY_FAILED": StatusPresentation(
        "충전 후 최종 재확인에 실패했습니다",
        "Final verification after refill failed",
        "error",
        True,
    ),
    "VERIFY_AND_LOGOUT_FAILED": StatusPresentation(
        "충전 후 최종 재확인과 서버 로그아웃에 실패했습니다",
        "Final verification after refill and server logout failed",
        "error",
        True,
    ),
    "VERIFY_MISMATCH": StatusPresentation(
        "충전 후 재조회 값이 예상과 다릅니다",
        "The rechecked value is different from the expected value",
        "error",
        True,
    ),
    "LOGOUT_VERIFY_FAILED": StatusPresentation(
        "로그아웃 실패: 프린터서버 세션 종료를 확인하지 못했습니다",
        "Logout failed: the printer server session termination could not be verified",
        "error",
        True,
    ),
}


def _fallback_spec(text: str) -> MessageSpec:
    """알 수 없는 메시지를 일반 오류/일반 상태로 분류하는 fallback 규칙을 만든다."""
    is_problem = any(token in text for token in ("실패", "오류", "문제", "불가", "만료"))

    if "충전" in text:
        en = "A refill-related message was received"
    elif "조회" in text:
        en = "A search-related message was received"
    elif "로그아웃" in text:
        en = "A logout-related message was received"
    elif "매니저" in text:
        en = "A manager-related message was received"
    elif "WISDOM" in text:
        en = "A WISDOM-related message was received"
    else:
        en = "A status message was received"

    return MessageSpec(en=en, severity="error" if is_problem else "normal", contact_required=is_problem)


def build_status_presentation(korean: str) -> StatusPresentation:
    """정적 한국어 문구를 화면 표시용 한국어/영어 모델로 변환한다."""
    text = _clean_display_text(korean)
    if not text:
        return StatusPresentation("대기 중", "Ready", "normal", False)

    spec = STATIC_MESSAGES.get(text)
    if spec is not None:
        return StatusPresentation(text, spec.en, spec.severity, spec.contact_required)

    for prefix, prefix_spec in PREFIX_MESSAGES:
        if text.startswith(prefix):
            return StatusPresentation(text, prefix_spec.en, prefix_spec.severity, prefix_spec.contact_required)

    fallback = _fallback_spec(text)
    return StatusPresentation(text, fallback.en, fallback.severity, fallback.contact_required)


def build_search_presentation(result: Any) -> StatusPresentation:
    """검색 응답의 reasonCode와 수치 필드로 사용자 표시 문구를 만든다.

    Manager의 message 문장 변화가 Client 화면 로직을 깨지 않도록, 성공/실패 분기는
    reasonCode를 우선 사용하고 숫자 필드만 문장에 끼워 넣는다.
    """
    code = _code(result)
    current = _int_value(result, "currentCredit")
    refill = _int_value(result, "refillAmount")

    if code == "SEARCH_OK_REFILLABLE":
        return StatusPresentation(
            f"조회되었습니다\n현재 잔여 {current}매 / 충전 시 {current + refill}매까지 채웁니다",
            f"Search completed\nCurrent balance: {current} / Refill target: {current + refill}",
            "success",
            False,
        )
    if code == "SEARCH_OK_NOT_REFILLABLE":
        return StatusPresentation(
            f"조회되었습니다\n현재 잔여 {current}매 / 충전이 필요하지 않습니다",
            f"Search completed\nCurrent balance: {current} / Refill is not needed",
            "normal",
            False,
        )
    if code == "ALREADY_REFILLED_IN_SESSION":
        return StatusPresentation(
            f"조회되었습니다\n현재 잔여 {current}매 / 이미 이번 운영 세션에서 충전했습니다",
            f"Search completed\nCurrent balance: {current} / Already refilled during this operating session",
            "error",
            True,
        )

    return REASON_MESSAGES.get(code, build_status_presentation(str(_value(result, "message", "조회 처리 중 문제가 발생했습니다"))))


def build_refill_presentation(result: Any) -> StatusPresentation:
    """충전 응답의 reasonCode와 검증값으로 사용자 표시 문구를 만든다.

    충전 결과는 단순 성공/실패보다 로그아웃 실패, 재조회 실패, 검증값 불일치가 중요하므로
    reasonCode별로 사용자가 취해야 할 조치 수준을 구분한다.
    """
    code = _code(result)
    before = _int_value(result, "beforeCredit")
    refill = _int_value(result, "refillAmount")
    after = _int_value(result, "afterCredit")

    if code == "REFILL_OK":
        return StatusPresentation(
            f"충전되었습니다\n{before}매 → {after}매",
            f"Refill completed\n{before} to {after}",
            "success",
            False,
        )
    if code == "LOGOUT_FAILED":
        return StatusPresentation(
            f"충전은 반영되었습니다\n{before}매 → {after}매\n다만 서버 로그아웃은 실패했습니다",
            f"The refill was applied\n{before} to {after}\nHowever, server logout failed",
            "error",
            True,
        )
    if code == "VERIFY_MISMATCH":
        return StatusPresentation(
            f"충전 후 재조회 값이 예상과 다릅니다\n충전 전 {before}매 / 충전량 {refill}매 / 재조회 {after}매",
            f"The rechecked value is different from expected\nBefore: {before} / Refill: {refill} / Rechecked: {after}",
            "error",
            True,
        )

    return REASON_MESSAGES.get(code, build_status_presentation(str(_value(result, "message", "충전 처리 중 문제가 발생했습니다"))))


def build_logout_presentation(result: Any) -> StatusPresentation:
    """로그아웃 응답의 reasonCode로 사용자 표시 문구를 만든다."""
    code = _code(result)
    if code == "LOGOUT_OK":
        return StatusPresentation(
            "로그아웃 완료\n프린터서버 세션이 종료되었습니다",
            "Logout completed\nThe printer server session has been terminated",
            "success",
            False,
        )

    return REASON_MESSAGES.get(code, build_status_presentation(str(_value(result, "message", "로그아웃 처리 중 문제가 발생했습니다"))))
