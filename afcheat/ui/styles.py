"""ttk 主题与控件样式。"""

from tkinter import ttk

from .. import constants as C


def _register_button_style(style: ttk.Style, name: str, colors) -> None:
    """按主题色注册一个扁平圆角按钮样式。colors = (底色, 悬停, 按下)"""
    base, active, pressed = colors
    style.configure(
        f'{name}.TButton',
        background=base,
        foreground='white',
        font=(C.FONT_FAMILY, 10, 'bold'),
        padding=(20, 10),
        relief='flat',
        borderwidth=0,
    )
    style.map(
        f'{name}.TButton',
        background=[('active', active), ('pressed', pressed)],
        foreground=[('active', 'white'), ('pressed', 'white')],
    )


def setup_styles() -> None:
    """设置 GUI 样式"""
    style = ttk.Style()

    # 使用 clam 主题，更现代
    try:
        style.theme_use('clam')
    except Exception:
        pass

    # 功能按钮配色
    _register_button_style(style, 'Success', C.COLOR_SUCCESS)
    _register_button_style(style, 'Primary', C.COLOR_PRIMARY)
    _register_button_style(style, 'Warning', C.COLOR_WARNING)
    _register_button_style(style, 'Danger', C.COLOR_DANGER)

    # 标签样式
    style.configure('Title.TLabel', font=(C.FONT_FAMILY, 18, 'bold'), foreground=C.COLOR_TEXT)
    style.configure('Subtitle.TLabel', font=(C.FONT_FAMILY, 10), foreground=C.COLOR_TEXT_MUTED)
    style.configure('Accent.TLabel', font=(C.FONT_FAMILY, 10, 'bold'), foreground=C.COLOR_ACCENT)
    style.configure('Header.TLabel', font=(C.FONT_FAMILY, 12, 'bold'), foreground=C.COLOR_TEXT_STRONG)
    style.configure('Status.TLabel', font=(C.FONT_MONO, 9), foreground=C.COLOR_STATUS)

    # 卡片容器
    style.configure('Card.TLabelframe', background=C.COLOR_CARD, relief='flat', borderwidth=0, padding=15)
    style.configure('Card.TLabelframe.Label', background=C.COLOR_CARD, foreground=C.COLOR_TEXT_STRONG,
                    font=(C.FONT_FAMILY, 11, 'bold'))

    # 常用容器 Frame
    style.configure('Card.TFrame', background=C.COLOR_CARD)
    style.configure('Main.TFrame', background=C.COLOR_BG)

    # 表格
    style.configure('Treeview', background=C.COLOR_CARD, fieldbackground=C.COLOR_CARD,
                    foreground=C.COLOR_TEXT_STRONG, font=(C.FONT_FAMILY, 9), rowheight=28)
    style.map('Treeview', background=[('selected', C.COLOR_ROW_SELECT)])

    style.configure('Treeview.Heading', background=C.COLOR_SUBTLE_ALT, foreground=C.COLOR_TEXT_STRONG,
                    font=(C.FONT_FAMILY, 9, 'bold'), relief='flat')

    # 输入框
    style.configure('TEntry', font=(C.FONT_FAMILY, 10), relief='flat', borderwidth=2,
                    fieldbackground=C.COLOR_SUBTLE, bordercolor=C.COLOR_BORDER, padding=8)
    style.map('TEntry', bordercolor=[('focus', C.COLOR_ACCENT)],
              fieldbackground=[('focus', C.COLOR_CARD)])
