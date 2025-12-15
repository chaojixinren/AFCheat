# AFCheat (Amazing Frog 修改器)

## 简介
AFCheat 是一个对 Windows 平台的《Amazing Frog》单机游戏修改器，提供图形界面，允许用户通过内存修改实现解锁皮肤、启用无限子弹等功能。

## 原理
- 使用 Windows API打开游戏进程句柄并读写进程内存。
- 定位 `GameAssembly.dll` 的基址，然后根据已知偏移或模式扫描查找目标函数地址。
- 通过写入汇编补丁来强制函数返回指定值，从而实现功能修改。

## 技术栈
- 语言：Python 3
- GUI：`tkinter`
- 进程与内存操作：`ctypes`（调用 `kernel32` / `psapi`）、`KittyMemory.py`
- 进程枚举：`psutil`
- 平台：Windows（需要管理员权限以写入其他进程内存）

## 功能
- 列出并选择运行中的进程
- 验证并定位 `GameAssembly.dll` 基址
- 解锁所有皮肤（服装）
- 启用/恢复无限子弹
- 恢复为原始内存状态

## 使用
1. 安装依赖：

```bash
pip install psutil
```

2. 以管理员身份运行游戏并确保其在运行。然后以管理员权限运行本工具：

```bash
python main.py
```

3. 在 GUI 中选择目标进程，查找函数并应用/恢复修改。

## 注意事项
- 仅供学习和研究用途。
- 仅在 Windows 上使用；写入内存需要管理员权限。
- 使用前请备份游戏进度与相关数据。

---
本项目作者不对使用本工具产生的任何后果负责。
