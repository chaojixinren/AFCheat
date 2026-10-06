"""可复用的界面组件。"""

import tkinter as tk
from typing import Tuple

from .. import constants as C


def card(parent: tk.Misc, icon: str, title: str, row: int,
         pady=(0, 15)) -> Tuple[tk.Frame, tk.Frame]:
    """构建一个「白底卡片 + 灰底标题栏 + 内容区」容器。

    返回 (卡片外层, 内容区)。调用方把控件放进内容区即可。

    原先在进程面板和修改面板里各重复了一遍完全相同的样板代码，
    这里统一成一处。
    """
    card_frame = tk.Frame(parent, bg=C.COLOR_CARD, relief='flat', bd=0)
    card_frame.grid(row=row, column=0, sticky="ew", padx=15, pady=pady)
    card_frame.columnconfigure(0, weight=1)

    header = tk.Frame(card_frame, bg=C.COLOR_SUBTLE, relief='flat', bd=0)
    header.pack(fill='x')

    tk.Label(
        header,
        text=f"{icon} {title}",
        font=(C.FONT_FAMILY, 13, 'bold'),
        fg=C.COLOR_TEXT_STRONG,
        bg=C.COLOR_SUBTLE,
        anchor='w',
        padx=20,
        pady=12,
    ).pack(fill='x')

    content = tk.Frame(card_frame, bg=C.COLOR_CARD)
    content.pack(fill='both', expand=True, padx=20, pady=20)
    content.columnconfigure(0, weight=1)

    return card_frame, content
