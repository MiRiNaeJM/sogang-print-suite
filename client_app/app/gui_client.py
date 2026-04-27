"""SOGANG Print Client의 메인 GUI 모듈.

사용자 입력과 결과 표시를 담당하며, 검색/충전 가능 여부의 최종 판단은 Manager 응답을 따른다.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from .client_context import build_client_context
from .config_store import ClientConfigStore
from .about_dialog import AboutDialog, ToolTip
from .about_content_loader import load_about_content, normalize_about_content
from .i18n import (
    DEFAULT_ANNOUNCEMENT,
    build_logout_presentation,
    build_refill_presentation,
    build_search_presentation,
    build_status_presentation,
    two_line,
)
from .manager_api import ManagerApi
from .resource_utils import APP_ICON_PNG, _load_photo_image, _set_window_icon
from .ui_style import (
    apply_base_style,
    bordered_card,
    CARD_BG,
    TEXT,
    PRIMARY,
    DANGER,
    SUCCESS_FG,
)


class ClientGUI:
    """사용자 입력과 상태 표시를 담당하는 Client 메인 화면.

    Client는 충전 가능 여부를 최종 판정하지 않는다. 조회, 충전, 로그아웃 판단은 Manager가
    WISDOM 상태를 기준으로 처리하고, 이 화면은 reasonCode에 맞는 사용자 안내를 표시한다.
    """
    def __init__(self) -> None:
        """객체가 사용할 상태와 UI 구성 요소를 초기화한다."""
        self.root = tk.Tk()
        self.root.title("SOGANG Print Client")
        self.root.geometry("860x900")
        self.root.minsize(840, 800)

        self.window_icon_image = _set_window_icon(self.root)
        self.header_icon_image = None
        apply_base_style(self.root)

        self.context = build_client_context()
        self.store = ClientConfigStore()
        self.config = self.store.load()
        self.api = ManagerApi(self.config.manager_base_url)
        self.about_content = load_about_content()

        self.current_emp_id = ""
        self.current_can_logout = False

        self._build_ui()
        self.refresh_from_manager()

    def _build_ui(self) -> None:
        """화면에 필요한 Tkinter 위젯을 생성하고 배치한다."""
        frm = ttk.Frame(self.root, padding=22)
        frm.pack(fill=tk.BOTH, expand=True)
        frm.columnconfigure(0, weight=1)
        frm.rowconfigure(4, weight=1)

        self.credit_var = tk.StringVar(value="-")

        header = ttk.Frame(frm)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header.columnconfigure(0, weight=1)

        title_box = ttk.Frame(header)
        title_box.grid(row=0, column=0, sticky="w")

        self.title_label = ttk.Label(title_box, text="프린터 충전 클라이언트", style="Title.TLabel")
        self.title_label.grid(row=0, column=0, sticky="w")

        ttk.Label(title_box, text="Printer Refill Client", style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(5, 0))
        ttk.Label(title_box, text=f"PC: {self.context.pc_name}", style="Subtitle.TLabel").grid(row=2, column=0, sticky="w", pady=(12, 0))

        self.header_icon_image = _load_photo_image(APP_ICON_PNG, width=120, height=120)
        if self.header_icon_image is not None:
            self.header_icon_label = ttk.Label(header, image=self.header_icon_image, cursor="hand2")
        else:
            self.header_icon_label = ttk.Label(header, text="ⓘ", style="Title.TLabel", cursor="hand2")
        self.header_icon_label.grid(row=0, column=1, sticky="ne", padx=(20, 6))
        self.header_icon_label.bind("<Button-1>", self.open_about)
        ToolTip(self.header_icon_label, "프로그램 정보")

        ann_outer, ann_card = bordered_card(frm, padding=16)
        ann_outer.grid(row=1, column=0, sticky="nsew", pady=(0, 14))
        ann_card.columnconfigure(0, weight=1)
        ann_card.rowconfigure(1, weight=1)

        ttk.Label(ann_card, text="공지 / Announcement", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.announcement_text = ScrolledText(
            ann_card,
            height=8,
            wrap="word",
            font=("맑은 고딕", 10),
            relief="flat",
            borderwidth=0,
            background=CARD_BG,
            foreground=TEXT,
            insertbackground=TEXT,
        )
        self.announcement_text.grid(row=1, column=0, sticky="nsew")
        self._set_readonly_text(self.announcement_text, DEFAULT_ANNOUNCEMENT, TEXT, ("맑은 고딕", 10))

        search_outer, search_card = bordered_card(frm, padding=16)
        search_outer.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        search_card.columnconfigure(0, weight=1)

        ttk.Label(search_card, text="사용자 조회 / Search", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 14))

        search_row = ttk.Frame(search_card, style="Inner.TFrame")
        search_row.grid(row=1, column=0, sticky="ew")
        search_row.columnconfigure(2, weight=1)

        ttk.Label(search_row, text="학번/사번", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(search_row, text="ID / Employee No.", style="Muted.TLabel").grid(row=0, column=1, sticky="w", padx=(8, 18))

        self.emp_var = tk.StringVar()
        ttk.Entry(search_row, textvariable=self.emp_var, width=26).grid(row=0, column=2, sticky="w", padx=(0, 10))

        self.search_button = ttk.Button(search_row, text="조회 / Search", command=self.perform_search, style="Primary.TButton")
        self.search_button.grid(row=0, column=3, sticky="e")

        result_grid = ttk.Frame(search_card, style="Inner.TFrame")
        result_grid.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        result_grid.columnconfigure(0, weight=1)
        result_grid.columnconfigure(1, weight=1)

        balance_box = ttk.Frame(result_grid, style="Inner.TFrame")
        balance_box.grid(row=0, column=0, sticky="ew", padx=(0, 20))

        ttk.Label(balance_box, text="현재 매수", style="Card.TLabel", font=("맑은 고딕", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(balance_box, text="Current balance", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))
        tk.Label(balance_box, textvariable=self.credit_var, bg=CARD_BG, fg=TEXT, font=("맑은 고딕", 22, "bold"), anchor="w").grid(row=2, column=0, sticky="w", pady=(10, 0))

        server_box = ttk.Frame(result_grid, style="Inner.TFrame")
        server_box.grid(row=0, column=1, sticky="ew")

        ttk.Label(server_box, text="프린터 로그인 상태", style="Card.TLabel", font=("맑은 고딕", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(server_box, text="Printer log-in status", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.server_status_badge = tk.Label(server_box, text="X", bg=CARD_BG, fg=TEXT, padx=4, pady=2, font=("맑은 고딕", 14, "bold"))
        self.server_status_badge.grid(row=2, column=0, sticky="w", pady=(12, 0))

        action_box = ttk.Frame(frm)
        action_box.grid(row=3, column=0, sticky="ew", pady=(0, 14))

        self.refill_button = ttk.Button(action_box, text="충전 / Refill", command=self.perform_refill, style="Primary.TButton")
        self.refill_button.pack(side=tk.LEFT)

        self.logout_button = ttk.Button(action_box, text="로그아웃 / Logout", command=self.perform_logout, state=tk.DISABLED)
        self.logout_button.pack(side=tk.LEFT, padx=(8, 0))

        status_outer, status_card = bordered_card(frm, padding=16)
        status_outer.grid(row=4, column=0, sticky="nsew")
        status_card.columnconfigure(0, weight=1)
        status_card.rowconfigure(1, weight=1)

        ttk.Label(status_card, text="상태 / Status", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.status_text = ScrolledText(
            status_card,
            height=6,
            wrap="word",
            font=("맑은 고딕", 10),
            relief="flat",
            borderwidth=0,
            background=CARD_BG,
            foreground=TEXT,
            insertbackground=TEXT,
        )
        self.status_text.grid(row=1, column=0, sticky="nsew")

        self.status_text.tag_configure("normal", foreground=TEXT, font=("맑은 고딕", 10))
        self.status_text.tag_configure("success", foreground=PRIMARY, font=("맑은 고딕", 10, "bold"))
        self.status_text.tag_configure("error", foreground=DANGER, font=("맑은 고딕", 10, "bold"))
        self.status_text.tag_configure("contact", foreground=TEXT, font=("맑은 고딕", 10, "bold"))

        self._set_status("대기 중")

    def _set_readonly_text(self, widget: ScrolledText, content: str, color: str, font: tuple) -> None:
        """읽기 전용 텍스트 위젯의 내용을 안전하게 교체한다."""
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.tag_configure("body", foreground=color, font=font)
        widget.insert(tk.END, content.strip(), "body")
        widget.configure(state=tk.DISABLED)

    def _refresh_client_config(self) -> None:
        """Manager에서 공지와 Client 프로그램 정보를 다시 받아 화면 상태를 갱신한다.

        조회/충전/로그아웃 후에도 호출해 관리자가 수정한 공지와 aboutContent가 사용 중인
        Client 화면에 자연스럽게 반영되도록 한다.
        """
        try:
            client_config = self.api.get_client_config()
            announcement = (client_config.announcement or "").strip()
            self._set_readonly_text(
                self.announcement_text,
                announcement if announcement else DEFAULT_ANNOUNCEMENT,
                TEXT,
                ("맑은 고딕", 10),
            )
            if client_config.aboutContent:
                self.about_content = normalize_about_content(client_config.aboutContent)
        except Exception:
            pass

    def _render_status(self, presentation) -> None:
        """상태 표시 모델을 실제 GUI 라벨과 텍스트로 반영한다."""
        severity_tag = {"normal": "normal", "success": "success", "error": "error"}.get(presentation.severity, "normal")

        self.status_text.configure(state=tk.NORMAL)
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert(tk.END, f"{presentation.main_ko}\n{presentation.main_en}", severity_tag)

        if presentation.contact_required:
            self.status_text.insert(tk.END, "\n\n다시 시도하거나 관리자에게 문의해 주세요\nPlease try again or contact the administrator", "contact")

        self.status_text.configure(state=tk.DISABLED)
        self.root.update_idletasks()

    def _set_status(self, korean_message: str) -> None:
        """한국어 상태 문구를 표시 모델로 변환해 화면에 반영한다."""
        self._render_status(build_status_presentation(korean_message))

    def _set_busy(self, busy: bool) -> None:
        """요청 처리 중 버튼 중복 클릭을 막기 위해 busy 상태를 반영한다."""
        state = tk.DISABLED if busy else tk.NORMAL
        self.search_button.configure(state=state)
        self.refill_button.configure(state=state)
        self.logout_button.configure(state=tk.DISABLED if busy or not self.current_can_logout else tk.NORMAL)
        self.root.update_idletasks()

    def _update_server_login_status(self, status_text: str | None, can_logout: bool) -> None:
        """WISDOM 프린터 서버 로그인 상태를 Client 화면에 표시한다."""
        self.current_can_logout = bool(can_logout)
        symbol = "O" if can_logout else "X"
        fg = SUCCESS_FG if can_logout else TEXT

        if hasattr(self, "server_status_badge"):
            self.server_status_badge.configure(text=symbol, bg=CARD_BG, fg=fg)

        self.logout_button.configure(state=tk.NORMAL if self.current_can_logout else tk.DISABLED)

    def _classify_exception_message(self, action: str, exc: Exception) -> str:
        """통신 예외 내용을 사용자에게 보여줄 일반 문구로 분류한다."""
        text = str(exc or "").lower()
        connection_markers = (
            "httpconnectionpool",
            "max retries exceeded",
            "failed to establish a new connection",
            "newconnectionerror",
            "connection refused",
            "winerror 10061",
            "winerror 10060",
            "winerror 11001",
            "temporarily failure in name resolution",
            "temporary failure in name resolution",
            "name or service not known",
            "nodename nor servname provided",
            "connection aborted",
            "connection reset",
            "read timed out",
            "connect timeout",
            "timeout",
        )
        response_markers = (
            "404 client error",
            "500 server error",
            "502 server error",
            "503 server error",
            "504 server error",
            "bad response",
            "invalid response",
            "jsondecodeerror",
            "expecting value",
            "not json",
        )

        if any(marker in text for marker in connection_markers):
            return "매니저에 연결할 수 없습니다"
        if any(marker in text for marker in response_markers):
            return "매니저 응답이 올바르지 않습니다"
        if action == "search":
            return "조회 처리 중 문제가 발생했습니다"
        if action == "refill":
            return "충전 처리 중 문제가 발생했습니다"
        if action == "logout":
            return "로그아웃 처리 중 문제가 발생했습니다"
        if action == "refresh":
            return "매니저에 연결할 수 없습니다"
        return "문제가 발생했습니다"

    def _reset_result(self) -> None:
        """이전 조회 결과를 초기화해 잘못된 충전 버튼 활성화를 막는다."""
        self.credit_var.set("-")
        self.current_emp_id = ""
        self._update_server_login_status(None, False)

    def _has_manager_base_url(self) -> bool:
        """Client 설정에 Manager 주소가 있는지 확인한다."""
        return bool((self.config.manager_base_url or "").strip())

    def refresh_from_manager(self) -> None:
        """Manager 연결 상태와 Client 설정을 수동으로 다시 확인한다."""
        if not self._has_manager_base_url():
            self._set_readonly_text(self.announcement_text, DEFAULT_ANNOUNCEMENT, TEXT, ("맑은 고딕", 10))
            self._set_status("매니저 주소가 설정되지 않았습니다")
            self._reset_result()
            return

        try:
            self.api = ManagerApi(self.config.manager_base_url)
            health = self.api.health()
            if not health.ok:
                self._set_status("매니저 상태 이상")
                return

            self._refresh_client_config()

            if health.configured:
                self._set_status("매니저 연결 성공")
            else:
                self._set_status("매니저에는 연결되었지만 설정이 아직 완료되지 않았습니다")
        except Exception as exc:
            self._set_readonly_text(self.announcement_text, DEFAULT_ANNOUNCEMENT, TEXT, ("맑은 고딕", 10))
            self._set_status(self._classify_exception_message("refresh", exc))
            self._reset_result()

    def perform_search(self) -> None:
        """입력된 직원번호를 Manager에 조회 요청하고 결과를 화면에 반영한다."""
        if not self._has_manager_base_url():
            self._set_status("매니저 주소가 설정되지 않았습니다")
            return

        emp_id = self.emp_var.get().strip()
        if not emp_id:
            messagebox.showwarning("입력 필요 / Input required", two_line("학번/사번을 입력하세요", "Please enter your ID or employee number"))
            return

        self._set_busy(True)
        try:
            result = self.api.search(emp_id, self.context.pc_name)
            self.current_emp_id = emp_id if result.found else ""
            self.credit_var.set(str(result.currentCredit) if result.found else "-")
            self._update_server_login_status(result.serverLoginStatus, result.canLogout)
            self._render_status(build_search_presentation(result))
            self._refresh_client_config()
        except Exception as exc:
            self._update_server_login_status(None, False)
            self._set_status(self._classify_exception_message("search", exc))
        finally:
            self._set_busy(False)

    def perform_refill(self) -> None:
        """현재 조회된 직원번호에 대해 Manager에 충전 요청을 보낸다.

        화면 버튼 상태는 사용자 경험용 방어선이다. 중복 충전 여부와 실제 충전량은
        Manager 응답을 기준으로 확정한다.
        """
        if not self._has_manager_base_url():
            self._set_status("매니저 주소가 설정되지 않았습니다")
            return

        emp_id = self.current_emp_id or self.emp_var.get().strip()
        if not emp_id:
            messagebox.showwarning("입력 필요 / Input required", two_line("먼저 조회하세요", "Please search first"))
            return

        self._set_status("충전중…")
        self._set_busy(True)
        try:
            result = self.api.refill(emp_id, self.context.pc_name)
            if result.ok:
                self.credit_var.set(str(result.afterCredit))
            self._update_server_login_status(result.serverLoginStatus, result.canLogout)
            self._render_status(build_refill_presentation(result))
            self._refresh_client_config()
        except Exception as exc:
            self._update_server_login_status(None, False)
            self._set_status(self._classify_exception_message("refill", exc))
        finally:
            self._set_busy(False)

    def perform_logout(self) -> None:
        """현재 조회된 직원번호의 프린터 서버 로그아웃을 Manager에 요청한다."""
        if not self._has_manager_base_url():
            self._set_status("매니저 주소가 설정되지 않았습니다")
            return

        emp_id = self.current_emp_id or self.emp_var.get().strip()
        if not emp_id:
            messagebox.showwarning("입력 필요 / Input required", two_line("먼저 조회하세요", "Please search first"))
            return

        self._set_status("로그아웃중…")
        self._set_busy(True)
        try:
            result = self.api.logout_user(emp_id, self.context.pc_name)
            self._update_server_login_status(result.serverLoginStatus, result.canLogout)
            self._render_status(build_logout_presentation(result))
            self._refresh_client_config()
        except Exception as exc:
            self._update_server_login_status(None, False)
            self._set_status(self._classify_exception_message("logout", exc))
        finally:
            self._set_busy(False)

    def open_about(self, _event=None) -> None:
        """현재 보관 중인 프로그램 정보로 정보 창을 연다."""
        AboutDialog(self.root, self.about_content)

    def run(self) -> None:
        """Tkinter 이벤트 루프를 시작한다."""
        self.root.mainloop()


def launch_client_gui() -> None:
    """Client GUI 객체를 만들고 Tkinter 이벤트 루프를 시작한다."""
    ClientGUI().run()
