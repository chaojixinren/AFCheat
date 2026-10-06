"""顶部标题区：封面图 + 标题 + 作者信息条。"""

import tkinter as tk
from typing import Optional

from .. import constants as C


def build_title_section(parent: tk.Misc, hero_image: Optional[tk.PhotoImage]) -> None:
    """在 parent 的第 0 行构建标题卡片。"""
    title_card = tk.Frame(parent, bg=C.COLOR_CARD, relief='flat', bd=0)
    title_card.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
    title_card.columnconfigure(1, weight=1)

    title_frame = tk.Frame(title_card, bg=C.COLOR_CARD)
    title_frame.pack(fill='both', expand=True, padx=25, pady=20)

    # 左侧封面图（无图时用 🐸 占位）
    hero_container = tk.Frame(title_frame, bg=C.COLOR_SUBTLE, relief='flat', bd=0)
    hero_container.grid(row=0, column=0, sticky="nw", padx=(0, 25))

    hero = tk.Frame(hero_container, bg=C.COLOR_SUBTLE, bd=0)
    hero.pack(padx=8, pady=8)

    if hero_image:
        tk.Label(hero, image=hero_image, bg=C.COLOR_SUBTLE, bd=0).pack()
    else:
        tk.Label(hero, text="🐸", font=(C.FONT_EMOJI, 48),
                 bg=C.COLOR_SUBTLE, fg=C.COLOR_ACCENT).pack()

    # 右侧信息区
    info = tk.Frame(title_frame, bg=C.COLOR_CARD)
    info.grid(row=0, column=1, sticky="ew")
    info.columnconfigure(0, weight=1)

    tk.Label(info, text="AFCheat", font=(C.FONT_FAMILY, 24, 'bold'),
             fg=C.COLOR_TEXT, bg=C.COLOR_CARD, anchor='w'
             ).grid(row=0, column=0, sticky="w", pady=(0, 8))

    tk.Label(info, text="先选择 / 验证 Amazing Frog 进程，再使用下方功能按钮。",
             font=(C.FONT_FAMILY, 11), fg=C.COLOR_TEXT_MUTED, bg=C.COLOR_CARD, anchor='w'
             ).grid(row=1, column=0, sticky="w", pady=(0, 15))

    author_bar = tk.Frame(info, bg=C.COLOR_SUBTLE_ALT, relief='flat', bd=0)
    author_bar.grid(row=2, column=0, sticky="ew")

    tk.Label(author_bar, text=C.AUTHOR_INFO, font=(C.FONT_FAMILY, 9),
             bg=C.COLOR_SUBTLE_ALT, fg=C.COLOR_TEXT_SOFT, anchor='w', padx=12, pady=8
             ).pack(fill='x')
