"""Amazing Frog 游戏修改核心逻辑：定位函数并应用/恢复补丁。"""

import logging

try:
    import psutil
except ImportError:
    psutil = None

from ..constants import (
    AMMO_OFFSET,
    FORCE_RETURN_TRUE,
    FUNCTION_PROLOGUE_BYTES,
    GAME_MODULE,
    UNLOCK_OFFSET,
)
from . import memory

logger = logging.getLogger(__name__)


class AmazingFrogCheat:
    """Amazing Frog 游戏修改核心类"""

    def __init__(self):
        self.gameassembly_base = None
        self.unlock_addr = None
        self.ammo_check_addr = None
        self.original_unlock_bytes = None
        self.original_ammo_bytes = None

        # 进程相关
        self.selected_pid = None
        self.process_name = "Amazing Frog.exe"  # 默认进程名

        self.costume_unlocked = False
        self.infinite_ammo_enabled = False

    def set_target_process(self, pid: int, process_name: str):
        """设置目标进程"""
        self.selected_pid = pid
        self.process_name = process_name

    def validate_game_process(self, pid: int) -> bool:
        """验证进程是否是有效的Amazing Frog游戏进程"""
        if psutil is None:
            return False
        try:
            if not psutil.pid_exists(pid):
                return False

            # 尝试获取 GameAssembly.dll 基址来验证
            base_addr = memory.get_base_address_by_pid(pid, GAME_MODULE)
            return base_addr is not None

        except Exception:
            logger.exception("验证进程 %s 失败", pid)
            return False

    def get_base_address(self) -> bool:
        """获取 GameAssembly.dll 基址"""
        try:
            if self.selected_pid is not None:
                # 如果已选择特定进程，使用进程ID
                self.gameassembly_base = memory.get_base_address_by_pid(
                    self.selected_pid, GAME_MODULE
                )
            else:
                # 默认方式：通过进程名查找
                self.gameassembly_base = memory.get_base_address(GAME_MODULE)

            return self.gameassembly_base is not None
        except Exception:
            logger.exception("获取模块基址失败")
            return False

    def find_functions(self) -> tuple[bool, bool]:
        """查找需要修改的函数地址"""
        if not self.gameassembly_base:
            if not self.get_base_address():
                return False, False

        unlock_found = False
        ammo_found = False

        # 查找 IsCostumeItemUnlocked 函数
        if UNLOCK_OFFSET is not None:
            test_addr = self.gameassembly_base + UNLOCK_OFFSET
            try:
                bytes_at_addr = memory.read_bytes(test_addr, 10)
                if bytes_at_addr and bytes_at_addr[0] in FUNCTION_PROLOGUE_BYTES:
                    self.unlock_addr = test_addr
                    unlock_found = True
            except Exception:
                logger.exception("读取解锁函数地址 0x%X 失败", test_addr)

        # 查找 get_infiniteAmmo 函数
        if AMMO_OFFSET is not None:
            test_addr = self.gameassembly_base + AMMO_OFFSET
            try:
                bytes_at_addr = memory.read_bytes(test_addr, 10)
                if bytes_at_addr and bytes_at_addr[0] in FUNCTION_PROLOGUE_BYTES:
                    self.ammo_check_addr = test_addr
                    ammo_found = True
            except Exception:
                logger.exception("读取无限子弹函数地址 0x%X 失败", test_addr)

        return unlock_found, ammo_found

    def unlock_all_costumes(self) -> bool:
        """解锁所有皮肤"""
        if not self.unlock_addr:
            return False

        try:
            # 保存原始字节
            self.original_unlock_bytes = memory.read_bytes(
                self.unlock_addr, len(FORCE_RETURN_TRUE)
            )

            # 应用 patch：总是返回 true
            memory.write_bytes(self.unlock_addr, FORCE_RETURN_TRUE)
            self.costume_unlocked = True
            return True

        except Exception:
            logger.exception("解锁皮肤补丁写入失败")
            return False

    def enable_infinite_ammo(self) -> bool:
        """启用无限子弹"""
        if not self.ammo_check_addr:
            return False

        try:
            # 保存原始字节
            self.original_ammo_bytes = memory.read_bytes(
                self.ammo_check_addr, len(FORCE_RETURN_TRUE)
            )

            # 应用 patch：总是返回 true
            memory.write_bytes(self.ammo_check_addr, FORCE_RETURN_TRUE)
            self.infinite_ammo_enabled = True
            return True

        except Exception:
            logger.exception("无限子弹补丁写入失败")
            return False

    def restore_original(self) -> tuple[bool, bool]:
        """恢复原始代码"""
        return self.restore_costume_unlock(), self.restore_infinite_ammo()

    def restore_costume_unlock(self) -> bool:
        """仅恢复“解锁全部皮肤”相关修改"""
        if self.unlock_addr and self.original_unlock_bytes:
            try:
                memory.write_bytes(self.unlock_addr, self.original_unlock_bytes)
                self.costume_unlocked = False
                return True
            except Exception:
                logger.exception("恢复皮肤解锁修改失败")
                return False
        return False

    def restore_infinite_ammo(self) -> bool:
        """仅恢复“无限子弹”相关修改"""
        if self.ammo_check_addr and self.original_ammo_bytes:
            try:
                memory.write_bytes(self.ammo_check_addr, self.original_ammo_bytes)
                self.infinite_ammo_enabled = False
                return True
            except Exception:
                logger.exception("恢复无限子弹修改失败")
                return False
        return False
