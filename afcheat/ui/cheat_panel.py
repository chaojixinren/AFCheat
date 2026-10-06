"""游戏修改面板：解锁皮肤、无限子弹及恢复。"""

import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from .. import constants as C
from .widgets import card

logger = logging.getLogger(__name__)


class CheatPanel:
    """包裹修改功能按钮与状态显示。"""

    def __init__(self, parent: tk.Misc, cheat, status_var: tk.StringVar):
        self.parent = parent
        self.cheat = cheat
        self.status_var = status_var

        self.unlock_btn_var = tk.StringVar(value="解锁所有皮肤")
        self.ammo_btn_var = tk.StringVar(value="启用无限子弹")

        self._build()

    # ------------------------------------------------------------------ 构建
    def _build(self):
        _, control_frame = card(self.parent, "🎮", "游戏修改功能", row=2)

        main_features_frame = tk.Frame(control_frame, bg=C.COLOR_CARD)
        main_features_frame.pack(pady=(0, 20), anchor='center')

        unlock_frame = tk.Frame(main_features_frame, bg=C.COLOR_CARD)
        unlock_frame.pack(side='left', padx=(0, 15))
        self.unlock_btn = ttk.Button(unlock_frame, textvariable=self.unlock_btn_var,
                                     command=self._unlock_costumes, style='Success.TButton')
        self.unlock_btn.pack()

        ammo_frame = tk.Frame(main_features_frame, bg=C.COLOR_CARD)
        ammo_frame.pack(side='left', padx=(0, 15))
        self.ammo_btn = ttk.Button(ammo_frame, textvariable=self.ammo_btn_var,
                                   command=self._enable_infinite_ammo, style='Success.TButton')
        self.ammo_btn.pack()

        restore_frame = tk.Frame(main_features_frame, bg=C.COLOR_CARD)
        restore_frame.pack(side='left')
        self.restore_unlock_btn = ttk.Button(restore_frame, text="恢复皮肤解锁",
                                             command=self._restore_costume_unlock_only, style='Danger.TButton')
        self.restore_unlock_btn.pack(side='left', padx=(0, 15))
        self.restore_ammo_btn = ttk.Button(restore_frame, text="恢复无限子弹",
                                           command=self._restore_infinite_ammo_only, style='Danger.TButton')
        self.restore_ammo_btn.pack(side='left')

        # 状态显示
        status_frame = tk.Frame(control_frame, bg=C.COLOR_SUBTLE, relief='flat', bd=0)
        status_frame.pack(fill='x')

        status_header = tk.Frame(status_frame, bg=C.COLOR_SUBTLE)
        status_header.pack(fill='x', padx=12, pady=(12, 8))
        tk.Label(status_header, text="📊", font=(C.FONT_EMOJI, 14),
                 bg=C.COLOR_SUBTLE).pack(side='left', padx=(0, 8))
        tk.Label(status_header, text="操作状态", font=(C.FONT_FAMILY, 11, 'bold'),
                 fg=C.COLOR_TEXT_STRONG, bg=C.COLOR_SUBTLE).pack(side='left')

        status_content = tk.Frame(status_frame, bg=C.COLOR_SUBTLE)
        status_content.pack(fill='x', padx=12, pady=(0, 12))
        tk.Label(status_content, text="当前状态：", font=(C.FONT_FAMILY, 10, 'bold'),
                 fg=C.COLOR_TEXT_STRONG, bg=C.COLOR_SUBTLE).pack(side='left', padx=(0, 8))
        tk.Label(status_content, textvariable=self.status_var, font=(C.FONT_FAMILY, 10, "bold"),
                 fg=C.COLOR_STATUS, bg=C.COLOR_SUBTLE).pack(side='left')

    # ------------------------------------------------------------------ 工具
    def _ui(self, fn):
        """把回调切回主线程执行（tkinter 非线程安全）。"""
        self.parent.after(0, fn)

    def _require_process(self) -> bool:
        if self.cheat.selected_pid is not None:
            return True
        messagebox.showwarning(
            "未选择进程",
            "请先从进程列表中选择 Amazing Frog 游戏进程。\n\n"
            "1. 确保游戏正在运行\n"
            "2. 点击'刷新进程列表'按钮\n"
            "3. 在列表中选择游戏进程\n"
            "4. 然后再尝试修改"
        )
        return False

    # ------------------------------------------------------------------ 功能
    def _unlock_costumes(self):
        """解锁所有皮肤"""
        if not self._require_process():
            return

        def worker():
            try:
                self.status_var.set("正在查找函数...")
                unlock_found, _ = self.cheat.find_functions()

                if not unlock_found:
                    self.status_var.set("❌ 未找到皮肤解锁函数")
                    self._ui(lambda: messagebox.showerror(
                        "错误", "无法找到皮肤解锁函数。\n请确保游戏正在运行且版本匹配。"))
                    return

                self.status_var.set("正在解锁所有皮肤...")
                if self.cheat.unlock_all_costumes():
                    self._ui(self._on_unlock_success)
                else:
                    self.status_var.set("❌ 解锁失败，请检查权限和游戏状态")
                    self._ui(lambda: messagebox.showerror(
                        "❌ 解锁失败", "皮肤解锁失败。\n请确保游戏正在运行并以管理员权限启动程序。"))

            except Exception as e:
                logger.exception("解锁皮肤时发生错误")
                self.status_var.set("❌ 发生错误")
                self._ui(lambda: messagebox.showerror("错误", f"解锁过程中发生错误：\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_unlock_success(self):
        self.status_var.set("🎉 恭喜！所有皮肤已成功解锁！")
        self.unlock_btn_var.set("✅ 已解锁所有皮肤")
        self.unlock_btn.configure(state="disabled")
        messagebox.showinfo("🎊 解锁成功！", "所有皮肤已成功解锁！\n请回到游戏中查看新解锁的服装！")

    def _enable_infinite_ammo(self):
        """启用无限子弹"""
        if not self._require_process():
            return

        def worker():
            try:
                self.status_var.set("正在查找函数...")
                _, ammo_found = self.cheat.find_functions()

                if not ammo_found:
                    self.status_var.set("❌ 未找到无限子弹函数")
                    self._ui(lambda: messagebox.showerror(
                        "错误", "无法找到无限子弹函数。\n请确保游戏正在运行且版本匹配。"))
                    return

                self.status_var.set("正在启用无限子弹...")
                if self.cheat.enable_infinite_ammo():
                    self._ui(self._on_ammo_success)
                else:
                    self.status_var.set("❌ 无限子弹启用失败")
                    self._ui(lambda: messagebox.showerror(
                        "❌ 启用失败", "无限子弹启用失败。\n请确保游戏正在运行并以管理员权限启动程序。"))

            except Exception as e:
                logger.exception("启用无限子弹时发生错误")
                self.status_var.set("❌ 发生错误")
                self._ui(lambda: messagebox.showerror("错误", f"启用过程中发生错误：\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_ammo_success(self):
        self.status_var.set("🔫 无限子弹已激活！尽情射击吧！")
        self.ammo_btn_var.set("✅ 无限子弹已启用")
        self.ammo_btn.configure(state="disabled")
        messagebox.showinfo("🔥 无限子弹激活！", "无限子弹功能已成功启用！\n现在你可以无限射击，尽情享受游戏！")

    def _restore_costume_unlock_only(self):
        """仅恢复“解锁全部皮肤”修改"""
        def worker():
            try:
                self.status_var.set("正在恢复皮肤解锁修改...")
                ok = self.cheat.restore_costume_unlock()
                self._ui(lambda: self._on_restore_done(
                    ok, "皮肤解锁", self.unlock_btn_var, self.unlock_btn, "解锁所有皮肤"))
            except Exception as e:
                logger.exception("恢复皮肤解锁时发生错误")
                self.status_var.set("❌ 恢复失败")
                self._ui(lambda: messagebox.showerror("错误", f"恢复皮肤解锁时发生错误：\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _restore_infinite_ammo_only(self):
        """仅恢复“无限子弹”修改"""
        def worker():
            try:
                self.status_var.set("正在恢复无限子弹修改...")
                ok = self.cheat.restore_infinite_ammo()
                self._ui(lambda: self._on_restore_done(
                    ok, "无限子弹", self.ammo_btn_var, self.ammo_btn, "启用无限子弹"))
            except Exception as e:
                logger.exception("恢复无限子弹时发生错误")
                self.status_var.set("❌ 恢复失败")
                self._ui(lambda: messagebox.showerror("错误", f"恢复无限子弹时发生错误：\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_restore_done(self, ok, label, btn_var, btn, normal_text):
        """恢复结果的统一 UI 处理。"""
        if ok:
            btn_var.set(normal_text)
            btn.configure(state="normal")
            self.status_var.set(f"✅ 已恢复{label}修改")
            messagebox.showinfo("成功", f"已恢复{label}修改。")
        else:
            self.status_var.set(f"ℹ️ 没有可恢复的{label}修改")
            messagebox.showinfo("提示", f"没有检测到可恢复的{label}修改。")
