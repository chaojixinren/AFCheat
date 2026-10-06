"""主窗口：装配标题区与各功能面板。"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage

from .. import constants as C
from ..core import process as process_core
from ..core.game import AmazingFrogCheat
from .styles import setup_styles
from .title_section import build_title_section
from .process_panel import ProcessPanel
from .cheat_panel import CheatPanel


def _resource_dir() -> str:
    """资源目录：打包后为解包目录，否则为项目根。

    源码运行时本文件位于 <root>/afcheat/ui/app.py，向上三级即项目根；
    PyInstaller 冻结后资源被解包到 sys._MEIPASS。
    """
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AmazingFrogCheatGUI(tk.Tk):
    """Amazing Frog 修改器 GUI 主窗口"""

    def __init__(self):
        super().__init__()

        self.title(C.WINDOW_TITLE)
        self.geometry(C.WINDOW_SIZE)
        self.minsize(*C.WINDOW_MINSIZE)
        self.resizable(True, True)
        self.configure(bg=C.COLOR_BG)

        # 窗口图标
        try:
            self.iconbitmap(os.path.join(_resource_dir(), "icon.ico"))
        except Exception:
            pass

        setup_styles()
        self._load_assets()

        # 核心逻辑与共享状态
        self.cheat = AmazingFrogCheat()
        self.status_var = tk.StringVar(value="就绪")

        self._build_ui()
        self.check_dependencies()

    # ------------------------------------------------------------------ 资源
    def _load_assets(self):
        """加载 UI 资源（封面图）；图片过大时自动缩小。"""
        self.hero_image = None
        img_path = os.path.join(_resource_dir(), "amazingfrog.png")
        if os.path.exists(img_path):
            try:
                img = PhotoImage(file=img_path)
                max_width = 300
                if img.width() > max_width:
                    scale = (img.width() + max_width - 1) // max_width  # 向上取整
                    img = img.subsample(scale, scale)
                self.hero_image = img
            except Exception as exc:
                print(f"[ui] 加载 amazingfrog.png 失败: {exc}")

    # ------------------------------------------------------------------ 布局
    def _on_mousewheel(self, event):
        canvas = getattr(self, "_scroll_canvas", None)
        if canvas is None:
            return
        try:
            widget_class = event.widget.winfo_class()
        except Exception:
            widget_class = ""
        if widget_class in {"Treeview", "Text", "Entry", "TEntry"}:
            return
        delta = int(-1 * (event.delta / 120)) if getattr(event, "delta", 0) else 0
        if delta:
            canvas.yview_scroll(delta, "units")

    def _build_ui(self):
        """构建用户界面"""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll_root = ttk.Frame(self, style="Main.TFrame")
        scroll_root.grid(row=0, column=0, sticky="nsew")
        scroll_root.columnconfigure(0, weight=1)
        scroll_root.rowconfigure(0, weight=1)

        self._scroll_canvas = tk.Canvas(scroll_root, bg=C.COLOR_BG, highlightthickness=0)
        v_scroll = ttk.Scrollbar(scroll_root, orient="vertical", command=self._scroll_canvas.yview)
        self._scroll_canvas.configure(yscrollcommand=v_scroll.set)

        self._scroll_canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        content = ttk.Frame(self._scroll_canvas, style="Main.TFrame")
        self._scroll_content = content
        window_id = self._scroll_canvas.create_window((0, 0), window=content, anchor="nw")

        def _on_content_configure(_event):
            self._scroll_canvas.configure(scrollregion=self._scroll_canvas.bbox("all"))

        def _on_canvas_configure(event):
            self._scroll_canvas.itemconfigure(window_id, width=event.width)

        content.bind("<Configure>", _on_content_configure)
        self._scroll_canvas.bind("<Configure>", _on_canvas_configure)
        self.bind_all("<MouseWheel>", self._on_mousewheel)

        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=0)  # 标题区域
        content.rowconfigure(1, weight=0)  # 进程选择面板
        content.rowconfigure(2, weight=0)  # 游戏修改面板

        build_title_section(content, self.hero_image)
        self.process_panel = ProcessPanel(content, self.cheat, self.status_var)
        self.cheat_panel = CheatPanel(content, self.cheat, self.status_var)

    # ------------------------------------------------------------------ 依赖
    def check_dependencies(self):
        """检查必要依赖"""
        if process_core.psutil is None:
            messagebox.showerror(
                "缺少依赖",
                "未找到 psutil 依赖。\n\n"
                "请执行：pip install psutil\n"
                "进程枚举功能需要此依赖。"
            )
            return

        self.process_panel.refresh()
