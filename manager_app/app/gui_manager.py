"""SOGANG Print Manager의 메인 GUI 모듈.

공지, 서버 상태, WISDOM 설정, 운영 로그, 트레이 종료 흐름을 관리자 화면에서 제어한다.
"""

from __future__ import annotations

from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from .admin_auth import hash_password, verify_password
from .admin_dialog import AdminDialog
from .about_dialog import AboutDialog
from .app_service import ManagerService
from .config_models import EffectiveManagerConfig, ManagerLogRecord, ManagerPublicConfig
from .dialogs import PasswordDialog
from .health_presenter import humanize_health
from .public_config_store import PublicConfigStore
from .resource_utils import _set_window_icon
from .secret_store import SecretStore
from .server_app import create_server_app
from .server_runtime import ServerRuntime
from .tray_runtime import TrayRuntime
from .ui_style import (
    apply_base_style,
    bordered_card,
    CARD_BG,
    TEXT,
    SUCCESS_BG,
    SUCCESS_FG,
)


class ManagerGUI:
    """Manager의 관리자 화면과 서버 수명 주기를 제어하는 메인 GUI."""
    def __init__(self) -> None:
        """객체가 사용할 상태와 UI 구성 요소를 초기화한다."""
        self.root = tk.Tk()
        self.root.title("SOGANG Print Manager")
        self.root.geometry("980x730")
        self.root.minsize(900, 650)

        self.window_icon_image = _set_window_icon(self.root)
        apply_base_style(self.root)

        self.public_store = PublicConfigStore()
        self.secret_store = SecretStore()
        self.public_config = self.public_store.load()
        self.secrets = self.secret_store.load()

        self.service = ManagerService(self.get_effective_config, self.append_log)
        self.server_runtime = ServerRuntime(
            app_factory=lambda: create_server_app(self.service),
            host=self.public_config.manager_host,
            port=self.public_config.manager_port,
        )
        self.tray = TrayRuntime(
            show_callback=lambda: self.root.after(0, self.restore_window),
            toggle_server_callback=lambda: self.root.after(0, self.toggle_server),
            status_callback=lambda: self.root.after(0, self.check_health),
            exit_callback=lambda: self.root.after(0, self.exit_program),
            is_server_running=lambda: self.server_runtime.is_running(),
        )
        self.tray_started = False
        self.is_exiting = False

        self._build_ui()
        self._load_into_form()
        self.root.protocol("WM_DELETE_WINDOW", self.handle_close_request)
        self.root.bind("<Control-Return>", self._save_announcement_shortcut)

        self._init_tray()
        if self._ensure_initial_setup():
            self.start_server(auto=True)
        else:
            self.append_system_log("setup", "rejected", "초기 설정이 완료되지 않아 서버를 시작하지 않았습니다.")


    def _configuration_errors(self) -> list[str]:
        """서버 시작 전 필수 설정 누락 여부를 확인한다."""
        errors: list[str] = []
        if not self.public_config.admin_password_hash:
            errors.append("관리자 비밀번호")
        if not (self.secrets.wisdom_base_url or "").strip():
            errors.append("WISDOM Base URL")
        if not (self.secrets.wisdom_admin_id or "").strip():
            errors.append("WISDOM Admin ID")
        if not (self.secrets.wisdom_admin_pw or ""):
            errors.append("WISDOM Admin PW")
        return errors

    def _ensure_initial_setup(self) -> bool:
        """최초 실행 시 필요한 관리자 설정을 완료할 때까지 안내한다."""
        if not self._configuration_errors():
            return True

        dlg_admin = AdminDialog(self.root, self.public_config, self.secrets, require_complete_setup=True)
        self.root.wait_window(dlg_admin)
        if not dlg_admin.result:
            messagebox.showwarning("초기 설정 필요", "초기 설정이 완료되지 않았습니다. 설정 버튼을 눌러 다시 진행하세요.")
            return False

        try:
            new_public: ManagerPublicConfig = dlg_admin.result["public"]
            new_password = dlg_admin.result.get("new_password", "")
            new_public.admin_password_hash = hash_password(new_password)
            self._apply_public_config(new_public)
            self.secrets = dlg_admin.result["secrets"]
            self.secret_store.save(self.secrets)
            self._notify("초기 설정 저장", "초기 설정을 저장했습니다.")
            messagebox.showinfo("초기 설정 완료", "초기 설정을 저장했습니다.")
            return True
        except Exception as exc:
            messagebox.showerror("초기 설정 저장 실패", str(exc))
            return False

    def get_effective_config(self) -> EffectiveManagerConfig:
        """공개 설정과 비밀 설정을 합쳐 서비스 계층에 제공한다."""
        return EffectiveManagerConfig(public=self.public_config, secrets=self.secrets)

    def _build_ui(self) -> None:
        """화면에 필요한 Tkinter 위젯을 생성하고 배치한다."""
        frm = ttk.Frame(self.root, padding=16)
        frm.pack(fill=tk.BOTH, expand=True)
        frm.columnconfigure(0, weight=1)
        frm.rowconfigure(2, weight=1)

        home_outer, home_box = bordered_card(frm, padding=16)
        home_outer.grid(row=0, column=0, sticky="ew")
        home_box.columnconfigure(1, weight=1)

        ttk.Label(home_box, text="홈", style="SectionTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))
        ttk.Label(home_box, text="Announcement", style="Card.TLabel").grid(row=1, column=0, sticky="nw", pady=(2, 0))

        announcement_frame = ttk.Frame(home_box, style="Inner.TFrame")
        announcement_frame.grid(row=1, column=1, sticky="nsew", padx=8)
        announcement_frame.columnconfigure(0, weight=1)
        announcement_frame.rowconfigure(0, weight=1)

        self.announcement_text = tk.Text(
            announcement_frame,
            width=78,
            height=4,
            wrap="word",
            relief="solid",
            borderwidth=1,
            background=CARD_BG,
            foreground=TEXT,
            insertbackground=TEXT,
            font=("맑은 고딕", 10),
        )
        announcement_scroll = ttk.Scrollbar(announcement_frame, orient="vertical", command=self.announcement_text.yview)
        self.announcement_text.configure(yscrollcommand=announcement_scroll.set)
        self.announcement_text.grid(row=0, column=0, sticky="nsew")
        announcement_scroll.grid(row=0, column=1, sticky="ns")

        home_actions = ttk.Frame(home_box, style="Inner.TFrame")
        home_actions.grid(row=1, column=2, sticky="n", padx=(12, 0))
        ttk.Button(home_actions, text="프로그램 종료", command=self.exit_program, style="Danger.TButton").pack(fill=tk.X)
        ttk.Button(home_actions, text="프로그램 정보", command=self.open_about).pack(fill=tk.X, pady=(8, 0))
        ttk.Label(home_box, text="Enter는 줄바꿈, Ctrl+Enter는 공지 저장입니다.", style="Muted.TLabel").grid(row=2, column=1, sticky="w", padx=8, pady=(8, 0))

        buttons = ttk.Frame(home_box, style="Inner.TFrame")
        buttons.grid(row=3, column=1, sticky="e", padx=8, pady=(12, 0))
        ttk.Button(buttons, text="공지 저장", command=self.save_announcement, style="Primary.TButton").pack(side=tk.LEFT)
        ttk.Button(buttons, text="설정", command=self.open_admin_page).pack(side=tk.LEFT, padx=(8, 0))

        server_outer, server_box = bordered_card(frm, padding=16)
        server_outer.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        server_box.columnconfigure(2, weight=1)

        self.server_status_var = tk.StringVar(value="서버 상태: 중지됨")
        ttk.Label(server_box, text="서버 제어", style="SectionTitle.TLabel").grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 12))
        ttk.Label(server_box, text="서버 상태", style="Card.TLabel").grid(row=1, column=0, sticky="w")

        self.server_status_badge = tk.Label(server_box, text="중지됨", bg="#F3F4F6", fg="#374151", padx=12, pady=5, font=("맑은 고딕", 10, "bold"))
        self.server_status_badge.grid(row=1, column=1, sticky="w", padx=(10, 18))

        self.server_address_var = tk.StringVar(value="")
        ttk.Label(server_box, textvariable=self.server_address_var, style="Muted.TLabel").grid(row=1, column=2, sticky="w")

        self.server_toggle_button = ttk.Button(server_box, text="서버 시작", command=self.toggle_server, style="Primary.TButton")
        self.server_toggle_button.grid(row=1, column=3, padx=(12, 8))
        ttk.Button(server_box, text="상태 확인", command=self.check_health).grid(row=1, column=4)

        log_outer, log_box = bordered_card(frm, padding=16)
        log_outer.grid(row=2, column=0, sticky="nsew", pady=(14, 0))
        log_outer.columnconfigure(0, weight=1)
        log_outer.rowconfigure(0, weight=1)
        log_box.columnconfigure(0, weight=1)
        log_box.rowconfigure(1, weight=1)

        ttk.Label(log_box, text="로그", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))

        table_frame = ttk.Frame(log_box, style="Inner.TFrame")
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("timestamp", "pc_name", "emp_id", "action", "result", "reason")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)

        for col, title, width in [
            ("timestamp", "시각", 150),
            ("pc_name", "PC 이름", 120),
            ("emp_id", "학번/사번", 120),
            ("action", "작업", 90),
            ("result", "결과", 100),
            ("reason", "사유", 440),
        ]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        self._configure_log_row_tags()

    def _load_into_form(self) -> None:
        """저장된 설정 값을 GUI 입력 영역에 반영한다."""
        self.announcement_text.delete("1.0", tk.END)
        self.announcement_text.insert("1.0", self.public_config.announcement)
        self._update_server_widgets()

    def _save_announcement_shortcut(self, _event=None):
        """키보드 단축키로 공지 저장을 실행하고 기본 이벤트를 막는다."""
        self.save_announcement()
        return "break"

    def save_announcement(self) -> None:
        """홈 화면에서 수정한 공지를 공개 설정 파일에 저장한다."""
        self.public_config.announcement = self.announcement_text.get("1.0", tk.END).rstrip()
        self.public_store.save(self.public_config)
        self._notify("공지 저장", "공지사항을 저장했습니다.")
        messagebox.showinfo("저장 완료", "공지사항을 저장했습니다.")

    def _apply_public_config(self, new_public: ManagerPublicConfig) -> None:
        """관리자 설정 창에서 저장된 공개 설정을 GUI와 런타임에 반영한다."""
        restart_needed = self.public_config.manager_host != new_public.manager_host or self.public_config.manager_port != new_public.manager_port
        new_public.announcement = self.public_config.announcement
        self.public_config = new_public
        self.public_store.save(self.public_config)
        self.server_runtime.update_binding(self.public_config.manager_host, self.public_config.manager_port)
        if restart_needed and self.server_runtime.is_running():
            try:
                self.server_runtime.restart(self.public_config.manager_host, self.public_config.manager_port)
                self.append_system_log("system", "success", "서버 바인드 설정이 바뀌어 서버를 다시 시작했습니다.")
            except Exception as exc:
                self.append_system_log("system", "error", f"서버 재시작 실패: {exc}")
                raise
        self._update_server_widgets()

    def open_admin_page(self) -> None:
        """관리자 설정 대화상자를 열고 저장 결과를 현재 화면에 반영한다."""
        if not self.public_config.admin_password_hash:
            self._ensure_initial_setup()
            return

        dlg = PasswordDialog(self.root, "관리자 확인", "관리자 비밀번호를 입력하세요.")
        self.root.wait_window(dlg)
        if dlg.result is None:
            return
        if not verify_password(dlg.result, self.public_config.admin_password_hash):
            messagebox.showwarning("접근 거부", "관리자 비밀번호가 일치하지 않습니다.")
            return

        dlg_admin = AdminDialog(self.root, self.public_config, self.secrets)
        self.root.wait_window(dlg_admin)
        if not dlg_admin.result:
            return
        try:
            new_public: ManagerPublicConfig = dlg_admin.result["public"]
            new_public.admin_password_hash = self.public_config.admin_password_hash
            new_password = dlg_admin.result.get("new_password", "")
            if new_password:
                new_public.admin_password_hash = hash_password(new_password)
            self._apply_public_config(new_public)
            self.secrets = dlg_admin.result["secrets"]
            self.secret_store.save(self.secrets)
            self._notify("설정 저장", "관리 페이지 설정을 저장했습니다.")
            messagebox.showinfo("저장 완료", "관리 페이지 설정을 저장했습니다.")
        except Exception as exc:
            messagebox.showerror("저장 실패", str(exc))

    def _init_tray(self) -> None:
        """트레이 아이콘 런타임을 만들고 백그라운드로 시작한다."""
        self.tray_started = self.tray.start()

    def _update_server_widgets(self) -> None:
        """서버 실행 여부와 바인딩 주소를 화면 버튼/라벨에 반영한다."""
        if self.server_runtime.is_running():
            self.server_status_var.set(f"서버 상태: 실행 중 ({self.public_config.manager_host}:{self.public_config.manager_port})")
            if hasattr(self, "server_status_badge"):
                self.server_status_badge.configure(text="실행 중", bg=SUCCESS_BG, fg=SUCCESS_FG)
            if hasattr(self, "server_address_var"):
                self.server_address_var.set(f"{self.public_config.manager_host}:{self.public_config.manager_port}")
            self.server_toggle_button.configure(text="서버 종료")
        else:
            self.server_status_var.set("서버 상태: 중지됨")
            if hasattr(self, "server_status_badge"):
                self.server_status_badge.configure(text="중지됨", bg="#F3F4F6", fg="#374151")
            if hasattr(self, "server_address_var"):
                self.server_address_var.set("")
            self.server_toggle_button.configure(text="서버 시작")

        self.tray.refresh()

    def start_server(self, auto: bool = False) -> None:
        """현재 설정으로 Manager API 서버를 시작한다."""
        missing = self._configuration_errors()
        if missing:
            message = "서버 시작 전 필요한 설정을 완료하세요: " + ", ".join(missing)
            self.append_system_log("setup", "rejected", message)
            self._notify("설정 필요", message)
            if not auto:
                messagebox.showwarning("설정 필요", message)
            self._update_server_widgets()
            return

        try:
            self.server_runtime.update_binding(self.public_config.manager_host, self.public_config.manager_port)
            self.server_runtime.start()
            self._update_server_widgets()
            message = "프로그램 시작과 함께 서버를 실행했습니다." if auto else "서버를 시작했습니다."
            self.append_system_log("system", "success", message)
            self._notify("서버 시작", message)
        except Exception as exc:
            self._update_server_widgets()
            error = f"서버 시작 실패: {exc}"
            self.append_system_log("system", "error", error)
            self._notify("서버 오류", error)
            if not auto:
                messagebox.showerror("서버 시작 실패", str(exc))

    def stop_server(self) -> None:
        """실행 중인 Manager API 서버를 중지한다."""
        try:
            self.server_runtime.stop()
            self._update_server_widgets()
            self.append_system_log("system", "success", "서버를 종료했습니다.")
            self._notify("서버 종료", "서버를 종료했습니다.")
        except Exception as exc:
            self.append_system_log("system", "error", f"서버 종료 실패: {exc}")
            self._notify("서버 오류", f"서버 종료 실패: {exc}")
            messagebox.showerror("서버 종료 실패", str(exc))

    def toggle_server(self) -> None:
        """현재 상태에 따라 서버 시작 또는 중지를 실행한다."""
        if self.server_runtime.is_running():
            self.stop_server()
        else:
            self.start_server(auto=False)

    def check_health(self) -> None:
        """현재 서버 상태를 조회해 관리자에게 사람이 읽는 문장으로 보여준다."""
        state = self.service.health()
        state["message"] = "running" if self.server_runtime.is_running() else "stopped"
        messagebox.showinfo("서버 현황", humanize_health(state))

    def append_system_log(self, action: str, result: str, reason: str) -> None:
        """시스템 이벤트를 운영 로그 표에 추가한다."""
        record = ManagerLogRecord(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pc_name="MANAGER", emp_id="-", action=action, result=result, reason=reason)
        self.append_log(record)

    def _configure_log_row_tags(self) -> None:
        """로그 결과별 색상 태그를 Treeview에 등록한다."""
        self.tree.tag_configure(
            "log_success",
            background="#F0FDF4",
            foreground="#166534",
        )
        self.tree.tag_configure(
            "log_rejected",
            background="#FFF7ED",
            foreground="#9A3412",
        )
        self.tree.tag_configure(
            "log_error",
            background="#FEF2F2",
            foreground="#991B1B",
        )
        self.tree.tag_configure(
            "log_default",
            background="#FFFFFF",
            foreground="#0F172A",
        )

    def _log_tag_for_result(self, result: str) -> str:
        """로그 결과 문자열을 Treeview 태그 이름으로 변환한다."""
        normalized = (result or "").strip().lower()
        if normalized == "success":
            return "log_success"
        if normalized == "rejected":
            return "log_rejected"
        if normalized == "error":
            return "log_error"
        return "log_default"

    def append_log(self, record: ManagerLogRecord) -> None:
        """ManagerService에서 전달한 운영 로그를 표와 알림에 반영한다."""
        def _insert() -> None:
            """_insert 동작을 수행한다."""
            self.tree.insert(
                "",
                0,
                values=(
                    record.timestamp,
                    record.pc_name,
                    record.emp_id,
                    record.action,
                    record.result,
                    record.reason,
                ),
                tags=(self._log_tag_for_result(record.result),),
            )

            if self._should_notify(record):
                self._notify(self._notification_title(record), record.reason)

        self.root.after(0, _insert)

    def _should_notify(self, record: ManagerLogRecord) -> bool:
        """로그 이벤트 중 트레이 알림으로 보여줄 항목을 판정한다."""
        if record.action == "search" and record.result == "success":
            return False
        if record.action == "system":
            return True
        return record.result in {"success", "rejected", "error"}

    def _notification_title(self, record: ManagerLogRecord) -> str:
        """로그 이벤트의 action/result를 알림 제목으로 변환한다."""
        if record.action == "refill" and record.result == "success":
            return "충전 완료"
        if record.result == "error":
            return "오류"
        if record.result == "rejected":
            return "처리 거부"
        return "SOGANG Print Manager"

    def _notify(self, title: str, message: str) -> None:
        """트레이가 준비되어 있으면 운영 이벤트 알림을 표시한다."""
        self.tray.notify(title, message)

    def open_about(self) -> None:
        """현재 보관 중인 프로그램 정보로 정보 창을 연다."""
        AboutDialog(self.root)

    def handle_close_request(self) -> None:
        """창 닫기 버튼을 트레이 최소화 동작으로 처리한다."""
        if self.is_exiting:
            return
        if self.tray_started:
            self.root.withdraw()
            self._notify("SOGANG Print Manager", "창을 숨기고 서버는 계속 실행합니다.")
        else:
            self.root.iconify()

    def restore_window(self) -> None:
        """트레이에서 숨겨진 Manager 창을 다시 표시한다."""
        self.root.deiconify()
        self.root.lift()
        try:
            self.root.focus_force()
        except Exception:
            pass

    def exit_program(self) -> None:
        """트레이, 서버, GUI를 순서대로 종료한다."""
        self.is_exiting = True
        try:
            self.server_runtime.stop()
        except Exception:
            pass
        self.tray.stop()
        self.root.destroy()

    def run(self) -> None:
        """Tkinter 이벤트 루프를 시작한다."""
        self.root.mainloop()


def launch_manager_gui() -> None:
    """Manager GUI 객체를 만들고 Tkinter 이벤트 루프를 시작한다."""
    ManagerGUI().run()
