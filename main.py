#!/usr/bin/env python3
"""
Amazing Frog 修改器GUI
基于tkinter开发的游戏修改器界面

功能：
- 解锁所有皮肤（服装）- 内存修改
- 启用无限子弹 - 内存修改
- 状态反馈和错误处理

依赖：
- KittyMemory (用于内存修改)
- tkinter (GUI框架)
- psutil (用于进程枚举)
"""

import os
import struct
import threading
from dataclasses import dataclass
from typing import List

import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage, filedialog

try:
    import KittyMemory
except ImportError:
    KittyMemory = None

try:
    import psutil
except ImportError:
    psutil = None



@dataclass
class ProcessInfo:
    """进程信息数据类"""
    pid: int
    name: str
    exe_path: str = ""
    memory_info: str = ""

class AmazingFrogCheat:
    """Amazing Frog 游戏修改核心类"""

    def __init__(self):
        self.gameassembly_base = None
        self.silent_unlock_addr = None
        self.ammo_check_addr = None
        self.original_unlock_bytes = None
        self.original_ammo_bytes = None

        # 进程相关
        self.selected_pid = None
        self.process_name = "Amazing Frog.exe"  # 默认进程名

        # PC版本偏移量（从分析文档中获取）
        self.pc_unlock_offset = 0x740AF0  # IsCostumeItemUnlocked
        self.pc_ammo_offset = 0x65BAF0    # get_infiniteAmmo
        self.pc_silent_unlock_offset = 0x991310  # SilentUnlockCostume

        self.costume_unlocked = False
        self.infinite_ammo_enabled = False

    def enumerate_processes(self) -> List[ProcessInfo]:
        """枚举所有运行中的进程"""
        processes = []

        if psutil is None:
            return processes

        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'memory_info']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name'] or ""
                    exe_path = proc.info['exe'] or ""
                    memory_mb = 0

                    if proc.info['memory_info']:
                        memory_mb = proc.info['memory_info'].rss // (1024 * 1024)

                    # 过滤掉系统进程和无用进程
                    if (name and
                        not name.startswith(('System', 'svchost', 'csrss', 'lsass', 'winlogon')) and
                        memory_mb > 10):  # 只显示内存使用大于10MB的进程

                        processes.append(ProcessInfo(
                            pid=pid,
                            name=name,
                            exe_path=exe_path,
                            memory_info=f"{memory_mb}MB"
                        ))

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # 按进程名排序
            processes.sort(key=lambda x: x.name.lower())
            return processes

        except Exception as e:
            return processes

    def set_target_process(self, pid: int, process_name: str):
        """设置目标进程"""
        self.selected_pid = pid
        self.process_name = process_name

    def validate_game_process(self, pid: int) -> bool:
        """验证进程是否是有效的Amazing Frog游戏进程"""
        try:
            # 首先检查进程是否仍然存在
            import psutil
            if not psutil.pid_exists(pid):
                return False

            # 尝试获取GameAssembly.dll基址来验证
            base_addr = KittyMemory.get_base_address_by_pid(pid, "GameAssembly.dll")
            return base_addr is not None

        except Exception as e:
            return False

    def get_base_address(self) -> bool:
        """获取GameAssembly.dll基址"""
        try:
            if self.selected_pid is not None:
                # 如果已选择特定进程，使用进程ID
                self.gameassembly_base = KittyMemory.get_base_address_by_pid(
                    self.selected_pid, "GameAssembly.dll"
                )
            else:
                # 默认方式：通过进程名查找
                self.gameassembly_base = KittyMemory.get_base_address("GameAssembly.dll")

            return self.gameassembly_base is not None
        except Exception as e:
            return False

    def find_functions(self) -> tuple[bool, bool]:
        """查找需要修改的函数地址"""
        if not self.gameassembly_base:
            if not self.get_base_address():
                return False, False

        unlock_found = False
        ammo_found = False

        # 查找IsCostumeItemUnlocked函数
        if self.pc_unlock_offset is not None:
            test_addr = self.gameassembly_base + self.pc_unlock_offset
            try:
                bytes_at_addr = KittyMemory.read_bytes(test_addr, 10)
                if bytes_at_addr and bytes_at_addr[0] in [0x40, 0x48, 0x55, 0xE9]:
                    self.silent_unlock_addr = test_addr
                    unlock_found = True
            except:
                pass

        # 查找get_infiniteAmmo函数
        if self.pc_ammo_offset is not None:
            test_addr = self.gameassembly_base + self.pc_ammo_offset
            try:
                bytes_at_addr = KittyMemory.read_bytes(test_addr, 10)
                if bytes_at_addr and bytes_at_addr[0] in [0x40, 0x48, 0x55, 0xE9]:
                    self.ammo_check_addr = test_addr
                    ammo_found = True
            except:
                pass

        return unlock_found, ammo_found

    def unlock_all_costumes(self) -> bool:
        """解锁所有皮肤"""
        if not self.silent_unlock_addr:
            return False

        try:
            # 修改为总是返回true: mov rax, 1; ret
            patch = bytes([0x48, 0xC7, 0xC0, 0x01, 0x00, 0x00, 0x00, 0xC3])

            # 保存原始字节
            self.original_unlock_bytes = KittyMemory.read_bytes(
                self.silent_unlock_addr, len(patch)
            )

            # 应用patch
            KittyMemory.write_bytes(self.silent_unlock_addr, patch)
            self.costume_unlocked = True
            return True

        except Exception as e:
            return False

    def enable_infinite_ammo(self) -> bool:
        """启用无限子弹"""
        if not self.ammo_check_addr:
            return False

        try:
            # 修改为总是返回true: mov rax, 1; ret
            patch = bytes([0x48, 0xC7, 0xC0, 0x01, 0x00, 0x00, 0x00, 0xC3])

            # 保存原始字节
            self.original_ammo_bytes = KittyMemory.read_bytes(
                self.ammo_check_addr, len(patch)
            )

            # 应用patch
            KittyMemory.write_bytes(self.ammo_check_addr, patch)
            self.infinite_ammo_enabled = True
            return True

        except Exception as e:
            return False

    def restore_original(self) -> tuple[bool, bool]:
        """恢复原始代码"""
        unlock_restored = False
        ammo_restored = False

        if self.silent_unlock_addr and self.original_unlock_bytes:
            try:
                KittyMemory.write_bytes(self.silent_unlock_addr, self.original_unlock_bytes)
                unlock_restored = True
                self.costume_unlocked = False
            except Exception as e:
                pass

        if self.ammo_check_addr and self.original_ammo_bytes:
            try:
                KittyMemory.write_bytes(self.ammo_check_addr, self.original_ammo_bytes)
                ammo_restored = True
                self.infinite_ammo_enabled = False
            except Exception as e:
                pass

        return unlock_restored, ammo_restored

    def restore_costume_unlock(self) -> bool:
        """仅恢复“解锁全部皮肤”相关修改"""
        if self.silent_unlock_addr and self.original_unlock_bytes:
            try:
                KittyMemory.write_bytes(self.silent_unlock_addr, self.original_unlock_bytes)
                self.costume_unlocked = False
                return True
            except Exception as e:
                pass
                return False
        return False

    def restore_infinite_ammo(self) -> bool:
        """仅恢复“无限子弹”相关修改"""
        if self.ammo_check_addr and self.original_ammo_bytes:
            try:
                KittyMemory.write_bytes(self.ammo_check_addr, self.original_ammo_bytes)
                self.infinite_ammo_enabled = False
                return True
            except Exception as e:
                pass
                return False
        return False



