"""Manager 실행 세션 동안 이미 충전한 직원을 기억하는 메모리 저장소 모듈.

Client 재실행으로 중복 충전 제한이 풀리지 않게 Manager 프로세스 단위로 기록한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class RefillMark:
    """Manager 실행 세션 안에서 충전 완료 직원을 식별하기 위한 기록."""
    emp_id: str
    pc_name: str


class SessionRefillRegistry:
    """같은 Manager 실행 세션에서 동일 직원의 중복 충전을 막는 저장소."""
    def __init__(self) -> None:
        """객체가 사용할 상태와 UI 구성 요소를 초기화한다."""
        self._marks: Dict[str, RefillMark] = {}

    def has_refilled(self, emp_id: str) -> bool:
        """현재 Manager 실행 세션에서 해당 직원이 이미 충전되었는지 확인한다."""
        return emp_id in self._marks

    def get_mark(self, emp_id: str) -> Optional[RefillMark]:
        """중복 충전 기록을 조회해 어떤 PC에서 충전했는지 확인할 수 있게 한다."""
        return self._marks.get(emp_id)

    def mark_refilled(self, emp_id: str, pc_name: str) -> None:
        """충전 완료 직원을 Manager 실행 세션의 메모리 기록에 저장한다."""
        self._marks[emp_id] = RefillMark(emp_id=emp_id, pc_name=pc_name)
