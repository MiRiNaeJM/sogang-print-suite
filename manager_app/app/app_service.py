"""Manager GUI와 Flask API가 공유하는 업무 로직 모듈.

검색, 충전, 로그아웃, Client 설정 제공을 한 곳에서 처리해 GUI 로그와 HTTP 응답이 같은 규칙을 사용한다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, Optional

import requests

from .about_content import APP_VERSION
from .about_content_loader import load_client_about_content
from .config_models import EffectiveManagerConfig, ManagerLogRecord
from .session_refill_registry import SessionRefillRegistry
from .wisdom_client import WisdomAuthError, WisdomClient

TOPUP_LIMIT = 50
"""충전 후 맞춰야 하는 목표 매수.

Client가 충전량을 계산하지 않고 Manager가 WISDOM에서 현재 매수를 조회한 뒤
이 값까지 필요한 차이만큼 증가 요청을 보낸다.
"""


class ManagerService:
    """검색, 충전, 로그아웃을 처리하는 Manager의 업무 계층.

    GUI와 Flask API가 같은 객체를 사용하므로, Client로 반환되는 reasonCode와
    Manager 로그에 남는 message가 한 흐름에서 만들어진다. reasonCode는 Client 표시
    판단의 기준이고, message는 로그와 fallback을 위한 보조 정보다.
    """
    def __init__(
        self,
        config_provider: Callable[[], EffectiveManagerConfig],
        log_callback: Optional[Callable[[ManagerLogRecord], None]] = None,
    ) -> None:
        """객체가 사용할 상태와 UI 구성 요소를 초기화한다."""
        self._config_provider = config_provider
        self._log_callback = log_callback
        self._registry = SessionRefillRegistry()

    def _log(self, pc_name: str, emp_id: str, action: str, result: str, reason: str) -> None:
        """업무 처리 결과를 GUI 로그 콜백으로 전달한다."""
        if self._log_callback is None:
            return
        self._log_callback(
            ManagerLogRecord(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                pc_name=pc_name,
                emp_id=emp_id,
                action=action,
                result=result,
                reason=reason,
            )
        )

    def _build_client(self) -> WisdomClient:
        """현재 설정으로 WISDOM 요청용 클라이언트를 새로 만든다.

        사용량이 낮은 운영 환경을 전제로 요청마다 로그인/처리/종료 흐름을 수행한다.
        세션 재사용 최적화보다 외부 WISDOM 세션 상태를 예측 가능하게 유지하는 쪽을 택한다.
        """
        config = self._config_provider()
        return WisdomClient(config.secrets)

    def _refill_amount_for(self, current_credit: int) -> int:
        """현재 매수에서 목표 매수까지 필요한 충전량을 계산한다."""
        return max(0, TOPUP_LIMIT - current_credit)

    def _search_payload(
        self,
        *,
        ok: bool,
        found: bool,
        emp_id: str,
        current_credit: int = 0,
        refill_amount: int = 0,
        can_refill: bool = False,
        server_login_status: str = "확인불가",
        can_logout: bool = False,
        message: str,
        reason_code: str,
    ) -> Dict[str, Any]:
        """Client 검색 응답 dict를 한 형식으로 생성한다."""
        return {
            "ok": ok,
            "found": found,
            "empId": emp_id,
            "currentCredit": current_credit,
            "refillAmount": refill_amount,
            "canRefill": can_refill,
            "serverLoginStatus": server_login_status,
            "canLogout": can_logout,
            "message": message,
            "reasonCode": reason_code,
        }

    def _refill_payload(
        self,
        *,
        ok: bool,
        emp_id: str,
        before_credit: int = 0,
        refill_amount: int = 0,
        after_credit: int = 0,
        logout_done: bool = False,
        server_login_status: str = "확인불가",
        can_logout: bool = False,
        message: str,
        reason_code: str,
    ) -> Dict[str, Any]:
        """Client 충전 응답 dict를 한 형식으로 생성한다."""
        return {
            "ok": ok,
            "empId": emp_id,
            "beforeCredit": before_credit,
            "refillAmount": refill_amount,
            "afterCredit": after_credit,
            "logoutDone": logout_done,
            "serverLoginStatus": server_login_status,
            "canLogout": can_logout,
            "message": message,
            "reasonCode": reason_code,
        }

    def _logout_payload(
        self,
        *,
        ok: bool,
        emp_id: str,
        message: str,
        server_login_status: str = "확인불가",
        can_logout: bool = False,
        reason_code: str,
    ) -> Dict[str, Any]:
        """Client 로그아웃 응답 dict를 한 형식으로 생성한다."""
        return {
            "ok": ok,
            "empId": emp_id,
            "message": message,
            "serverLoginStatus": server_login_status,
            "canLogout": can_logout,
            "reasonCode": reason_code,
        }

    def health(self) -> Dict[str, Any]:
        """Manager 서버 실행 여부와 설정 완료 상태를 확인한다."""
        config = self._config_provider()
        configured = bool(
            config.secrets.wisdom_base_url and
            config.secrets.wisdom_admin_id and
            config.secrets.wisdom_admin_pw
        )
        return {
            "ok": True,
            "message": "running",
            "configured": configured,
        }

    def get_client_config(self) -> Dict[str, Any]:
        """Client가 사용할 공지와 프로그램 정보를 반환한다."""
        config = self._config_provider()
        return {
            "ok": True,
            "announcement": config.public.announcement,
            "managerVersion": APP_VERSION,
            "aboutContent": load_client_about_content(),
        }

    def search(self, emp_id: str, pc_name: str) -> Dict[str, Any]:
        """직원번호를 WISDOM에서 조회하고 Client가 표시할 검색 응답을 만든다.

        Client는 입력과 표시만 담당하므로 현재 잔여 매수, 충전 가능 여부, 서버 로그인 상태는
        Manager가 WISDOM 응답을 기준으로 다시 계산해 내려준다.
        """
        emp_id = (emp_id or "").strip()
        if not emp_id:
            payload = self._search_payload(
                ok=False,
                found=False,
                emp_id="",
                message="학번/사번을 입력하세요.",
                reason_code="INVALID_INPUT",
            )
            self._log(pc_name, emp_id, "search", "rejected", payload["message"])
            return payload

        client = self._build_client()
        try:
            client.login()
            result = client.search_user(emp_id)
        except ValueError as exc:
            payload = self._search_payload(
                ok=False,
                found=False,
                emp_id=emp_id,
                message=str(exc),
                reason_code="CONFIG_INVALID",
            )
            self._log(pc_name, emp_id, "search", "rejected", payload["message"])
            return payload
        except WisdomAuthError as exc:
            payload = self._search_payload(
                ok=False,
                found=False,
                emp_id=emp_id,
                message=f"WISDOM 로그인 실패: {exc}",
                reason_code="AUTH_ERROR",
            )
            self._log(pc_name, emp_id, "search", "rejected", payload["message"])
            return payload
        except requests.RequestException as exc:
            payload = self._search_payload(
                ok=False,
                found=False,
                emp_id=emp_id,
                message=f"조회 실패: {exc}",
                reason_code="NETWORK_ERROR",
            )
            self._log(pc_name, emp_id, "search", "rejected", payload["message"])
            return payload
        except Exception as exc:
            payload = self._search_payload(
                ok=False,
                found=False,
                emp_id=emp_id,
                message=f"조회 실패: {exc}",
                reason_code="SEARCH_ERROR",
            )
            self._log(pc_name, emp_id, "search", "error", payload["message"])
            return payload
        finally:
            client.close()

        if not result.found:
            payload = self._search_payload(
                ok=False,
                found=False,
                emp_id=emp_id,
                server_login_status=result.server_login_status,
                can_logout=result.can_logout,
                message=result.message or "조회 결과가 없습니다.",
                reason_code="NOT_FOUND",
            )
            self._log(pc_name, emp_id, "search", "rejected", payload["message"])
            return payload

        if result.current_credit is None:
            payload = self._search_payload(
                ok=False,
                found=False,
                emp_id=emp_id,
                server_login_status=result.server_login_status,
                can_logout=result.can_logout,
                message=result.message or "현재 매수를 파싱하지 못했습니다.",
                reason_code="PARSE_FAILED",
            )
            self._log(pc_name, emp_id, "search", "rejected", payload["message"])
            return payload

        current_credit = result.current_credit
        refill_amount = self._refill_amount_for(current_credit)
        already_refilled = self._registry.has_refilled(emp_id)
        can_refill = refill_amount > 0 and not already_refilled
        if already_refilled:
            reason_code = "ALREADY_REFILLED_IN_SESSION"
        elif can_refill:
            reason_code = "SEARCH_OK_REFILLABLE"
        else:
            reason_code = "SEARCH_OK_NOT_REFILLABLE"

        message = (
            f"현재 잔여 {current_credit}매 / 충전 시 {TOPUP_LIMIT}매까지 채웁니다."
            if can_refill
            else f"현재 잔여 {current_credit}매 / 충전 불가"
        )
        payload = self._search_payload(
            ok=True,
            found=True,
            emp_id=emp_id,
            current_credit=current_credit,
            refill_amount=refill_amount,
            can_refill=can_refill,
            server_login_status=result.server_login_status,
            can_logout=result.can_logout,
            message=message,
            reason_code=reason_code,
        )
        self._log(pc_name, emp_id, "search", "success", message)
        return payload

    def refill(self, emp_id: str, pc_name: str) -> Dict[str, Any]:
        """직원번호의 현재 매수를 재조회하고 필요한 만큼 WISDOM 증가 요청을 보낸다.

        Manager 실행 세션 안에서 이미 충전한 직원은 다시 충전하지 않는다.
        충전 요청 후에는 재조회 값이 기대값과 일치하는지 확인해 성공 여부를 판단한다.
        """
        emp_id = (emp_id or "").strip()
        if not emp_id:
            payload = self._refill_payload(
                ok=False,
                emp_id="",
                message="학번/사번이 비어 있습니다.",
                reason_code="INVALID_INPUT",
            )
            self._log(pc_name, emp_id, "refill", "rejected", payload["message"])
            return payload

        if self._registry.has_refilled(emp_id):
            mark = self._registry.get_mark(emp_id)
            reason = f"이미 이번 운영 세션에서 충전했습니다. ({mark.pc_name if mark else '-'})"
            payload = self._refill_payload(
                ok=False,
                emp_id=emp_id,
                message=reason,
                reason_code="ALREADY_REFILLED_IN_SESSION",
            )
            self._log(pc_name, emp_id, "refill", "rejected", reason)
            return payload

        client = self._build_client()
        try:
            client.login()
            before = client.search_user(emp_id)
            if not before.found or before.current_credit is None:
                reason_code = "NOT_FOUND" if not before.found else "PARSE_FAILED"
                payload = self._refill_payload(
                    ok=False,
                    emp_id=emp_id,
                    server_login_status=before.server_login_status,
                    can_logout=before.can_logout,
                    message=before.message or "충전 전 사용자 조회에 실패했습니다.",
                    reason_code=reason_code,
                )
                self._log(pc_name, emp_id, "refill", "rejected", payload["message"])
                return payload

            before_credit = before.current_credit
            refill_amount = self._refill_amount_for(before_credit)
            if refill_amount <= 0:
                payload = self._refill_payload(
                    ok=False,
                    emp_id=emp_id,
                    before_credit=before_credit,
                    after_credit=before_credit,
                    server_login_status=before.server_login_status,
                    can_logout=before.can_logout,
                    message=f"현재 잔여가 이미 {TOPUP_LIMIT}매 이상입니다.",
                    reason_code="REFILL_NOT_NEEDED",
                )
                self._log(pc_name, emp_id, "refill", "rejected", payload["message"])
                return payload

            increase_done = False
            logout_done = False
            logout_error = ""
            after_credit: int | None = None
            try:
                client.increase_credit(emp_id, refill_amount)
                increase_done = True
                after = client.search_user(emp_id)
                after_credit = after.current_credit
            finally:
                if increase_done:
                    try:
                        client.logout_user(emp_id)
                        logout_done = True
                    except Exception as exc:
                        logout_error = str(exc)
        except ValueError as exc:
            payload = self._refill_payload(
                ok=False,
                emp_id=emp_id,
                message=str(exc),
                reason_code="CONFIG_INVALID",
            )
            self._log(pc_name, emp_id, "refill", "rejected", payload["message"])
            return payload
        except WisdomAuthError as exc:
            payload = self._refill_payload(
                ok=False,
                emp_id=emp_id,
                message=f"WISDOM 인증 실패: {exc}",
                reason_code="AUTH_ERROR",
            )
            self._log(pc_name, emp_id, "refill", "rejected", payload["message"])
            return payload
        except requests.RequestException as exc:
            payload = self._refill_payload(
                ok=False,
                emp_id=emp_id,
                message=f"WISDOM 통신 실패: {exc}",
                reason_code="NETWORK_ERROR",
            )
            self._log(pc_name, emp_id, "refill", "rejected", payload["message"])
            return payload
        except Exception as exc:
            payload = self._refill_payload(
                ok=False,
                emp_id=emp_id,
                message=f"충전 처리 실패: {exc}",
                reason_code="REFILL_ERROR",
            )
            self._log(pc_name, emp_id, "refill", "error", payload["message"])
            return payload
        finally:
            client.close()

        expected_credit = before_credit + refill_amount
        verified = after_credit == expected_credit

        # 충전은 단순 요청 성공이 아니라 재조회 값이 기대값과 일치해야 성공으로 본다.
        # logout 성공 여부는 사용자가 추가 조치를 해야 하는지 판단하기 위해 별도로 유지한다.
        if verified and logout_done:
            message = f"충전 완료: {before_credit}매 → {after_credit}매."
            ok = True
            reason_code = "REFILL_OK"
            server_login_status = "로그아웃됨"
            can_logout = False
        elif verified and not logout_done:
            message = f"충전은 반영되었습니다: {before_credit}매 → {after_credit}매. 다만 서버 로그아웃은 실패했습니다. ({logout_error})"
            ok = False
            reason_code = "LOGOUT_FAILED"
            server_login_status = "로그인됨"
            can_logout = True
        elif after_credit is None and logout_done:
            message = "충전 후 최종 재확인에는 실패했지만 서버 로그아웃은 완료되었습니다. 관리자가 실제 반영값을 다시 확인하세요."
            ok = False
            reason_code = "VERIFY_FAILED"
            server_login_status = "로그아웃됨"
            can_logout = False
        elif after_credit is None and not logout_done:
            message = f"충전 후 최종 재확인에 실패했고 서버 로그아웃도 실패했습니다. ({logout_error})"
            ok = False
            reason_code = "VERIFY_AND_LOGOUT_FAILED"
            server_login_status = "확인불가"
            can_logout = True
        else:
            message = f"재조회 값이 예상과 다릅니다. 충전 전 {before_credit}매, 충전량 {refill_amount}매, 재조회 {after_credit}매."
            message += " 서버 로그아웃은 완료되었습니다." if logout_done else f" 서버 로그아웃도 실패했습니다. ({logout_error})"
            ok = False
            reason_code = "VERIFY_MISMATCH"
            server_login_status = "로그아웃됨" if logout_done else "로그인됨"
            can_logout = not logout_done

        payload = self._refill_payload(
            ok=ok,
            emp_id=emp_id,
            before_credit=before_credit,
            refill_amount=refill_amount,
            after_credit=after_credit if after_credit is not None else before_credit,
            logout_done=logout_done,
            server_login_status=server_login_status,
            can_logout=can_logout,
            message=message,
            reason_code=reason_code,
        )
        if ok:
            self._registry.mark_refilled(emp_id, pc_name)
            self._log(pc_name, emp_id, "refill", "success", message)
        else:
            self._log(pc_name, emp_id, "refill", "rejected", message)
        return payload

    def logout_user(self, emp_id: str, pc_name: str) -> Dict[str, Any]:
        """직원번호의 WISDOM 프린터 서버 세션 종료를 요청하고 결과를 검증한다.

        Client는 서버 세션을 직접 다루지 않으므로 Manager가 로그아웃 요청과 재조회 확인을
        함께 수행해 사용자가 추가 조치를 해야 하는지 알려준다.
        """
        emp_id = (emp_id or "").strip()
        if not emp_id:
            payload = self._logout_payload(
                ok=False,
                emp_id="",
                message="학번/사번이 비어 있습니다.",
                reason_code="INVALID_INPUT",
            )
            self._log(pc_name, emp_id, "logout", "rejected", payload["message"])
            return payload

        client = self._build_client()
        try:
            client.login()
            result = client.logout_user(emp_id)
            parsed = result.search_result
            if parsed is None:
                parsed = client.search_user(emp_id)
        except ValueError as exc:
            payload = self._logout_payload(
                ok=False,
                emp_id=emp_id,
                message=str(exc),
                reason_code="CONFIG_INVALID",
            )
            self._log(pc_name, emp_id, "logout", "rejected", payload["message"])
            return payload
        except WisdomAuthError as exc:
            payload = self._logout_payload(
                ok=False,
                emp_id=emp_id,
                message=f"WISDOM 로그아웃 실패: {exc}",
                reason_code="AUTH_ERROR",
            )
            self._log(pc_name, emp_id, "logout", "rejected", payload["message"])
            return payload
        except requests.RequestException as exc:
            payload = self._logout_payload(
                ok=False,
                emp_id=emp_id,
                message=f"로그아웃 실패: {exc}",
                reason_code="NETWORK_ERROR",
            )
            self._log(pc_name, emp_id, "logout", "rejected", payload["message"])
            return payload
        except Exception as exc:
            payload = self._logout_payload(
                ok=False,
                emp_id=emp_id,
                message=f"로그아웃 실패: {exc}",
                reason_code="LOGOUT_ERROR",
            )
            self._log(pc_name, emp_id, "logout", "error", payload["message"])
            return payload
        finally:
            client.close()

        success = parsed.server_login_status == "로그아웃됨" or not parsed.can_logout
        if success:
            message = "로그아웃 완료: 프린터서버 세션이 종료되었습니다."
            reason_code = "LOGOUT_OK"
        else:
            message = "로그아웃 실패: 프린터서버 세션 종료를 확인하지 못했습니다."
            reason_code = "LOGOUT_VERIFY_FAILED"

        payload = self._logout_payload(
            ok=success,
            emp_id=emp_id,
            message=message,
            server_login_status=parsed.server_login_status,
            can_logout=parsed.can_logout,
            reason_code=reason_code,
        )
        self._log(pc_name, emp_id, "logout", "success" if success else "rejected", message)
        return payload