class AmazingFrogCheatGUI(tk.Tk):
    """Amazing Frog 修改器GUI主窗口"""

    def __init__(self):
        super().__init__()

        # 设置窗口属性
        self.title("AFCheat v1.0 -by 超級の新人")
        self.geometry("1000x800")
        self.minsize(960, 720)
        self.resizable(True, True)
        self.configure(bg='#f0f2f5')

        # 设置窗口图标（如果有的话）
        try:
            self.iconbitmap("AmazingFrog.exe")  # 尝试使用游戏图标
        except:
            pass

        # 设置主题样式
        self._setup_styles()
        self._load_assets()

        # 初始化修改器
        self.cheat = AmazingFrogCheat()


        # GUI变量
        self.status_var = tk.StringVar(value="就绪")
        self.unlock_btn_var = tk.StringVar(value="解锁所有皮肤")
        self.ammo_btn_var = tk.StringVar(value="启用无限子弹")
        self.selected_process_var = tk.StringVar(value="未选择进程")
        self.process_list = []  # 存储进程列表
        self.filtered_process_list = []  # 过滤后的进程列表
        self.process_search_var = tk.StringVar()  # 进程搜索关键词


        # 构建界面
        self._build_ui()

        # 检查依赖
        self.check_dependencies()



    def _setup_styles(self):
        """设置GUI样式"""
        style = ttk.Style()

        # 设置主题
        try:
            style.theme_use('clam')  # 使用clam主题，更现代
        except:
            pass

        # 自定义按钮样式 - 使用更现代的颜色和圆角效果
        style.configure('Success.TButton',
                       background='#10b981',  # 绿色
                       foreground='white',
                       font=('Microsoft YaHei', 10, 'bold'),
                       padding=(20, 10),
                       relief='flat',
                       borderwidth=0)

        style.map('Success.TButton',
                 background=[('active', '#059669'), ('pressed', '#047857')],
                 foreground=[('active', 'white'), ('pressed', 'white')])

        style.configure('Primary.TButton',
                       background='#3b82f6',  # 蓝色
                       foreground='white',
                       font=('Microsoft YaHei', 10, 'bold'),
                       padding=(20, 10),
                       relief='flat',
                       borderwidth=0)

        style.map('Primary.TButton',
                 background=[('active', '#2563eb'), ('pressed', '#1d4ed8')],
                 foreground=[('active', 'white'), ('pressed', 'white')])

        style.configure('Warning.TButton',
                       background='#f59e0b',  # 橙色
                       foreground='white',
                       font=('Microsoft YaHei', 10, 'bold'),
                       padding=(20, 10),
                       relief='flat',
                       borderwidth=0)

        style.map('Warning.TButton',
                 background=[('active', '#d97706'), ('pressed', '#b45309')],
                 foreground=[('active', 'white'), ('pressed', 'white')])

        style.configure('Danger.TButton',
                       background='#ef4444',  # 红色
                       foreground='white',
                       font=('Microsoft YaHei', 10, 'bold'),
                       padding=(20, 10),
                       relief='flat',
                       borderwidth=0)

        style.map('Danger.TButton',
                 background=[('active', '#dc2626'), ('pressed', '#b91c1c')],
                 foreground=[('active', 'white'), ('pressed', 'white')])

        # 标签样式
        style.configure('Title.TLabel',
                       font=('Microsoft YaHei', 18, 'bold'),
                       foreground='#0f172a')

        style.configure('Subtitle.TLabel',
                       font=('Microsoft YaHei', 10),
                       foreground='#64748b')

        style.configure('Accent.TLabel',
                       font=('Microsoft YaHei', 10, 'bold'),
                       foreground='#3b82f6')

        style.configure('Header.TLabel',
                       font=('Microsoft YaHei', 12, 'bold'),
                       foreground='#334155')

        style.configure('Status.TLabel',
                       font=('Consolas', 9),
                       foreground='#059669')

        # 框架样式 - 添加更柔和的边框和阴影效果
        style.configure('Card.TLabelframe',
                       background='#ffffff',
                       relief='flat',
                       borderwidth=0,
                       padding=15)

        style.configure('Card.TLabelframe.Label',
                       background='#ffffff',
                       foreground='#334155',
                       font=('Microsoft YaHei', 11, 'bold'))

        # 常用容器 Frame 样式
        style.configure('Card.TFrame', background='#ffffff')
        style.configure('Main.TFrame', background='#f0f2f5')

        # 表格样式
        style.configure('Treeview',
                       background='#ffffff',
                       fieldbackground='#ffffff',
                       foreground='#334155',
                       font=('Microsoft YaHei', 9),
                       rowheight=28)
        style.map('Treeview', background=[('selected', '#e0f2fe')])

        style.configure('Treeview.Heading',
                       background='#f1f5f9',
                       foreground='#334155',
                       font=('Microsoft YaHei', 9, 'bold'),
                       relief='flat')

        style.configure('TEntry',
                       font=('Microsoft YaHei', 10),
                       relief='flat',
                       borderwidth=2,
                       fieldbackground='#f8fafc',
                       bordercolor='#e2e8f0',
                       padding=8)
        
        style.map('TEntry',
                 bordercolor=[('focus', '#3b82f6')],
                 fieldbackground=[('focus', '#ffffff')])

    def _load_assets(self):
        """加载 UI 资源（如封面图）；图片过大时自动缩小"""
        self.hero_image = None
        img_path = os.path.join(os.path.dirname(__file__), "amazingfrog.png")
        if os.path.exists(img_path):
            try:
                img = PhotoImage(file=img_path)
                # 如果图片太大，缩小到合适尺寸（最大宽度300px）
                max_width = 300
                if img.width() > max_width:
                    scale = (img.width() + max_width - 1) // max_width  # 向上取整
                    img = img.subsample(scale, scale)
                self.hero_image = img
            except Exception as exc:
                print(f"[ui] 加载 amazingfrog.png 失败: {exc}")

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

    def check_dependencies(self):
        """检查必要依赖"""
        if KittyMemory is None:
            messagebox.showerror(
                "缺少依赖",
                "未找到 KittyMemory 依赖。\n\n"
                "请确保 KittyMemory.py 文件与本脚本同目录。\n"
                "该功能需要管理员权限运行。"
            )
            return

        if psutil is None:
            messagebox.showerror(
                "缺少依赖",
                "未找到 psutil 依赖。\n\n"
                "请执行：pip install psutil\n"
                "进程枚举功能需要此依赖。"
            )
            return

        self._refresh_process_list()

    def _build_title_section(self, parent):
        """构建标题区域 - 美化版本"""
        # 创建带边框的卡片容器
        title_card = tk.Frame(parent, bg='#ffffff', relief='flat', bd=0)
        title_card.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        title_card.columnconfigure(1, weight=1)
        
        # 添加内部边距框架
        title_frame = tk.Frame(title_card, bg='#ffffff')
        title_frame.pack(fill='both', expand=True, padx=25, pady=20)

        # 左侧图片区域 - 添加圆角边框效果
        hero_container = tk.Frame(title_frame, bg='#f8fafc', relief='flat', bd=0)
        hero_container.grid(row=0, column=0, sticky="nw", padx=(0, 25))
        
        hero = tk.Frame(hero_container, bg='#f8fafc', bd=0)
        hero.pack(padx=8, pady=8)
        
        if self.hero_image:
            img_label = tk.Label(hero, image=self.hero_image, bg='#f8fafc', bd=0)
            img_label.pack()
        else:
            tk.Label(
                hero,
                text="🐸",
                font=('Segoe UI Emoji', 48),
                bg='#f8fafc',
                fg='#3b82f6'
            ).pack()

        # 右侧信息区域
        info = tk.Frame(title_frame, bg='#ffffff')
        info.grid(row=0, column=1, sticky="ew")
        info.columnconfigure(0, weight=1)

        # 主标题 - 添加渐变效果文字
        title_label = tk.Label(
            info,
            text="AFCheat",
            font=('Microsoft YaHei', 24, 'bold'),
            fg='#0f172a',
            bg='#ffffff',
            anchor='w'
        )
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        # 副标题
        subtitle_label = tk.Label(
            info,
            text="先选择 / 验证 Amazing Frog 进程，再使用下方功能按钮。",
            font=('Microsoft YaHei', 11),
            fg='#64748b',
            bg='#ffffff',
            anchor='w'
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(0, 15))

        # 作者信息条 - 美化样式
        author_bar = tk.Frame(info, bg='#f1f5f9', relief='flat', bd=0)
        author_bar.grid(row=2, column=0, sticky="ew")
        
        author_label = tk.Label(
            author_bar,
            text="本程序仅供学习交流，请勿倒卖。作者：超級の新人 | QQ：3488993732 | 群：364969455 | 适用 QMMT part 6.35",
            font=('Microsoft YaHei', 9),
            bg='#f1f5f9',
            fg='#475569',
            anchor='w',
            padx=12,
            pady=8
        )
        author_label.pack(fill='x')


    def _refresh_process_list(self):
        """刷新进程列表"""
        try:
            self.process_list = self.cheat.enumerate_processes()
            self._filter_processes()  # 刷新时重新过滤
            self.status_var.set(f"🔄 已刷新进程列表，共发现 {len(self.process_list)} 个进程")
        except Exception as e:
            self.status_var.set(f"❌ 刷新进程列表失败: {str(e)}")

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
        # 清空现有项目
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)

        # 添加进程项目
        for idx, process in enumerate(self.filtered_process_list):
            self.process_tree.insert(
                "",
                "end",
                values=(
                    process.pid,
                    process.name,
                    process.memory_info,
                    process.exe_path
                ),
                tags=('oddrow',) if (idx % 2) else ()
            )

    def _select_process(self, pid: int, name: str):
        """设置当前目标进程，并异步验证是否为游戏进程（避免卡 UI）"""
        self.cheat.set_target_process(pid, name)
        self.selected_process_var.set(f"已选择: {name} (PID: {pid})")
        self.status_var.set("正在验证进程是否为游戏…")

        def worker():
            try:
                is_valid_game = self.cheat.validate_game_process(pid)
            except Exception:
                is_valid_game = False

            def update_ui():
                if is_valid_game:
                    self.selected_process_var.set(f"已选择: {name} (PID: {pid})")
                    self.status_var.set("已选择有效的游戏进程，可以开始修改！")
                    self._set_process_list_collapsed(True)
                else:
                    self.selected_process_var.set(f"⚠️ 已选择: {name} (PID: {pid}) - 非游戏进程/无法验证")
                    self.status_var.set("⚠️ 警告：选择的进程不包含 GameAssembly.dll，可能不是 Amazing Frog。")

            self.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def _set_process_list_collapsed(self, collapsed: bool):
        if not hasattr(self, "process_search_container") or not hasattr(self, "process_list_container"):
            return
        if collapsed:
            self.process_search_container.grid_remove()
            self.process_list_container.grid_remove()
            self._process_list_collapsed = True
            if hasattr(self, "toggle_process_list_btn"):
                self.toggle_process_list_btn.configure(text="📂 展开进程列表")
        else:
            self.process_search_container.grid()
            self.process_list_container.grid()
            self._process_list_collapsed = False
            if hasattr(self, "toggle_process_list_btn"):
                self.toggle_process_list_btn.configure(text="📂 收起进程列表")

    def _toggle_process_list(self):
        self._set_process_list_collapsed(not getattr(self, "_process_list_collapsed", False))

    def _on_process_select(self, event):
        """处理进程选择事件"""
        try:
            selection = self.process_tree.selection()
            if not selection:
                return
            item = self.process_tree.item(selection[0])
            values = item.get("values") or []
            if len(values) < 2:
                return
            pid = int(values[0])
            name = str(values[1])
            self._select_process(pid, name)
        except Exception as e:
            self.status_var.set(f"❌ 选择进程失败: {e}")








    def _build_ui(self):
        """构建用户界面"""
        # 使用 Canvas + 右侧滚动条，避免窗口内容过长时看不到下方功能
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll_root = ttk.Frame(self, style="Main.TFrame")
        scroll_root.grid(row=0, column=0, sticky="nsew")
        scroll_root.columnconfigure(0, weight=1)
        scroll_root.rowconfigure(0, weight=1)

        self._scroll_canvas = tk.Canvas(scroll_root, bg="#f0f2f5", highlightthickness=0)
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

        parent = content
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=0)  # 标题区域
        parent.rowconfigure(1, weight=0)  # 进程选择面板
        parent.rowconfigure(2, weight=0)  # 游戏修改面板
        parent.rowconfigure(3, weight=0)  # 底部信息面板

        # 标题区域
        self._build_title_section(parent)

        # 进程选择面板 - 美化版本
        process_card = tk.Frame(parent, bg='#ffffff', relief='flat', bd=0)
        process_card.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        process_card.columnconfigure(0, weight=1)
        
        # 标题栏
        process_header = tk.Frame(process_card, bg='#f8fafc', relief='flat', bd=0)
        process_header.pack(fill='x')
        
        header_label = tk.Label(
            process_header,
            text="🎯 进程选择与管理",
            font=('Microsoft YaHei', 13, 'bold'),
            fg='#334155',
            bg='#f8fafc',
            anchor='w',
            padx=20,
            pady=12
        )
        header_label.pack(fill='x')
        
        # 内容区域
        process_frame = tk.Frame(process_card, bg='#ffffff')
        process_frame.pack(fill='both', expand=True, padx=20, pady=20)
        process_frame.columnconfigure(0, weight=1)

        # 进程控制按钮区域
        control_frame = tk.Frame(process_frame, bg='#ffffff')
        control_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # 统一按钮组
        btn_frame = tk.Frame(control_frame, bg='#ffffff')
        btn_frame.pack()

        self.refresh_btn = ttk.Button(
            btn_frame,
            text="刷新进程列表",
            command=self._refresh_process_list,
            style='Primary.TButton'
        )
        self.refresh_btn.pack(side='left', padx=(0, 15))

        self.auto_find_btn = ttk.Button(
            btn_frame,
            text="自动查找游戏",
            command=self._auto_find_game_process,
            style='Success.TButton'
        )
        self.auto_find_btn.pack(side='left', padx=(0, 15))

        self.validate_btn = ttk.Button(
            btn_frame,
            text="验证游戏进程",
            command=self._validate_selected_process,
            style='Warning.TButton'
        )
        self.validate_btn.pack(side='left', padx=(0, 15))

        self.toggle_process_list_btn = ttk.Button(
            btn_frame,
            text="收起进程列表",
            command=self._toggle_process_list,
            style='Primary.TButton'
        )
        self.toggle_process_list_btn.pack(side='left')

        # 当前选择进程显示区域 - 美化
        selection_frame = tk.Frame(process_frame, bg='#f8fafc', relief='flat', bd=0)
        selection_frame.grid(row=1, column=0, columnspan=3, pady=(0, 15), sticky='ew')
        
        tk.Label(
            selection_frame,
            text="当前选择：",
            font=('Microsoft YaHei', 11, 'bold'),
            fg='#334155',
            bg='#f8fafc'
        ).pack(side='left', padx=12, pady=10)
        
        tk.Label(
            selection_frame,
            textvariable=self.selected_process_var,
            font=("Microsoft YaHei", 11, 'bold'),
            fg="#3b82f6",
            bg='#f8fafc'
        ).pack(side='left', padx=(0, 12), pady=10)

        # 进程搜索框 - 美化
        search_container = tk.Frame(process_frame, bg='#ffffff')
        search_container.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        self.process_search_container = search_container

        search_frame = tk.Frame(search_container, bg='#ffffff')
        search_frame.pack(fill='x', pady=5)
        search_frame.columnconfigure(1, weight=1)

        search_label_frame = tk.Frame(search_frame, bg='#ffffff')
        search_label_frame.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        tk.Label(
            search_label_frame,
            text="🔍",
            font=('Segoe UI Emoji', 14),
            bg='#ffffff'
        ).pack(side='left', padx=(0, 6))
        
        tk.Label(
            search_label_frame,
            text="搜索进程：",
            font=('Microsoft YaHei', 11, 'bold'),
            fg='#334155',
            bg='#ffffff'
        ).pack(side='left')
        
        process_search_entry = ttk.Entry(
            search_frame,
            textvariable=self.process_search_var,
            font=('Microsoft YaHei', 10),
            width=35
        )
        process_search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 0))
        process_search_entry.bind("<KeyRelease>", lambda e: self._filter_processes())

        # 进程列表容器 - 美化
        list_container = tk.Frame(process_frame, bg='#ffffff')
        list_container.grid(row=3, column=0, columnspan=3, sticky="ew")
        self.process_list_container = list_container

        # 列表标题
        list_title_frame = tk.Frame(list_container, bg='#f8fafc', relief='flat', bd=0)
        list_title_frame.pack(fill='x', pady=(0, 8))

        tk.Label(
            list_title_frame,
            text="📋",
            font=('Segoe UI Emoji', 14),
            bg='#f8fafc'
        ).pack(side='left', padx=(12, 8), pady=10)

        tk.Label(
            list_title_frame,
            text="运行中的进程列表",
            font=('Microsoft YaHei', 11, 'bold'),
            fg='#334155',
            bg='#f8fafc'
        ).pack(side='left', pady=10)

        # 进程表格
        process_list_frame = tk.Frame(list_container, bg='#ffffff')
        process_list_frame.pack(fill='both', expand=True, pady=(0, 0))
        process_list_frame.columnconfigure(0, weight=1)
        process_list_frame.rowconfigure(0, weight=1)

        columns = ("pid", "name", "memory", "path")
        self.process_tree = ttk.Treeview(
            process_list_frame,
            columns=columns,
            show="headings",
            height=8,  # 增加高度显示更多进程
            selectmode='browse'
        )
        self.process_tree.tag_configure('oddrow', background='#f8fafc')

        # 设置表格样式
        self.process_tree.heading("pid", text="PID", anchor='center')
        self.process_tree.heading("name", text="进程名称")
        self.process_tree.heading("memory", text="内存使用")
        self.process_tree.heading("path", text="文件路径")

        self.process_tree.column("pid", width=80, anchor="center", stretch=False)
        self.process_tree.column("name", width=180, anchor="w", stretch=False)
        self.process_tree.column("memory", width=100, anchor="center", stretch=False)
        self.process_tree.column("path", width=400, anchor="w", stretch=True)

        # 滚动条
        process_v_scrollbar = ttk.Scrollbar(
            process_list_frame,
            orient="vertical",
            command=self.process_tree.yview
        )
        process_h_scrollbar = ttk.Scrollbar(
            process_list_frame,
            orient="horizontal",
            command=self.process_tree.xview
        )
        self.process_tree.configure(
            yscrollcommand=process_v_scrollbar.set,
            xscrollcommand=process_h_scrollbar.set
        )

        self.process_tree.grid(row=0, column=0, sticky="nsew")
        process_v_scrollbar.grid(row=0, column=1, sticky="ns")
        process_h_scrollbar.grid(row=1, column=0, sticky="ew")

        # 绑定选择事件
        self.process_tree.bind("<<TreeviewSelect>>", self._on_process_select)
        self.process_tree.bind("<ButtonRelease-1>", self._on_process_select)

        # 游戏修改面板 - 美化版本
        control_card = tk.Frame(parent, bg='#ffffff', relief='flat', bd=0)
        control_card.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        control_card.columnconfigure(0, weight=1)
        
        # 标题栏
        control_header = tk.Frame(control_card, bg='#f8fafc', relief='flat', bd=0)
        control_header.pack(fill='x')
        
        header_label = tk.Label(
            control_header,
            text="🎮 游戏修改功能",
            font=('Microsoft YaHei', 13, 'bold'),
            fg='#334155',
            bg='#f8fafc',
            anchor='w',
            padx=20,
            pady=12
        )
        header_label.pack(fill='x')
        
        # 内容区域
        control_frame = tk.Frame(control_card, bg='#ffffff')
        control_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 主要功能按钮区域 - 美化布局
        main_features_frame = tk.Frame(control_frame, bg='#ffffff')
        main_features_frame.pack(pady=(0, 20), anchor='center')

        # 解锁皮肤功能
        unlock_frame = tk.Frame(main_features_frame, bg='#ffffff')
        unlock_frame.pack(side='left', padx=(0, 15))

        self.unlock_btn = ttk.Button(
            unlock_frame,
            textvariable=self.unlock_btn_var,
            command=self._unlock_costumes,
            style='Success.TButton'
        )
        self.unlock_btn.pack()

        # 无限子弹功能
        ammo_frame = tk.Frame(main_features_frame, bg='#ffffff')
        ammo_frame.pack(side='left', padx=(0, 15))

        self.ammo_btn = ttk.Button(
            ammo_frame,
            textvariable=self.ammo_btn_var,
            command=self._enable_infinite_ammo,
            style='Success.TButton'
        )
        self.ammo_btn.pack()

        # 恢复功能
        restore_frame = tk.Frame(main_features_frame, bg='#ffffff')
        restore_frame.pack(side='left')

        self.restore_unlock_btn = ttk.Button(
            restore_frame,
            text="恢复皮肤解锁",
            command=self._restore_costume_unlock_only,
            style='Danger.TButton'
        )
        self.restore_unlock_btn.pack(side='left', padx=(0, 15))

        self.restore_ammo_btn = ttk.Button(
            restore_frame,
            text="恢复无限子弹",
            command=self._restore_infinite_ammo_only,
            style='Danger.TButton'
        )
        self.restore_ammo_btn.pack(side='left')


        # 状态显示区域 - 美化
        status_frame = tk.Frame(control_frame, bg='#f8fafc', relief='flat', bd=0)
        status_frame.pack(fill='x', pady=(0, 0))

        status_header = tk.Frame(status_frame, bg='#f8fafc')
        status_header.pack(fill='x', padx=12, pady=(12, 8))

        tk.Label(
            status_header,
            text="📊",
            font=('Segoe UI Emoji', 14),
            bg='#f8fafc'
        ).pack(side='left', padx=(0, 8))

        tk.Label(
            status_header,
            text="操作状态",
            font=('Microsoft YaHei', 11, 'bold'),
            fg='#334155',
            bg='#f8fafc'
        ).pack(side='left')

        status_content = tk.Frame(status_frame, bg='#f8fafc')
        status_content.pack(fill='x', padx=12, pady=(0, 12))

        tk.Label(
            status_content,
            text="当前状态：",
            font=('Microsoft YaHei', 10, 'bold'),
            fg='#334155',
            bg='#f8fafc'
        ).pack(side='left', padx=(0, 8))
        
        status_label = tk.Label(
            status_content,
            textvariable=self.status_var,
            font=("Microsoft YaHei", 10, "bold"),
            fg="#059669",
            bg='#f8fafc'
        )
        status_label.pack(side='left')

    def _unlock_costumes(self):
        """解锁所有皮肤"""
        if self.cheat.selected_pid is None:
            messagebox.showwarning(
                "未选择进程",
                "请先从进程列表中选择 Amazing Frog 游戏进程。\n\n"
                "1. 确保游戏正在运行\n"
                "2. 点击'刷新进程列表'按钮\n"
                "3. 在列表中选择游戏进程\n"
                "4. 然后再尝试修改"
            )
            return

        def worker():
            try:
                self.status_var.set("正在查找函数...")
                unlock_found, _ = self.cheat.find_functions()

                if not unlock_found:
                    self.status_var.set("❌ 未找到皮肤解锁函数")
                    messagebox.showerror("错误", "无法找到皮肤解锁函数。\n请确保游戏正在运行且版本匹配。")
                    return

                self.status_var.set("正在解锁所有皮肤...")
                if self.cheat.unlock_all_costumes():
                    self.status_var.set("🎉 恭喜！所有皮肤已成功解锁！")
                    self.unlock_btn_var.set("✅ 已解锁所有皮肤")
                    self.unlock_btn.configure(state="disabled")
                    messagebox.showinfo("🎊 解锁成功！", "所有皮肤已成功解锁！\n请回到游戏中查看新解锁的服装！")
                else:
                    self.status_var.set("❌ 解锁失败，请检查权限和游戏状态")
                    messagebox.showerror("❌ 解锁失败", "皮肤解锁失败。\n请确保游戏正在运行并以管理员权限启动程序。")

            except Exception as e:
                self.status_var.set("❌ 发生错误")
                messagebox.showerror("错误", f"解锁过程中发生错误：\n{str(e)}")
        threading.Thread(target=worker, daemon=True).start()

    def _enable_infinite_ammo(self):
        """启用无限子弹"""
        if self.cheat.selected_pid is None:
            messagebox.showwarning(
                "未选择进程",
                "请先从进程列表中选择 Amazing Frog 游戏进程。\n\n"
                "1. 确保游戏正在运行\n"
                "2. 点击'刷新进程列表'按钮\n"
                "3. 在列表中选择游戏进程\n"
                "4. 然后再尝试修改"
            )
            return

        def worker():
            try:
                self.status_var.set("正在查找函数...")
                _, ammo_found = self.cheat.find_functions()

                if not ammo_found:
                    self.status_var.set("❌ 未找到无限子弹函数")
                    messagebox.showerror("错误", "无法找到无限子弹函数。\n请确保游戏正在运行且版本匹配。")
                    return

                self.status_var.set("正在启用无限子弹...")
                if self.cheat.enable_infinite_ammo():
                    self.status_var.set("🔫 无限子弹已激活！尽情射击吧！")
                    self.ammo_btn_var.set("✅ 无限子弹已启用")
                    self.ammo_btn.configure(state="disabled")
                    messagebox.showinfo("🔥 无限子弹激活！", "无限子弹功能已成功启用！\n现在你可以无限射击，尽情享受游戏！")
                else:
                    self.status_var.set("❌ 无限子弹启用失败")
                    messagebox.showerror("❌ 启用失败", "无限子弹启用失败。\n请确保游戏正在运行并以管理员权限启动程序。")

            except Exception as e:
                self.status_var.set("❌ 发生错误")
                messagebox.showerror("错误", f"启用过程中发生错误：\n{str(e)}")

        threading.Thread(target=worker, daemon=True).start()

    def _restore_costume_unlock_only(self):
        """仅恢复“解锁全部皮肤”修改"""
        def worker():
            try:
                self.status_var.set("正在恢复皮肤解锁修改...")
                ok = self.cheat.restore_costume_unlock()
                if ok:
                    self.unlock_btn_var.set("解锁所有皮肤")
                    self.unlock_btn.configure(state="normal")
                    self.status_var.set("✅ 已恢复皮肤解锁修改")
                    messagebox.showinfo("成功", "已恢复皮肤解锁修改。")
                else:
                    self.status_var.set("ℹ️ 没有可恢复的皮肤解锁修改")
                    messagebox.showinfo("提示", "没有检测到可恢复的皮肤解锁修改。")
            except Exception as e:
                self.status_var.set("❌ 恢复失败")
                messagebox.showerror("错误", f"恢复皮肤解锁时发生错误：\n{e}")

        threading.Thread(target=worker, daemon=True).start()

    def _restore_infinite_ammo_only(self):
        """仅恢复“无限子弹”修改"""
        def worker():
            try:
                self.status_var.set("正在恢复无限子弹修改...")
                ok = self.cheat.restore_infinite_ammo()
                if ok:
                    self.ammo_btn_var.set("启用无限子弹")
                    self.ammo_btn.configure(state="normal")
                    self.status_var.set("✅ 已恢复无限子弹修改")
                    messagebox.showinfo("成功", "已恢复无限子弹修改。")
                else:
                    self.status_var.set("ℹ️ 没有可恢复的无限子弹修改")
                    messagebox.showinfo("提示", "没有检测到可恢复的无限子弹修改。")
            except Exception as e:
                self.status_var.set("❌ 恢复失败")
                messagebox.showerror("错误", f"恢复无限子弹时发生错误：\n{e}")
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

        game_processes = []
        for process in self.process_list:
            if self.cheat.validate_game_process(process.pid):
                game_processes.append(process)

        if game_processes:
            if len(game_processes) == 1:
                # 只有一个游戏进程，直接选择
                process = game_processes[0]
                self._select_process(process.pid, process.name)
                messagebox.showinfo("自动查找成功", f"已自动选择游戏进程：\n{process.name} (PID: {process.pid})")
            else:
                # 多个游戏进程，让用户选择
                self.status_var.set(f"找到 {len(game_processes)} 个游戏进程，请手动选择")
                messagebox.showinfo("找到多个游戏进程", f"找到 {len(game_processes)} 个可能的游戏进程，\n请从列表中选择一个。")
        else:
            self.status_var.set("❌ 未找到游戏进程")
            messagebox.showwarning("未找到游戏进程", "未找到包含GameAssembly.dll的进程。\n请确保游戏正在运行，然后刷新进程列表。")



def main():
    """主函数"""
    try:
        app = AmazingFrogCheatGUI()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("启动失败", f"程序启动失败：\n{str(e)}")


if __name__ == "__main__":
    main()
