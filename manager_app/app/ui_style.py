"""Manager Tkinter UI 스타일을 한 곳에서 정의하는 모듈.

관리자 화면의 색상, 카드, 버튼, 라벨 스타일을 중앙화해 화면 간 일관성을 유지한다.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


FONT_FAMILY = "맑은 고딕"

BG = "#EEF3F8"
CARD_BG = "#FFFFFF"
PANEL_BG = "#F8FAFC"
BORDER = "#D8E0EA"
TEXT = "#0F172A"
MUTED = "#667085"
PRIMARY = "#2563EB"
PRIMARY_HOVER = "#1D4ED8"
SUCCESS = "#16A34A"
SUCCESS_BG = "#DCFCE7"
SUCCESS_FG = "#166534"
WARNING = "#D97706"
DANGER = "#DC2626"
DANGER_BG = "#FEE2E2"
DANGER_FG = "#991B1B"


def apply_base_style(root: tk.Misc) -> None:
    """앱 전체에서 사용할 ttk 스타일을 루트 윈도우에 등록한다."""
    try:
        root.configure(bg=BG)
    except tk.TclError:
        pass

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", font=(FONT_FAMILY, 10))

    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD_BG, relief="flat", borderwidth=0)
    style.configure("Inner.TFrame", background=CARD_BG, relief="flat", borderwidth=0)
    style.configure("Panel.TFrame", background=PANEL_BG, relief="flat", borderwidth=0)

    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT)
    style.configure("Panel.TLabel", background=PANEL_BG, foreground=TEXT)
    style.configure("Muted.TLabel", background=CARD_BG, foreground=MUTED)
    style.configure("PanelMuted.TLabel", background=PANEL_BG, foreground=MUTED)

    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=(FONT_FAMILY, 21, "bold"))
    style.configure("Subtitle.TLabel", background=BG, foreground=MUTED, font=(FONT_FAMILY, 11))
    style.configure("SectionTitle.TLabel", background=CARD_BG, foreground=TEXT, font=(FONT_FAMILY, 12, "bold"))
    style.configure("DialogTitle.TLabel", background=BG, foreground=TEXT, font=(FONT_FAMILY, 14, "bold"))
    style.configure("DialogSubtitle.TLabel", background=BG, foreground=MUTED, font=(FONT_FAMILY, 10))
    style.configure("Value.TLabel", background=CARD_BG, foreground=TEXT, font=(FONT_FAMILY, 22, "bold"))

    style.configure("TEntry", padding=(6, 4), fieldbackground="#FFFFFF", foreground=TEXT)

    style.configure("TButton", padding=(12, 7), font=(FONT_FAMILY, 10), background="#FFFFFF", foreground=TEXT)
    style.map("TButton", background=[("active", "#F3F4F6")])

    style.configure(
        "Primary.TButton",
        padding=(14, 7),
        font=(FONT_FAMILY, 10, "bold"),
        background=PRIMARY,
        foreground="#FFFFFF",
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Primary.TButton",
        background=[("active", PRIMARY_HOVER), ("pressed", PRIMARY_HOVER), ("disabled", "#CBD5E1")],
        foreground=[("disabled", "#F8FAFC")],
    )

    style.configure(
        "Danger.TButton",
        padding=(14, 7),
        font=(FONT_FAMILY, 10, "bold"),
        background="#FFFFFF",
        foreground=DANGER_FG,
    )
    style.map("Danger.TButton", background=[("active", DANGER_BG), ("pressed", DANGER_BG)])

    style.configure("Treeview", rowheight=28, font=(FONT_FAMILY, 10), background="#FFFFFF", fieldbackground="#FFFFFF")
    style.configure("Treeview.Heading", font=(FONT_FAMILY, 10, "bold"), background="#E9EEF5", foreground=TEXT)


def bordered_card(parent: tk.Misc, *, padding: int = 16) -> tuple[tk.Frame, ttk.Frame]:
    """배경과 카드 프레임을 함께 만들어 섹션을 시각적으로 구분한다."""
    outer = tk.Frame(parent, bg=BORDER, bd=0, highlightthickness=0)
    inner = ttk.Frame(outer, style="Card.TFrame", padding=padding)
    inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    return outer, inner


def bordered_panel(parent: tk.Misc, *, padding: int = 14) -> tuple[tk.Frame, ttk.Frame]:
    """카드보다 단순한 테두리 패널 프레임을 생성한다."""
    outer = tk.Frame(parent, bg=BORDER, bd=0, highlightthickness=0)
    inner = ttk.Frame(outer, style="Panel.TFrame", padding=padding)
    inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    return outer, inner
