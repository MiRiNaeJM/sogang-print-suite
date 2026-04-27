"""Manager 공개 설정과 비밀 설정을 편집하는 관리자 대화상자 모듈.

초기 설정과 일반 설정 화면이 같은 검증/저장 규칙을 사용하도록 하나의 창으로 구현한다.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from .config_models import ManagerPublicConfig, ManagerSecrets
from .ui_style import (
    apply_base_style,
    bordered_panel,
    BG,
)


WISDOM_BASE_URL_PLACEHOLDER = "http://(프린터 서버 주소):(포트)/WISDOM/"
PLACEHOLDER_ENTRY_STYLE = "Placeholder.TEntry"


try:
    from .resource_utils import _set_window_icon
except Exception:
    ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
    APP_ICON_PNG = ASSETS_DIR / "app_icon.png"
    APP_ICON_ICO = ASSETS_DIR / "app_icon.ico"

    def _load_photo_image(path: Path, *, width: int | None = None, height: int | None = None) -> tk.PhotoImage | None:
        """아이콘 이미지를 Tkinter PhotoImage로 읽되 실패하면 None을 반환한다."""
        if not path.exists():
            return None

        try:
            image = tk.PhotoImage(file=str(path))
        except tk.TclError:
            return None

        if width and image.width() > width:
            image = image.subsample(max(1, image.width() // width))
        if height and image.height() > height:
            image = image.subsample(max(1, image.height() // height))

        return image

    def _set_window_icon(window: tk.Misc) -> tk.PhotoImage | None:
        """창 아이콘을 설정하고 실패해도 앱 실행을 계속한다."""
        if APP_ICON_ICO.exists():
            try:
                window.iconbitmap(str(APP_ICON_ICO))
                return None
            except tk.TclError:
                pass

        image = _load_photo_image(APP_ICON_PNG, width=64, height=64)
        if image is not None:
            try:
                window.iconphoto(True, image)
            except tk.TclError:
                pass
        return image


class AdminDialog(tk.Toplevel):
    """AdminDialog 관련 상태와 동작을 하나의 책임 단위로 묶는다."""
    def __init__(
        self,
        master: tk.Misc,
        public_config: ManagerPublicConfig,
        secrets: ManagerSecrets,
        *,
        require_complete_setup: bool = False,
    ) -> None:
        """객체가 사용할 상태와 UI 구성 요소를 초기화한다."""
        super().__init__(master)
        self.title("관리 페이지")
        self.resizable(False, False)
        self.result: dict | None = None
        self.require_complete_setup = require_complete_setup
        self.icon_image = _set_window_icon(self)

        self._original_public_config = public_config
        self._placeholder_entries: dict[ttk.Entry, str] = {}

        apply_base_style(self)
        self.configure(bg=BG)

        self._configure_placeholder_style()

        self.bind_host_var = tk.StringVar(value=public_config.manager_host)
        self.bind_port_var = tk.StringVar(value=str(public_config.manager_port))
        self.wisdom_base_url_var = tk.StringVar(value=secrets.wisdom_base_url)
        self.wisdom_admin_id_var = tk.StringVar(value=secrets.wisdom_admin_id)
        self.wisdom_admin_pw_var = tk.StringVar(value=secrets.wisdom_admin_pw)
        self.new_password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()

        frm = ttk.Frame(self, padding=18)
        frm.pack(fill=tk.BOTH, expand=True)
        frm.columnconfigure(0, weight=1)

        title_text = "초기 설정" if self.require_complete_setup else "관리 페이지"
        subtitle_text = (
            "처음 실행하려면 서버, WISDOM, 관리자 비밀번호를 설정해야 합니다."
            if self.require_complete_setup
            else "서버, WISDOM, 관리자 비밀번호 설정을 변경합니다."
        )

        ttk.Label(frm, text=title_text, style="DialogTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(frm, text=subtitle_text, style="DialogSubtitle.TLabel").grid(
            row=1,
            column=0,
            sticky="w",
            pady=(4, 14),
        )

        server_outer, server_panel = bordered_panel(frm, padding=14)
        server_outer.grid(row=2, column=0, sticky="ew")
        self._section_title(server_panel, "서버 설정", 0)

        self._field(server_panel, "Bind Host", self.bind_host_var, 1, width=22, column_offset=0)
        self._field(server_panel, "Bind Port", self.bind_port_var, 1, width=10, column_offset=2)

        wisdom_outer, wisdom_panel = bordered_panel(frm, padding=14)
        wisdom_outer.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        self._section_title(wisdom_panel, "WISDOM 설정", 0)

        self.wisdom_base_url_entry = self._field(
            wisdom_panel,
            "WISDOM Base URL",
            self.wisdom_base_url_var,
            1,
            width=56,
        )
        self._apply_placeholder(self.wisdom_base_url_entry, WISDOM_BASE_URL_PLACEHOLDER)

        self._field(wisdom_panel, "WISDOM Admin ID", self.wisdom_admin_id_var, 2, width=26)
        self._field(wisdom_panel, "WISDOM Admin PW", self.wisdom_admin_pw_var, 3, width=26, show="*")

        password_outer, password_panel = bordered_panel(frm, padding=14)
        password_outer.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        self._section_title(password_panel, "관리 페이지 비밀번호", 0)

        self._field(password_panel, "새 비밀번호", self.new_password_var, 1, width=28, show="*")
        self._field(password_panel, "비밀번호 확인", self.confirm_password_var, 2, width=28, show="*")

        password_help = (
            "최초 설정에서는 반드시 입력해야 합니다."
            if self.require_complete_setup
            else "비워두면 기존 비밀번호를 유지합니다."
        )
        ttk.Label(password_panel, text=password_help, style="PanelMuted.TLabel").grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0),
        )

        footer = ttk.Frame(frm)
        footer.grid(row=5, column=0, sticky="ew", pady=(16, 0))
        footer.columnconfigure(0, weight=1)

        left_buttons = ttk.Frame(footer)
        left_buttons.grid(row=0, column=0, sticky="w")

        right_buttons = ttk.Frame(footer)
        right_buttons.grid(row=0, column=1, sticky="e")

        ttk.Button(
            left_buttons,
            text="프로그램 정보",
            command=self.open_about_editor,
        ).pack(side=tk.LEFT)

        ttk.Button(right_buttons, text="취소", command=self.cancel).pack(side=tk.LEFT)
        ttk.Button(right_buttons, text="저장", style="Primary.TButton", command=self.save).pack(side=tk.LEFT, padx=(8, 0))

        self.bind("<Escape>", lambda _event: self.cancel())
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.transient(master)
        self.grab_set()
        self.update_idletasks()
        self._center_on_master(master)

    def _configure_placeholder_style(self) -> None:
        """placeholder 입력값을 일반 입력값과 구분할 스타일을 준비한다."""
        style = ttk.Style(self)
        style.configure(PLACEHOLDER_ENTRY_STYLE, foreground="#9CA3AF")

    def _apply_placeholder(self, entry: ttk.Entry, placeholder: str) -> None:
        """빈 Entry에 안내 문구를 표시하고 실제 값과 구분한다."""
        self._placeholder_entries[entry] = placeholder

        def show_placeholder() -> None:
            """show_placeholder 동작을 수행한다."""
            if entry.get():
                return
            entry.insert(0, placeholder)
            entry.configure(style=PLACEHOLDER_ENTRY_STYLE)
            setattr(entry, "_is_placeholder", True)

        def hide_placeholder(_event=None) -> None:
            """hide_placeholder 동작을 수행한다."""
            if getattr(entry, "_is_placeholder", False):
                entry.delete(0, tk.END)
                entry.configure(style="TEntry")
                setattr(entry, "_is_placeholder", False)

        def restore_placeholder(_event=None) -> None:
            """restore_placeholder 동작을 수행한다."""
            if not entry.get():
                show_placeholder()

        entry.bind("<FocusIn>", hide_placeholder, add="+")
        entry.bind("<FocusOut>", restore_placeholder, add="+")
        show_placeholder()

    def _entry_value(self, entry: ttk.Entry) -> str:
        """placeholder가 아닌 실제 Entry 입력값만 반환한다."""
        if getattr(entry, "_is_placeholder", False):
            return ""
        return entry.get().strip()

    def _center_on_master(self, master: tk.Misc) -> None:
        """대화상자를 부모 창 중앙 근처에 배치한다."""
        try:
            x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
            y = master.winfo_rooty() + (master.winfo_height() - self.winfo_height()) // 2
            self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        except tk.TclError:
            pass

    def _section_title(self, parent: ttk.Frame, text: str, row: int) -> None:
        """관리자 설정 화면의 섹션 제목 라벨을 생성한다."""
        ttk.Label(parent, text=text, style="Panel.TLabel", font=("맑은 고딕", 11, "bold")).grid(
            row=row,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(0, 10),
        )

    def _field(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        row: int,
        *,
        width: int,
        show: str | None = None,
        column_offset: int = 0,
        colspan: int = 1,
    ) -> ttk.Entry:
        """관리자 설정 화면에 라벨과 Entry 한 쌍을 배치한다."""
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(
            row=row,
            column=column_offset,
            sticky="w",
            padx=(0, 8),
            pady=4,
        )
        entry = ttk.Entry(parent, textvariable=variable, width=width, show=show or "")
        entry.grid(row=row, column=column_offset + 1, columnspan=colspan, sticky="w", pady=4)
        return entry

    def open_about_editor(self) -> None:
        """관리자가 Manager/Client 프로그램 정보 편집 창을 열 수 있게 한다."""
        from .about_editor_dialog import AboutEditorDialog

        AboutEditorDialog(self)

    def save(self) -> None:
        """현재 설정 값을 JSON 또는 암호화 파일로 저장한다."""
        try:
            port = int(self.bind_port_var.get().strip())
            if port <= 0 or port > 65535:
                raise ValueError
        except ValueError:
            messagebox.showerror("입력 오류", "Bind Port는 1~65535 사이의 숫자여야 합니다.", parent=self)
            return

        new_password = self.new_password_var.get()
        confirm_password = self.confirm_password_var.get()

        if self.require_complete_setup and not new_password:
            messagebox.showerror("입력 오류", "초기 관리자 비밀번호를 입력하세요.", parent=self)
            return

        if new_password or confirm_password:
            if new_password != confirm_password:
                messagebox.showerror("입력 오류", "새 비밀번호와 확인 값이 일치하지 않습니다.", parent=self)
                return

        wisdom_base_url = self._entry_value(self.wisdom_base_url_entry)
        wisdom_admin_id = self.wisdom_admin_id_var.get().strip()
        wisdom_admin_pw = self.wisdom_admin_pw_var.get()

        if self.require_complete_setup:
            missing = []
            if not wisdom_base_url:
                missing.append("WISDOM Base URL")
            if not wisdom_admin_id:
                missing.append("WISDOM Admin ID")
            if not wisdom_admin_pw:
                missing.append("WISDOM Admin PW")

            if missing:
                messagebox.showerror(
                    "입력 오류",
                    "초기 설정에 필요한 값을 입력하세요: " + ", ".join(missing),
                    parent=self,
                )
                return

        public = ManagerPublicConfig(
            manager_host=self.bind_host_var.get().strip() or "0.0.0.0",
            manager_port=port,
            announcement=self._original_public_config.announcement,
            admin_password_hash=self._original_public_config.admin_password_hash,
        )

        secrets = ManagerSecrets(
            wisdom_base_url=wisdom_base_url,
            wisdom_admin_id=wisdom_admin_id,
            wisdom_admin_pw=wisdom_admin_pw,
        )

        self.result = {
            "public": public,
            "secrets": secrets,
            "new_password": new_password,
        }
        self.destroy()

    def cancel(self) -> None:
        """변경 내용을 저장하지 않고 대화상자를 닫는다."""
        self.result = None
        self.destroy()
