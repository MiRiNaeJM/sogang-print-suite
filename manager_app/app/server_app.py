"""Flask route를 ManagerService에 연결하는 API 어댑터 모듈.

HTTP 요청 파싱과 JSON 응답 변환만 담당하고 실제 업무 판단은 ManagerService에 위임한다.
"""

from __future__ import annotations

from flask import Flask, jsonify, request

from .app_service import ManagerService


def create_server_app(service: ManagerService) -> Flask:
    """ManagerService를 사용하는 Flask 앱과 API route를 생성한다."""
    app = Flask(__name__)

    @app.get("/health")
    def health():
        """Manager 서버 실행 여부와 설정 완료 상태를 확인한다."""
        return jsonify(service.health())

    @app.get("/client-config")
    def client_config():
        """Client가 시작 또는 갱신 시 받을 설정 응답을 반환한다."""
        return jsonify(service.get_client_config())

    @app.post("/search")
    def search():
        """직원번호 조회 요청을 Manager에 전달한다."""
        payload = request.get_json(silent=True) or {}
        emp_id = str(payload.get("empId", "")).strip()
        pc_name = str(payload.get("pcName", "")).strip() or "UNKNOWN-PC"
        if not emp_id:
            return jsonify({
                "ok": False,
                "found": False,
                "empId": "",
                "currentCredit": 0,
                "refillAmount": 0,
                "canRefill": False,
                "serverLoginStatus": "확인불가",
                "canLogout": False,
                "message": "empId가 비어 있습니다.",
                "reasonCode": "INVALID_INPUT",
            }), 400
        return jsonify(service.search(emp_id, pc_name))

    @app.post("/refill")
    def refill():
        """직원번호 충전 요청을 Manager에 전달한다."""
        payload = request.get_json(silent=True) or {}
        emp_id = str(payload.get("empId", "")).strip()
        pc_name = str(payload.get("pcName", "")).strip() or "UNKNOWN-PC"
        if not emp_id:
            return jsonify({
                "ok": False,
                "empId": "",
                "beforeCredit": 0,
                "refillAmount": 0,
                "afterCredit": 0,
                "logoutDone": True,
                "serverLoginStatus": "확인불가",
                "canLogout": False,
                "message": "empId가 비어 있습니다.",
                "reasonCode": "INVALID_INPUT",
            }), 400
        return jsonify(service.refill(emp_id, pc_name))

    @app.post("/logout-user")
    def logout_user():
        """직원번호의 프린터 서버 로그아웃 요청을 Manager에 전달한다."""
        payload = request.get_json(silent=True) or {}
        emp_id = str(payload.get("empId", "")).strip()
        pc_name = str(payload.get("pcName", "")).strip() or "UNKNOWN-PC"
        if not emp_id:
            return jsonify({
                "ok": False,
                "empId": "",
                "message": "empId가 비어 있습니다.",
                "serverLoginStatus": "확인불가",
                "canLogout": False,
                "reasonCode": "INVALID_INPUT",
            }), 400
        return jsonify(service.logout_user(emp_id, pc_name))

    return app
