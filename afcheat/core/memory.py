"""Windows 进程内存操作（原 KittyMemory）。

用于读取和写入其他进程的内存。

依赖：
- ctypes (Python 标准库)
- Windows API (kernel32.dll / psapi.dll)

注意：需要管理员权限才能修改其他进程的内存。
"""

import ctypes
from ctypes import wintypes
from typing import Optional

from ..constants import GAME_PROCESS_NAMES

# Windows API常量
PROCESS_ALL_ACCESS = 0x1F0FFF
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008

# 内存保护常量
PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_READ = 0x20
PAGE_READWRITE = 0x04
PAGE_READONLY = 0x02

# Windows API函数
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi


class _PROCESSENTRY32(ctypes.Structure):
    """CreateToolhelp32Snapshot 进程条目结构（原先在两处重复定义）。"""

    _fields_ = [
        ("dwSize", ctypes.c_ulong),
        ("cntUsage", ctypes.c_ulong),
        ("th32ProcessID", ctypes.c_ulong),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", ctypes.c_ulong),
        ("cntThreads", ctypes.c_ulong),
        ("th32ParentProcessID", ctypes.c_ulong),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", ctypes.c_ulong),
        ("szExeFile", ctypes.c_char * 260),
    ]


class _MODULEENTRY32(ctypes.Structure):
    """CreateToolhelp32Snapshot 模块条目结构。"""

    _fields_ = [
        ("dwSize", ctypes.c_ulong),
        ("th32ModuleID", ctypes.c_ulong),
        ("th32ProcessID", ctypes.c_ulong),
        ("GlblcntUsage", ctypes.c_ulong),
        ("ProccntUsage", ctypes.c_ulong),
        ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
        ("modBaseSize", ctypes.c_ulong),
        ("hModule", wintypes.HMODULE),
        ("szModule", ctypes.c_char * 256),
        ("szExePath", ctypes.c_char * 260),
    ]


