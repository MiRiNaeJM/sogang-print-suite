"""Manager 서버 상태 응답을 사람이 읽는 문장으로 바꾸는 모듈.

GUI 코드에서 상태 표시 문구 생성을 분리해 서버 상태 해석을 한 곳에 모은다.
"""

from __future__ import annotations

from typing import Mapping


def humanize_health(state: Mapping[str, object]) -> str:
    """서버 상태 응답 dict를 관리자용 설명 문장으로 변환한다."""
    ok = bool(state.get("ok"))
    configured = bool(state.get("configured"))
    message = str(state.get("message", ""))

    response_line = "서버 응답: 정상입니다." if ok else "서버 응답: 비정상입니다."
    config_line = (
        "설정 상태: WISDOM 및 매니저 설정이 완료되었습니다."
        if configured
        else "설정 상태: WISDOM 또는 매니저 설정이 아직 완료되지 않았습니다."
    )

    if message == "running":
        status_line = "서버 현황: 현재 서버가 실행 중입니다."
    elif message == "stopped":
        status_line = "서버 현황: 현재 서버가 중지되어 있습니다."
    else:
        status_line = f"서버 현황: {message}"

    return "\n".join([response_line, config_line, status_line])
