"""Manager와 Client 프로그램 정보를 편집하는 관리자 대화상자 모듈.

두 앱의 about JSON을 한 화면에서 관리해 배포 후 문구 수정이 코드 변경 없이 가능하도록 한다.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from typing import Mapping

from .about_content_loader import (
    load_client_about_content,
    load_manager_about_content,
    save_client_about_content,
    save_manager_about_content,
)
from .paths import CLIENT_ABOUT_CONTENT_PATH, MANAGER_ABOUT_CONTENT_PATH
from .resource_utils import _set_window_icon
from .ui_style import (
    apply_base_style,
    bordered_card,
    BG,
    CARD_BG,
    TEXT,
    MUTED,
)


# JSON 키, 화면 라벨, 입력 위젯 종류를 한 곳에 묶어 Manager/Client 탭이 같은 구조를 쓰게 한다.
CONTENT_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("app_name", "프로그램명", "entry"),
    ("app_version", "버전", "entry"),
    ("author", "제작자", "entry"),
    ("github_url", "GitHub URL", "entry"),
    ("license_name", "라이선스", "entry"),
    ("about_title", "정보 창 제목", "entry"),
    ("about_summary", "요약 설명", "text_small"),
    ("manual_text", "매뉴얼 본문", "text_large"),
)

REQUIRED_FIELDS = ("app_name", "app_version", "about_title")
"""정보 창이 최소한의 제목과 버전 정보를 잃지 않도록 저장 전에 검사하는 필수 필드."""


class AboutEditorDialog(tk.Toplevel):
    """Manager 정보와 Client 배포용 정보를 같은 화면에서 편집한다.

    관리자가 배포 후에도 프로그램 정보와 매뉴얼 문구를 JSON 파일만으로 수정할 수 있게 한다.
    """

    def __init__(self, master: tk.Misc) -> None:
        """객체가 사용할 상태와 UI 구성 요소를 초기화한다."""
        super().__init__(master)
        self.title("프로그램 정보 편집")
        self.geometry("760x720")
        self.minsize(700, 620)
        self.icon_image = _set_window_icon(self)

        self._manager_widgets: dict[str, ttk.Entry | ScrolledText] = {}
        self._client_widgets: dict[str, ttk.Entry | ScrolledText] = {}

        apply_base_style(self)
        self.configure(bg=BG)

        root = ttk.Frame(self, padding=18)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        ttk.Label(root, text="프로그램 정보 편집", style="DialogTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            root,
            text="Manager에 표시할 정보와 Client에 배포할 정보를 수정합니다.",
            style="DialogSubtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=2, column=0, sticky="nsew")

        manager_tab = ttk.Frame(self.notebook, padding=12)
        client_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(manager_tab, text="Manager 정보")
        self.notebook.add(client_tab, text="Client 정보")

        self._build_content_tab(
            manager_tab,
            load_manager_about_content(),
            self._manager_widgets,
            file_label=f"저장 파일: {MANAGER_ABOUT_CONTENT_PATH}",
        )
        self._build_content_tab(
            client_tab,
            load_client_about_content(),
            self._client_widgets,
            file_label=f"저장 파일: {CLIENT_ABOUT_CONTENT_PATH}",
        )

        buttons = ttk.Frame(root)
        buttons.grid(row=3, column=0, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="취소", command=self._cancel).pack(side=tk.LEFT)
        ttk.Button(buttons, text="저장", style="Primary.TButton", command=self._save).pack(side=tk.LEFT, padx=(8, 0))

        self.bind("<Escape>", lambda _event: self._cancel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.transient(master)
        self.grab_set()
        self.update_idletasks()
        self._center_on_master(master)

    def _build_content_tab(
        self,
        parent: ttk.Frame,
        content: Mapping[str, str],
        widget_map: dict[str, ttk.Entry | ScrolledText],
        *,
        file_label: str,
    ) -> None:
        """프로그램 정보 필드를 Entry와 ScrolledText로 구성한다."""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        outer, card = bordered_card(parent, padding=14)
        outer.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(1, weight=1)
        
        ttk.Label(card, text=file_label, style="Muted.TLabel").grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 10),
        )

        row = 1
        for key, label, field_type in CONTENT_FIELDS:
            ttk.Label(card, text=label, style="Card.TLabel").grid(
                row=row,
                column=0,
                sticky="nw",
                padx=(0, 10),
                pady=5,
            )

            value = content.get(key, "")
            if field_type == "entry":
                widget = ttk.Entry(card)
                widget.insert(0, value)
                widget.grid(row=row, column=1, sticky="ew", pady=5)
            else:
                height = 3 if field_type == "text_small" else 13
                widget = ScrolledText(
                    card,
                    height=height,
                    wrap="word",
                    relief="flat",
                    borderwidth=1,
                    background=CARD_BG,
                    foreground=TEXT,
                    insertbackground=TEXT,
                    font=("맑은 고딕", 10),
                )
                widget.insert("1.0", value)
                widget.grid(row=row, column=1, sticky="nsew" if field_type == "text_large" else "ew", pady=5)
                if field_type == "text_large":
                    card.rowconfigure(row, weight=1)

            widget_map[key] = widget
            row += 1

        ttk.Label(
            card,
            text="프로그램명, 버전, 정보 창 제목은 비워둘 수 없습니다.",
            style="Muted.TLabel",
            foreground=MUTED,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _center_on_master(self, master: tk.Misc) -> None:
        """대화상자를 부모 창 중앙 근처에 배치한다."""
        try:
            x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
            y = master.winfo_rooty() + (master.winfo_height() - self.winfo_height()) // 2
            self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        except tk.TclError:
            pass

    def _read_widgets(self, widget_map: Mapping[str, ttk.Entry | ScrolledText]) -> dict[str, str]:
        """편집 위젯에서 저장할 문자열 값을 수집한다."""
        values: dict[str, str] = {}
        for key, widget in widget_map.items():
            if isinstance(widget, ScrolledText):
                values[key] = widget.get("1.0", "end-1c").strip()
            else:
                values[key] = widget.get().strip()
        return values

    def _validate(self, label: str, values: Mapping[str, str]) -> bool:
        """프로그램 정보 필수값이 비어 있는지 확인한다."""
        missing = [key for key in REQUIRED_FIELDS if not values.get(key, "").strip()]
        if missing:
            field_names = {
                "app_name": "프로그램명",
                "app_version": "버전",
                "about_title": "정보 창 제목",
            }
            missing_labels = ", ".join(field_names[key] for key in missing)
            messagebox.showerror(
                "입력 오류",
                f"{label}의 필수값을 입력하세요: {missing_labels}",
                parent=self,
            )
            return False
        return True

    def _save(self) -> None:
        """Manager/Client 프로그램 정보를 각각 JSON 파일에 저장한다."""
        manager_content = self._read_widgets(self._manager_widgets)
        client_content = self._read_widgets(self._client_widgets)

        if not self._validate("Manager 정보", manager_content):
            self.notebook.select(0)
            return
        if not self._validate("Client 정보", client_content):
            self.notebook.select(1)
            return

        try:
            save_manager_about_content(manager_content)
            save_client_about_content(client_content)
        except Exception as exc:
            messagebox.showerror("저장 실패", f"프로그램 정보 저장에 실패했습니다.\n{exc}", parent=self)
            return

        messagebox.showinfo(
            "저장 완료",
            "프로그램 정보를 저장했습니다.\nClient 정보는 Client가 Manager 설정을 다시 불러올 때 반영됩니다.",
            parent=self,
        )
        self.destroy()

    def _cancel(self) -> None:
        """프로그램 정보 편집을 저장하지 않고 닫는다."""
        self.destroy()