class KittyMemory:
    """Windows进程内存操作类"""

    def __init__(self):
        self.process_handle = None
        self.process_id = None
        self.process_name = None
        self.force_pid = None  # 用于强制指定进程ID

    def _ensure_process_open(self) -> bool:
        """确保进程已打开"""
        if self.process_handle:
            # 检查句柄是否仍然有效
            exit_code = wintypes.DWORD()
            if kernel32.GetExitCodeProcess(self.process_handle, ctypes.byref(exit_code)):
                if exit_code.value == 259:  # STILL_ACTIVE
                    return True
                else:
                    # 进程已退出，关闭句柄
                    kernel32.CloseHandle(self.process_handle)
                    self.process_handle = None
                    self.process_id = None
                    self.process_name = None

        # 如果强制指定了PID，优先使用
        if self.force_pid is not None:
            self.process_handle = self._open_process(self.force_pid)
            if self.process_handle:
                self.process_id = self.force_pid
                self.process_name = self._get_process_name_by_pid(self.force_pid) or f"PID:{self.force_pid}"
                return True
            else:
                # 强制PID失败时，清除设置
                self.force_pid = None

        # 尝试打开进程 - 支持多种进程名变体
        for proc_name in GAME_PROCESS_NAMES:
            pid = self._get_process_id(proc_name)
            if pid:
                self.process_id = pid
                self.process_name = proc_name
                self.process_handle = self._open_process(pid)
                if self.process_handle:
                    return True

        return False

    def set_target_pid(self, pid: int):
        """设置目标进程ID"""
        self.force_pid = pid
        # 关闭当前进程句柄，强制重新打开
        if self.process_handle:
            kernel32.CloseHandle(self.process_handle)
            self.process_handle = None
            self.process_id = None
            self.process_name = None

    def get_base_address_by_pid(self, pid: int, module_name: str) -> Optional[int]:
        """根据PID获取模块基址"""
        # 临时设置PID
        old_force_pid = self.force_pid
        self.set_target_pid(pid)

        try:
            if self._ensure_process_open():
                return self._get_module_base_address(self.process_handle, module_name)
        finally:
            # 恢复原来的设置
            self.force_pid = old_force_pid
            if old_force_pid is None:
                # 如果原来没有强制PID，关闭当前句柄
                if self.process_handle:
                    kernel32.CloseHandle(self.process_handle)
                    self.process_handle = None
                    self.process_id = None
                    self.process_name = None

        return None

    def _get_process_id(self, process_name: str) -> Optional[int]:
        """根据进程名获取进程ID"""
        # 创建进程快照
        TH32CS_SNAPPROCESS = 0x2
        h_snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)

        if h_snapshot == -1:
            return None

        pe32 = _PROCESSENTRY32()
        pe32.dwSize = ctypes.sizeof(_PROCESSENTRY32)

        if not kernel32.Process32First(h_snapshot, ctypes.byref(pe32)):
            kernel32.CloseHandle(h_snapshot)
            return None

        while True:
            if pe32.szExeFile.decode('utf-8', errors='ignore').lower() == process_name.lower():
                kernel32.CloseHandle(h_snapshot)
                return pe32.th32ProcessID

            if not kernel32.Process32Next(h_snapshot, ctypes.byref(pe32)):
                break

        kernel32.CloseHandle(h_snapshot)
        return None

    def _open_process(self, process_id: int) -> Optional[int]:
        """打开进程句柄"""
        handle = kernel32.OpenProcess(
            PROCESS_ALL_ACCESS,
            False,
            process_id
        )
        return handle if handle else None

    def _get_process_name_by_pid(self, pid: int) -> Optional[str]:
        """根据PID获取进程名"""
        # 创建进程快照
        TH32CS_SNAPPROCESS = 0x2
        h_snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)

        if h_snapshot == -1:
            return None

        pe32 = _PROCESSENTRY32()
        pe32.dwSize = ctypes.sizeof(_PROCESSENTRY32)

        if not kernel32.Process32First(h_snapshot, ctypes.byref(pe32)):
            kernel32.CloseHandle(h_snapshot)
            return None

        while True:
            if pe32.th32ProcessID == pid:
                kernel32.CloseHandle(h_snapshot)
                return pe32.szExeFile.decode('utf-8', errors='ignore')

            if not kernel32.Process32Next(h_snapshot, ctypes.byref(pe32)):
                break

        kernel32.CloseHandle(h_snapshot)
        return None

    def _get_module_base_address(self, process_handle: int, module_name: str) -> Optional[int]:
        """获取模块基址"""
        # 方法1: 使用EnumProcessModules
        modules = (ctypes.POINTER(wintypes.HMODULE) * 1024)()
        needed = ctypes.c_ulong()

        if psapi.EnumProcessModules(
            process_handle,
            ctypes.byref(modules),
            ctypes.sizeof(modules),
            ctypes.byref(needed)
        ):
            module_count = needed.value // ctypes.sizeof(wintypes.HMODULE)

            for i in range(module_count):
                module_handle = modules[i]
                module_name_buf = ctypes.create_string_buffer(260)

                if psapi.GetModuleBaseNameA(
                    process_handle,
                    module_handle,
                    module_name_buf,
                    260
                ):
                    if module_name_buf.value.decode('utf-8', errors='ignore').lower() == module_name.lower():
                        return ctypes.cast(module_handle, ctypes.c_void_p).value

        # 方法2: 使用CreateToolhelp32Snapshot
        TH32CS_SNAPMODULE = 0x8
        TH32CS_SNAPMODULE32 = 0x10

        h_snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, self.process_id)
        if h_snapshot == -1:
            return None

        me32 = _MODULEENTRY32()
        me32.dwSize = ctypes.sizeof(_MODULEENTRY32)

        if kernel32.Module32First(h_snapshot, ctypes.byref(me32)):
            while True:
                if me32.szModule.decode('utf-8', errors='ignore').lower() == module_name.lower():
                    base_addr = ctypes.cast(me32.modBaseAddr, ctypes.c_void_p).value
                    kernel32.CloseHandle(h_snapshot)
                    return base_addr

                if not kernel32.Module32Next(h_snapshot, ctypes.byref(me32)):
                    break

        kernel32.CloseHandle(h_snapshot)
        return None

    def get_base_address(self, module_name: str) -> Optional[int]:
        """获取指定模块的基址"""
        if not self._ensure_process_open():
            return None

        # 获取模块基址
        return self._get_module_base_address(self.process_handle, module_name)

    def read_bytes(self, address: int, length: int) -> Optional[bytes]:
        """从指定地址读取内存"""
        if not self._ensure_process_open():
            raise Exception("无法打开进程，请确保游戏正在运行")

        buffer = ctypes.create_string_buffer(length)
        bytes_read = ctypes.c_size_t()

        if kernel32.ReadProcessMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            buffer,
            length,
            ctypes.byref(bytes_read)
        ):
            return buffer.raw[:bytes_read.value]
        else:
            error = kernel32.GetLastError()
            raise Exception(f"读取内存失败，错误代码: {error}")

    def write_bytes(self, address: int, data: bytes) -> bool:
        """向指定地址写入内存"""
        if not self._ensure_process_open():
            raise Exception("无法打开进程，请确保游戏正在运行")

        # 修改内存保护属性
        old_protect = wintypes.DWORD()
        if not kernel32.VirtualProtectEx(
            self.process_handle,
            ctypes.c_void_p(address),
            len(data),
            PAGE_EXECUTE_READWRITE,
            ctypes.byref(old_protect)
        ):
            error = kernel32.GetLastError()
            raise Exception(f"修改内存保护失败，错误代码: {error}")

        # 写入内存
        bytes_written = ctypes.c_size_t()
        buffer = ctypes.create_string_buffer(data)

        success = kernel32.WriteProcessMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            buffer,
            len(data),
            ctypes.byref(bytes_written)
        )

        # 恢复内存保护属性
        restore_protect = wintypes.DWORD()
        kernel32.VirtualProtectEx(
            self.process_handle,
            ctypes.c_void_p(address),
            len(data),
            old_protect,
            ctypes.byref(restore_protect)
        )

        if not success:
            error = kernel32.GetLastError()
            raise Exception(f"写入内存失败，错误代码: {error}")

        return bytes_written.value == len(data)

    def pattern_scan(self, pattern: bytes, start_address: int, end_address: int) -> Optional[int]:
        """在内存范围内搜索字节模式"""
        if not self._ensure_process_open():
            return None

        chunk_size = 0x10000  # 64KB chunks
        current_addr = start_address

        while current_addr < end_address:
            try:
                read_size = min(chunk_size, end_address - current_addr)
                data = self.read_bytes(current_addr, read_size)

                if data:
                    # 在数据中搜索模式
                    index = data.find(pattern)
                    if index != -1:
                        return current_addr + index

                current_addr += read_size
            except Exception:
                current_addr += chunk_size

        return None

    def close(self):
        """关闭进程句柄"""
        if self.process_handle:
            kernel32.CloseHandle(self.process_handle)
            self.process_handle = None


# 创建全局实例
_instance = KittyMemory()


def get_base_address(module_name: str) -> Optional[int]:
    """获取模块基址（全局函数）"""
    return _instance.get_base_address(module_name)


def get_base_address_by_pid(pid: int, module_name: str) -> Optional[int]:
    """根据PID获取模块基址（全局函数）"""
    return _instance.get_base_address_by_pid(pid, module_name)


def read_bytes(address: int, length: int) -> Optional[bytes]:
    """读取内存（全局函数）"""
    return _instance.read_bytes(address, length)


def write_bytes(address: int, data: bytes) -> bool:
    """写入内存（全局函数）"""
    return _instance.write_bytes(address, data)


def pattern_scan(pattern: bytes, start_address: int, end_address: int) -> Optional[int]:
    """模式扫描（全局函数）"""
    return _instance.pattern_scan(pattern, start_address, end_address)
