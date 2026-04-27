"""Manager의 프로그램 정보 창을 구성하는 Tkinter 대화상자 모듈.

창을 열 때마다 JSON을 다시 읽어 관리자가 수정한 최신 정보를 보여준다.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from typing import Mapping, Any
import webbrowser

from .about_content_loader import load_manager_about_content
from .resource_utils import _set_window_icon
from .ui_style import apply_base_style, bordered_card, BG, CARD_BG, TEXT


class AboutDialog(tk.Toplevel):
    """프로그램 정보와 매뉴얼을 사용자가 읽을 수 있게 표시하는 대화상자."""
    def __init__(self, master: tk.Misc, content: Mapping[str, Any] | None = None) -> None:
        """객체가 사용할 상태와 UI 구성 요소를 초기화한다."""
        super().__init__(master)
        self.content = load_manager_about_content()
        if content:
            for key, value in content.items():
                if isinstance(value, str) and key in self.content:
                    self.content[key] = value.strip()
        self.title(self.content["about_title"])
        self.geometry("620x620")
        self.minsize(560, 520)
        self.icon_image = _set_window_icon(self)

        apply_base_style(self)
        self.configure(bg=BG)

        frm = ttk.Frame(self, padding=18)
        frm.pack(fill=tk.BOTH, expand=True)
        frm.columnconfigure(0, weight=1)
        frm.rowconfigure(2, weight=1)

        ttk.Label(frm, text=self.content["app_name"], style="DialogTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(frm, text=f"Version {self.content['app_version']}", style="DialogSubtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 12))

        outer, card = bordered_card(frm, padding=14)
        outer.grid(row=2, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        meta = (
            f"{self.content['about_summary']}\n\n"
            f"제작자: {self.content['author']}\n"
            f"GitHub: {self.content['github_url']}\n"
            f"License: {self.content['license_name']}\n\n"
        )
        ttk.Label(card, text="프로그램 정보 / Manual", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.text = ScrolledText(
            card,
            wrap="word",
            relief="flat",
            borderwidth=0,
            background=CARD_BG,
            foreground=TEXT,
            insertbackground=TEXT,
            font=("맑은 고딕", 10),
        )
        self.text.grid(row=1, column=0, sticky="nsew")
        self.text.insert("1.0", meta + self.content["manual_text"])
        self.text.configure(state=tk.DISABLED)

        buttons = ttk.Frame(frm)
        buttons.grid(row=3, column=0, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="GitHub 열기", command=self.open_github).pack(side=tk.LEFT)
        ttk.Button(buttons, text="링크 복사", command=self.copy_github).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(buttons, text="닫기", style="Primary.TButton", command=self.destroy).pack(side=tk.LEFT, padx=(8, 0))

        self.transient(master)
        self.grab_set()
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

    def open_github(self) -> None:
        """설정된 GitHub 주소를 기본 브라우저로 연다."""
        github_url = self.content.get("github_url", "")
        if github_url and "OWNER/REPOSITORY" not in github_url:
            webbrowser.open(github_url)
        else:
            messagebox.showinfo("GitHub", "GitHub 주소를 manager_about_content.json 또는 about_content.py에서 수정하세요.", parent=self)

    def copy_github(self) -> None:
        """프로그램 정보의 GitHub 주소를 클립보드에 복사한다."""
        github_url = self.content.get("github_url", "")
        self.clipboard_clear()
        self.clipboard_append(github_url)
        messagebox.showinfo("복사 완료", "GitHub 링크를 클립보드에 복사했습니다.", parent=self)
