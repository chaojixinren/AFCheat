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
        self.app_btn_var = tk.StringVar(value="解锁所有APP")
        self.toy_btn_var = tk.StringVar(value="解锁所有玩具")
        self.disk_btn_var = tk.StringVar(value="解锁所有软盘")
        self.money_btn_var = tk.StringVar(value="无限金钱")

        self._build()

    # ------------------------------------------------------------------ 构建
    def _build(self):
        _, control_frame = card(self.parent, "🎮", "游戏修改功能", row=2)

        # 功能按钮行（三列网格）
        features_frame = tk.Frame(control_frame, bg=C.COLOR_CARD)
        features_frame.pack(pady=(0, 10), anchor='center')

        self.unlock_btn = ttk.Button(features_frame, textvariable=self.unlock_btn_var,
                                     command=self._unlock_costumes, style='Success.TButton')
        self.ammo_btn = ttk.Button(features_frame, textvariable=self.ammo_btn_var,
                                   command=self._enable_infinite_ammo, style='Success.TButton')
        self.app_btn = ttk.Button(features_frame, textvariable=self.app_btn_var,
                                  command=self._unlock_apps, style='Success.TButton')
        self.toy_btn = ttk.Button(features_frame, textvariable=self.toy_btn_var,
                                  command=self._unlock_toys, style='Success.TButton')
        self.disk_btn = ttk.Button(features_frame, textvariable=self.disk_btn_var,
                                   command=self._unlock_disks, style='Success.TButton')
        self.money_btn = ttk.Button(features_frame, textvariable=self.money_btn_var,
                                    command=self._enable_infinite_money, style='Success.TButton')

        feature_btns = (self.unlock_btn, self.ammo_btn, self.app_btn,
                        self.toy_btn, self.disk_btn, self.money_btn)
        self._grid_buttons(features_frame, feature_btns)

        # 恢复按钮行（三列网格）
        restore_frame = tk.Frame(control_frame, bg=C.COLOR_CARD)
        restore_frame.pack(pady=(0, 20), anchor='center')

        self.restore_unlock_btn = ttk.Button(restore_frame, text="恢复皮肤解锁",
                                             command=self._restore_costume_unlock_only, style='Danger.TButton')
        self.restore_ammo_btn = ttk.Button(restore_frame, text="恢复无限子弹",
                                           command=self._restore_infinite_ammo_only, style='Danger.TButton')
        self.restore_app_btn = ttk.Button(restore_frame, text="恢复APP解锁",
                                          command=self._restore_app_unlock_only, style='Danger.TButton')
        self.restore_toy_btn = ttk.Button(restore_frame, text="恢复玩具解锁",
                                          command=self._restore_toys_only, style='Danger.TButton')
        self.restore_disk_btn = ttk.Button(restore_frame, text="恢复软盘解锁",
                                           command=self._restore_disks_only, style='Danger.TButton')
        self.restore_money_btn = ttk.Button(restore_frame, text="恢复无限金钱",
                                            command=self._restore_infinite_money_only, style='Danger.TButton')

        restore_btns = (self.restore_unlock_btn, self.restore_ammo_btn, self.restore_app_btn,
                        self.restore_toy_btn, self.restore_disk_btn,
                        self.restore_money_btn)
        self._grid_buttons(restore_frame, restore_btns)

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

    @staticmethod
    def _grid_buttons(parent: tk.Misc, buttons, columns: int = 3):
        """把按钮按固定列数排成网格，各列等宽。"""
        for col in range(columns):
            parent.columnconfigure(col, weight=1, uniform="btn")
        for i, btn in enumerate(buttons):
            btn.grid(row=i // columns, column=i % columns, padx=8, pady=4, sticky='ew')

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

    def _unlock_apps(self):
        """解锁所有手机 APP"""
        if not self._require_process():
            return

        def worker():
            try:
                self.status_var.set("正在查找函数...")
                if not self.cheat.find_app_unlock_function():
                    self.status_var.set("❌ 未找到 APP 解锁函数")
                    self._ui(lambda: messagebox.showerror(
                        "错误", "无法找到手机 APP 解锁函数。\n请确保游戏正在运行且版本匹配。"))
                    return

                self.status_var.set("正在解锁所有 APP...")
                if self.cheat.unlock_all_apps():
                    self._ui(self._on_app_success)
                else:
                    self.status_var.set("❌ 解锁失败，请检查权限和游戏状态")
                    self._ui(lambda: messagebox.showerror(
                        "❌ 解锁失败", "手机 APP 解锁失败。\n请确保游戏正在运行并以管理员权限启动程序。"))

            except Exception as e:
                logger.exception("解锁手机 APP 时发生错误")
                self.status_var.set("❌ 发生错误")
                self._ui(lambda: messagebox.showerror("错误", f"解锁过程中发生错误：\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_app_success(self):
        self.status_var.set("📱 所有手机 APP 已解锁！打开手机查看")
        self.app_btn_var.set("✅ 已解锁所有APP")
        self.app_btn.configure(state="disabled")
        messagebox.showinfo("📱 解锁成功！", "所有需达成成就的手机 APP 已解锁！\n打开游戏内手机即可看到新 APP。")

    def _unlock_toys(self):
        """解锁所有玩具"""
        if not self._require_process():
            return

        def worker():
            try:
                self.status_var.set("正在查找函数...")
                if not self.cheat.find_toy_unlock_function():
                    self.status_var.set("❌ 未找到玩具解锁函数")
                    self._ui(lambda: messagebox.showerror(
                        "错误", "无法找到玩具解锁函数。\n请确保游戏正在运行且版本匹配。"))
                    return

                self.status_var.set("正在解锁所有玩具...")
                if self.cheat.unlock_all_toys():
                    self._ui(self._on_toy_success)
                else:
                    self.status_var.set("❌ 解锁失败，请检查权限和游戏状态")
                    self._ui(lambda: messagebox.showerror(
                        "❌ 解锁失败", "玩具解锁失败。\n请确保游戏正在运行并以管理员权限启动程序。"))

            except Exception as e:
                logger.exception("解锁玩具时发生错误")
                self.status_var.set("❌ 发生错误")
                self._ui(lambda: messagebox.showerror("错误", f"解锁过程中发生错误：\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_toy_success(self):
        self.status_var.set("🧸 所有玩具已解锁！")
        self.toy_btn_var.set("✅ 已解锁所有玩具")
        self.toy_btn.configure(state="disabled")
        messagebox.showinfo("🧸 解锁成功！", "所有玩具已解锁！\n打开游戏内的玩具菜单即可看到新道具。")

    def _unlock_disks(self):
        """解锁所有软盘"""
        if not self._require_process():
            return

        def worker():
            try:
                self.status_var.set("正在查找函数...")
                if not self.cheat.find_disk_unlock_function():
                    self.status_var.set("❌ 未找到软盘解锁函数")
                    self._ui(lambda: messagebox.showerror(
                        "错误", "无法找到软盘解锁函数。\n请确保游戏正在运行且版本匹配。"))
                    return

                self.status_var.set("正在解锁所有软盘...")
                if self.cheat.unlock_all_disks():
                    self._ui(self._on_disk_success)
                else:
                    self.status_var.set("❌ 解锁失败，请检查权限和游戏状态")
                    self._ui(lambda: messagebox.showerror(
                        "❌ 解锁失败", "软盘解锁失败。\n请确保游戏正在运行并以管理员权限启动程序。"))

            except Exception as e:
                logger.exception("解锁软盘时发生错误")
                self.status_var.set("❌ 发生错误")
                self._ui(lambda: messagebox.showerror("错误", f"解锁过程中发生错误：\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_disk_success(self):
        self.status_var.set("💾 所有软盘已解锁！打开 FAPS 终端查看")
        self.disk_btn_var.set("✅ 已解锁所有软盘")
        self.disk_btn.configure(state="disabled")
        messagebox.showinfo("💾 解锁成功！", "所有软盘已解锁！\n打开游戏内 FAPS 终端 / 关卡选择即可看到新地图。")

    def _enable_infinite_money(self):
        """启用无限金钱（NADS）"""
        if not self._require_process():
            return

        def worker():
            try:
                self.status_var.set("正在查找函数...")
                if not self.cheat.find_money_function():
                    self.status_var.set("❌ 未找到金钱函数")
                    self._ui(lambda: messagebox.showerror(
                        "错误", "无法找到金钱函数。\n请确保游戏正在运行且版本匹配。"))
                    return

                self.status_var.set("正在启用无限金钱...")
                if self.cheat.enable_infinite_money():
                    self._ui(self._on_money_success)
                else:
                    self.status_var.set("❌ 无限金钱启用失败")
                    self._ui(lambda: messagebox.showerror(
                        "❌ 启用失败", "无限金钱启用失败。\n请确保游戏正在运行并以管理员权限启动程序。"))

            except Exception as e:
                logger.exception("启用无限金钱时发生错误")
                self.status_var.set("❌ 发生错误")
                self._ui(lambda: messagebox.showerror("错误", f"启用过程中发生错误：\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_money_success(self):
        amount = f"{C.MONEY_VALUE:,}"
        self.status_var.set(f"💰 无限金钱已激活！数值 {amount}")
        self.money_btn_var.set("✅ 无限金钱已启用")
        self.money_btn.configure(state="disabled")
        messagebox.showinfo(
            "💰 无限金钱激活！",
            f"金钱功能已成功启用！\n打开游戏内「银行 / 口袋」等 App 即可看到金额变为 {amount}。\n"
            "若 App 已经打开，请关闭后重新打开一次。")

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

    def _restore_app_unlock_only(self):
        """仅恢复“解锁全部 APP”修改"""
        def worker():
            try:
                self.status_var.set("正在恢复 APP 解锁修改...")
                ok = self.cheat.restore_app_unlock()
                self._ui(lambda: self._on_restore_done(
                    ok, "APP 解锁", self.app_btn_var, self.app_btn, "解锁所有APP"))
            except Exception as e:
                logger.exception("恢复 APP 解锁时发生错误")
                self.status_var.set("❌ 恢复失败")
                self._ui(lambda: messagebox.showerror("错误", f"恢复 APP 解锁时发生错误：\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _restore_toys_only(self):
        """仅恢复“解锁全部玩具”修改"""
        def worker():
            try:
                self.status_var.set("正在恢复玩具解锁修改...")
                ok = self.cheat.restore_toys_unlock()
                self._ui(lambda: self._on_restore_done(
                    ok, "玩具解锁", self.toy_btn_var, self.toy_btn, "解锁所有玩具"))
            except Exception as e:
                logger.exception("恢复玩具解锁时发生错误")
                self.status_var.set("❌ 恢复失败")
                self._ui(lambda: messagebox.showerror("错误", f"恢复玩具解锁时发生错误：\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _restore_disks_only(self):
        """仅恢复“解锁全部软盘”修改"""
        def worker():
            try:
                self.status_var.set("正在恢复软盘解锁修改...")
                ok = self.cheat.restore_disks_unlock()
                self._ui(lambda: self._on_restore_done(
                    ok, "软盘解锁", self.disk_btn_var, self.disk_btn, "解锁所有软盘"))
            except Exception as e:
                logger.exception("恢复软盘解锁时发生错误")
                self.status_var.set("❌ 恢复失败")
                self._ui(lambda: messagebox.showerror("错误", f"恢复软盘解锁时发生错误：\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _restore_infinite_money_only(self):
        """仅恢复“无限金钱”修改"""
        def worker():
            try:
                self.status_var.set("正在恢复无限金钱修改...")
                ok = self.cheat.restore_infinite_money()
                self._ui(lambda: self._on_restore_done(
                    ok, "无限金钱", self.money_btn_var, self.money_btn, "无限金钱"))
            except Exception as e:
                logger.exception("恢复无限金钱时发生错误")
                self.status_var.set("❌ 恢复失败")
                self._ui(lambda: messagebox.showerror("错误", f"恢复无限金钱时发生错误：\n{e}"))

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
