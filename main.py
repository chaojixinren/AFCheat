#!/usr/bin/env python3
"""Amazing Frog 修改器入口。

实际代码都在 afcheat 包中：
- afcheat.core  —— 进程枚举、内存读写、补丁逻辑
- afcheat.ui    —— tkinter 界面
"""

from tkinter import messagebox

from afcheat.ui.app import AmazingFrogCheatGUI


def main():
    """启动 GUI 主循环"""
    try:
        app = AmazingFrogCheatGUI()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("启动失败", f"程序启动失败：\n{e}")


if __name__ == "__main__":
    main()
