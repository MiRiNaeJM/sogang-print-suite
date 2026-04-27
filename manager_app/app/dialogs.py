"""Manager에서 사용하는 간단한 비밀번호 입력 대화상자 모듈.

관리 기능 진입처럼 짧은 인증 입력이 필요한 경우 재사용할 수 있게 분리한다.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .resource_utils import _set_window_icon
from .ui_style import apply_base_style, bordered_card, BG


class PasswordDialog(tk.Toplevel):
    """관리자 기능 진입 시 비밀번호를 입력받는 간단한 대화상자."""
    def __init__(self, master: tk.Misc, title: str, message: str) -> None:
        """객체가 사용할 상태와 UI 구성 요소를 초기화한다."""
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.result: str | None = None
        self.icon_image = _set_window_icon(self)

        apply_base_style(self)
        self.configure(bg=BG)
        self.password_var = tk.StringVar()

        frm = ttk.Frame(self, padding=18)
        frm.pack(fill=tk.BOTH, expand=True)
        frm.columnconfigure(0, weight=1)

        ttk.Label(frm, text=title, style="DialogTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(frm, text=message, style="DialogSubtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 14))

        card_outer, card = bordered_card(frm, padding=14)
        card_outer.grid(row=2, column=0, sticky="ew")
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="비밀번호", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 12))
        entry = ttk.Entry(card, textvariable=self.password_var, show="*", width=28)
        entry.grid(row=0, column=1, sticky="ew")

        buttons = ttk.Frame(frm)
        buttons.grid(row=3, column=0, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="취소", command=self.cancel).pack(side=tk.LEFT)
        ttk.Button(buttons, text="확인", style="Primary.TButton", command=self.ok).pack(side=tk.LEFT, padx=(8, 0))

        self.bind("<Return>", lambda _event: self.ok())
        self.bind("<Escape>", lambda _event: self.cancel())
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.transient(master)
        self.grab_set()
        entry.focus_set()
        self.update_idletasks()
        self._center_on_master(master)

    def _center_on_master(self, master: tk.Misc) -> None:
        """대화상자를 부모 창 중앙 근처에 배치한다."""
        try:
            x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
            y = master.winfo_rooty() + (master.winfo_height() - self.winfo_height()) // 2
            self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        except tk.TclError:
            pass

    def ok(self) -> None:
        """입력된 비밀번호를 결과값으로 저장하고 대화상자를 닫는다."""
        self.result = self.password_var.get()
        self.destroy()

    def cancel(self) -> None:
        """변경 내용을 저장하지 않고 대화상자를 닫는다."""
        self.result = None
        self.destroy()
