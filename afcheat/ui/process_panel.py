"""进程选择面板：枚举、搜索、选择并验证游戏进程。"""

import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from .. import constants as C
from ..core import process as process_core
from .widgets import card

logger = logging.getLogger(__name__)


class ProcessPanel:
    """包裹进程列表相关的一整套控件与交互。"""

    def __init__(self, parent: tk.Misc, cheat, status_var: tk.StringVar):
        self.parent = parent
        self.cheat = cheat
        self.status_var = status_var

        self.process_list = []
        self.filtered_process_list = []
        self.process_search_var = tk.StringVar()
        self.selected_process_var = tk.StringVar(value="未选择进程")
        self._process_list_collapsed = False

        self._build()

    # ------------------------------------------------------------------ 构建
    def _build(self):
        _, process_frame = card(self.parent, "🎯", "进程选择与管理", row=1)

        # 控制按钮组
        control_frame = tk.Frame(process_frame, bg=C.COLOR_CARD)
        control_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        btn_frame = tk.Frame(control_frame, bg=C.COLOR_CARD)
        btn_frame.pack()

        self.refresh_btn = ttk.Button(btn_frame, text="刷新进程列表",
                                      command=self.refresh, style='Primary.TButton')
        self.refresh_btn.pack(side='left', padx=(0, 15))

        self.auto_find_btn = ttk.Button(btn_frame, text="自动查找游戏",
                                        command=self._auto_find_game_process, style='Success.TButton')
        self.auto_find_btn.pack(side='left', padx=(0, 15))

        self.validate_btn = ttk.Button(btn_frame, text="验证游戏进程",
                                       command=self._validate_selected_process, style='Warning.TButton')
        self.validate_btn.pack(side='left', padx=(0, 15))

        self.toggle_process_list_btn = ttk.Button(btn_frame, text="收起进程列表",
                                                  command=self._toggle_process_list, style='Primary.TButton')
        self.toggle_process_list_btn.pack(side='left')

        # 当前选择显示
        selection_frame = tk.Frame(process_frame, bg=C.COLOR_SUBTLE, relief='flat', bd=0)
        selection_frame.grid(row=1, column=0, columnspan=3, pady=(0, 15), sticky='ew')

        tk.Label(selection_frame, text="当前选择：", font=(C.FONT_FAMILY, 11, 'bold'),
                 fg=C.COLOR_TEXT_STRONG, bg=C.COLOR_SUBTLE).pack(side='left', padx=12, pady=10)
        tk.Label(selection_frame, textvariable=self.selected_process_var,
                 font=(C.FONT_FAMILY, 11, 'bold'), fg=C.COLOR_ACCENT,
                 bg=C.COLOR_SUBTLE).pack(side='left', padx=(0, 12), pady=10)

        # 搜索框
        search_container = tk.Frame(process_frame, bg=C.COLOR_CARD)
        search_container.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        self.process_search_container = search_container

        search_frame = tk.Frame(search_container, bg=C.COLOR_CARD)
        search_frame.pack(fill='x', pady=5)
        search_frame.columnconfigure(1, weight=1)

        search_label_frame = tk.Frame(search_frame, bg=C.COLOR_CARD)
        search_label_frame.grid(row=0, column=0, sticky="w", padx=(0, 10))

        tk.Label(search_label_frame, text="🔍", font=(C.FONT_EMOJI, 14),
                 bg=C.COLOR_CARD).pack(side='left', padx=(0, 6))
        tk.Label(search_label_frame, text="搜索进程：", font=(C.FONT_FAMILY, 11, 'bold'),
                 fg=C.COLOR_TEXT_STRONG, bg=C.COLOR_CARD).pack(side='left')

        process_search_entry = ttk.Entry(search_frame, textvariable=self.process_search_var,
                                         font=(C.FONT_FAMILY, 10), width=35)
        process_search_entry.grid(row=0, column=1, sticky="ew")
        process_search_entry.bind("<KeyRelease>", lambda e: self._filter_processes())

        # 进程列表
        list_container = tk.Frame(process_frame, bg=C.COLOR_CARD)
        list_container.grid(row=3, column=0, columnspan=3, sticky="ew")
        self.process_list_container = list_container

        list_title_frame = tk.Frame(list_container, bg=C.COLOR_SUBTLE, relief='flat', bd=0)
        list_title_frame.pack(fill='x', pady=(0, 8))

        tk.Label(list_title_frame, text="📋", font=(C.FONT_EMOJI, 14),
                 bg=C.COLOR_SUBTLE).pack(side='left', padx=(12, 8), pady=10)
        tk.Label(list_title_frame, text="运行中的进程列表", font=(C.FONT_FAMILY, 11, 'bold'),
                 fg=C.COLOR_TEXT_STRONG, bg=C.COLOR_SUBTLE).pack(side='left', pady=10)

        process_list_frame = tk.Frame(list_container, bg=C.COLOR_CARD)
        process_list_frame.pack(fill='both', expand=True)
        process_list_frame.columnconfigure(0, weight=1)
        process_list_frame.rowconfigure(0, weight=1)

        columns = ("pid", "name", "memory", "path")
        self.process_tree = ttk.Treeview(process_list_frame, columns=columns,
                                         show="headings", height=8, selectmode='browse')
        self.process_tree.tag_configure('oddrow', background=C.COLOR_ROW_ALT)

        self.process_tree.heading("pid", text="PID", anchor='center')
        self.process_tree.heading("name", text="进程名称")
        self.process_tree.heading("memory", text="内存使用")
        self.process_tree.heading("path", text="文件路径")

        self.process_tree.column("pid", width=80, anchor="center", stretch=False)
        self.process_tree.column("name", width=180, anchor="w", stretch=False)
        self.process_tree.column("memory", width=100, anchor="center", stretch=False)
        self.process_tree.column("path", width=400, anchor="w", stretch=True)

        process_v_scrollbar = ttk.Scrollbar(process_list_frame, orient="vertical",
                                            command=self.process_tree.yview)
        process_h_scrollbar = ttk.Scrollbar(process_list_frame, orient="horizontal",
                                            command=self.process_tree.xview)
        self.process_tree.configure(yscrollcommand=process_v_scrollbar.set,
                                    xscrollcommand=process_h_scrollbar.set)

        self.process_tree.grid(row=0, column=0, sticky="nsew")
        process_v_scrollbar.grid(row=0, column=1, sticky="ns")
        process_h_scrollbar.grid(row=1, column=0, sticky="ew")

        self.process_tree.bind("<<TreeviewSelect>>", self._on_process_select)
        self.process_tree.bind("<ButtonRelease-1>", self._on_process_select)

    # ------------------------------------------------------------------ 数据
    def refresh(self):
        """刷新进程列表"""
        try:
            self.process_list = process_core.enumerate_processes()
            self._filter_processes()
            self.status_var.set(f"🔄 已刷新进程列表，共发现 {len(self.process_list)} 个进程")
        except Exception as e:
            logger.exception("刷新进程列表失败")
            self.status_var.set(f"❌ 刷新进程列表失败: {e}")

    def _filter_processes(self):
        """根据搜索关键词过滤进程"""
        query = self.process_search_var.get().strip().lower()
        if not query:
            self.filtered_process_list = self.process_list
        else:
            self.filtered_process_list = [
                p for p in self.process_list
                if query in p.name.lower() or
                   query in str(p.pid) or
                   query in p.exe_path.lower()
            ]
        self._display_processes()

    def _display_processes(self):
        """显示进程列表"""
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)

        for idx, process in enumerate(self.filtered_process_list):
            self.process_tree.insert(
                "", "end",
                values=(process.pid, process.name, process.memory_info, process.exe_path),
                tags=('oddrow',) if (idx % 2) else ()
            )

    def _on_process_select(self, event):
        """处理进程选择事件"""
        try:
            selection = self.process_tree.selection()
            if not selection:
                return
            values = self.process_tree.item(selection[0]).get("values") or []
            if len(values) < 2:
                return
            self._select_process(int(values[0]), str(values[1]))
        except Exception as e:
            self.status_var.set(f"❌ 选择进程失败: {e}")

    # ------------------------------------------------------------------ 交互
    def _select_process(self, pid: int, name: str):
        """设置当前目标进程，并异步验证是否为游戏进程（避免卡 UI）"""
        self.cheat.set_target_process(pid, name)
        self.selected_process_var.set(f"已选择: {name} (PID: {pid})")
        self.status_var.set("正在验证进程是否为游戏…")

        def worker():
            try:
                is_valid_game = self.cheat.validate_game_process(pid)
            except Exception:
                logger.exception("验证进程 %s 失败", pid)
                is_valid_game = False

            def update_ui():
                if is_valid_game:
                    self.selected_process_var.set(f"已选择: {name} (PID: {pid})")
                    self.status_var.set("已选择有效的游戏进程，可以开始修改！")
                    self._set_process_list_collapsed(True)
                else:
                    self.selected_process_var.set(f"⚠️ 已选择: {name} (PID: {pid}) - 非游戏进程/无法验证")
                    self.status_var.set("⚠️ 警告：选择的进程不包含 GameAssembly.dll，可能不是 Amazing Frog。")

            self.parent.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def _validate_selected_process(self):
        """验证当前选择的进程"""
        if self.cheat.selected_pid is None:
            messagebox.showwarning("未选择进程", "请先从进程列表中选择一个进程。")
            return

        self.status_var.set("正在验证进程...")
        is_valid = self.cheat.validate_game_process(self.cheat.selected_pid)

        if is_valid:
            self.status_var.set("✅ 验证成功：这是一个有效的Amazing Frog游戏进程")
            messagebox.showinfo("验证成功", "当前选择的进程是有效的Amazing Frog游戏进程。")
        else:
            self.status_var.set("❌ 验证失败：这不是一个有效的游戏进程")
            messagebox.showerror("验证失败", "当前选择的进程不包含GameAssembly.dll，\n可能不是Amazing Frog游戏进程。")

    def _auto_find_game_process(self):
        """自动查找游戏进程"""
        self.status_var.set("正在搜索游戏进程...")

        game_processes = [p for p in self.process_list if self.cheat.validate_game_process(p.pid)]

        if not game_processes:
            self.status_var.set("❌ 未找到游戏进程")
            messagebox.showwarning("未找到游戏进程",
                                   "未找到包含GameAssembly.dll的进程。\n请确保游戏正在运行，然后刷新进程列表。")
        elif len(game_processes) == 1:
            process = game_processes[0]
            self._select_process(process.pid, process.name)
            messagebox.showinfo("自动查找成功",
                                f"已自动选择游戏进程：\n{process.name} (PID: {process.pid})")
        else:
            self.status_var.set(f"找到 {len(game_processes)} 个游戏进程，请手动选择")
            messagebox.showinfo("找到多个游戏进程",
                                f"找到 {len(game_processes)} 个可能的游戏进程，\n请从列表中选择一个。")

    # ------------------------------------------------------------------ 折叠
    def _set_process_list_collapsed(self, collapsed: bool):
        if collapsed:
            self.process_search_container.grid_remove()
            self.process_list_container.grid_remove()
            self._process_list_collapsed = True
            self.toggle_process_list_btn.configure(text="📂 展开进程列表")
        else:
            self.process_search_container.grid()
            self.process_list_container.grid()
            self._process_list_collapsed = False
            self.toggle_process_list_btn.configure(text="📂 收起进程列表")

    def _toggle_process_list(self):
        self._set_process_list_collapsed(not self._process_list_collapsed)
