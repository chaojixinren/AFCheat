"""Amazing Frog 游戏修改核心逻辑：定位函数并应用/恢复补丁。"""

import logging

try:
    import psutil
except ImportError:
    psutil = None

from ..constants import (
    AMMO_OFFSET,
    AMMO_ORIGINAL_BYTES,
    APP_ORIGINAL_BYTES,
    APP_UNLOCK_OFFSET,
    DISK_OFFSET,
    DISK_ORIGINAL_BYTES,
    FORCE_RETURN_TRUE,
    FUNCTION_PROLOGUE_BYTES,
    GAME_MODULE,
    MONEY_PATCHES,
    TOY_OFFSET,
    TOY_ORIGINAL_BYTES,
    UNLOCK_OFFSET,
    UNLOCK_ORIGINAL_BYTES,
)
from . import memory

logger = logging.getLogger(__name__)


class AmazingFrogCheat:
    """Amazing Frog 游戏修改核心类"""

    def __init__(self):
        self.gameassembly_base = None
        self.unlock_addr = None
        self.ammo_check_addr = None
        self.app_unlock_addr = None
        self.toy_unlock_addr = None
        self.disk_unlock_addr = None
        self.original_unlock_bytes = None
        self.original_ammo_bytes = None
        self.original_app_unlock_bytes = None
        self.original_toy_bytes = None
        self.original_disk_bytes = None
        self.original_money_patches = None

        # 进程相关
        self.selected_pid = None
        self.process_name = "Amazing Frog.exe"  # 默认进程名

        self.costume_unlocked = False
        self.infinite_ammo_enabled = False
        self.apps_unlocked = False
        self.toys_unlocked = False
        self.disks_unlocked = False
        self.infinite_money_enabled = False

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

    def _locate_function(self, offset: int):
        """按偏移读取函数入口；首字节命中序言集合即视为命中的函数入口。"""
        test_addr = self.gameassembly_base + offset
        try:
            bytes_at_addr = memory.read_bytes(test_addr, 10)
        except Exception:
            logger.exception("读取函数地址 0x%X 失败", test_addr)
            return None
        if bytes_at_addr and bytes_at_addr[0] in FUNCTION_PROLOGUE_BYTES:
            return test_addr
        return None

    def find_functions(self) -> tuple[bool, bool]:
        """查找需要修改的函数地址"""
        if not self.gameassembly_base:
            if not self.get_base_address():
                return False, False

        self.unlock_addr = self._locate_function(UNLOCK_OFFSET)
        self.ammo_check_addr = self._locate_function(AMMO_OFFSET)
        self.app_unlock_addr = self._locate_function(APP_UNLOCK_OFFSET)

        return self.unlock_addr is not None, self.ammo_check_addr is not None

    def find_money_function(self) -> bool:
        """确认可以应用金钱补丁（只需模块基址可用，逐项校验在 enable 时进行）。"""
        if not self.gameassembly_base and not self.get_base_address():
            return False
        return True

    def find_app_unlock_function(self) -> bool:
        """查找手机 APP 解锁函数地址（fjAchievementObject.IsUnlocked）。"""
        if not self.gameassembly_base and not self.get_base_address():
            return False
        self.app_unlock_addr = self._locate_function(APP_UNLOCK_OFFSET)
        return self.app_unlock_addr is not None

    def find_toy_unlock_function(self) -> bool:
        """查找玩具解锁判定函数地址（fjSavedInformation.IsItemUnlocked）。"""
        if not self.gameassembly_base and not self.get_base_address():
            return False
        self.toy_unlock_addr = self._locate_function(TOY_OFFSET)
        return self.toy_unlock_addr is not None

    def find_disk_unlock_function(self) -> bool:
        """查找软盘解锁判定函数地址（fjSavedInformation.IsFAPSDiskUnlocked）。"""
        if not self.gameassembly_base and not self.get_base_address():
            return False
        self.disk_unlock_addr = self._locate_function(DISK_OFFSET)
        return self.disk_unlock_addr is not None

    def _apply_force_true(self, addr: int, expected: bytes):
        """应用 FORCE_RETURN_TRUE，返回可用于恢复的原始字节；失败返回 None。

        目标已是补丁态（上次未恢复）时，返回 expected 作为兜底原字节。
        """
        current = memory.read_bytes(addr, len(FORCE_RETURN_TRUE))
        if not current or len(current) < len(FORCE_RETURN_TRUE):
            return None
        if current[:len(FORCE_RETURN_TRUE)] == FORCE_RETURN_TRUE:
            return expected
        if current[:len(expected)] != expected:
            logger.warning("目标 0x%X 字节与预期原字节不符（游戏可能已更新）：%s",
                           addr, current.hex(" "))
            return None
        memory.write_bytes(addr, FORCE_RETURN_TRUE)
        return current

    def _restore_force_true(self, addr: int, original, expected: bytes) -> bool:
        """还原 FORCE_RETURN_TRUE 补丁；original 缺失且当前是补丁态时用 expected 兜底。"""
        if not addr:
            return False
        data = original
        if data is None:
            current = memory.read_bytes(addr, len(FORCE_RETURN_TRUE))
            if not current or current[:len(FORCE_RETURN_TRUE)] != FORCE_RETURN_TRUE:
                return False
            data = expected
        memory.write_bytes(addr, data)
        return True

    def unlock_all_costumes(self) -> bool:
        """解锁所有皮肤"""
        if not self.unlock_addr:
            return False
        try:
            original = self._apply_force_true(self.unlock_addr, UNLOCK_ORIGINAL_BYTES)
            if original is None:
                return False
            self.original_unlock_bytes = original
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
            original = self._apply_force_true(self.ammo_check_addr, AMMO_ORIGINAL_BYTES)
            if original is None:
                return False
            self.original_ammo_bytes = original
            self.infinite_ammo_enabled = True
            return True
        except Exception:
            logger.exception("无限子弹补丁写入失败")
            return False

    def unlock_all_apps(self) -> bool:
        """解锁所有手机 APP（强制成就判定为已达成）"""
        if not self.app_unlock_addr:
            return False
        try:
            original = self._apply_force_true(self.app_unlock_addr, APP_ORIGINAL_BYTES)
            if original is None:
                return False
            self.original_app_unlock_bytes = original
            self.apps_unlocked = True
            return True
        except Exception:
            logger.exception("解锁手机 APP 补丁写入失败")
            return False

    def unlock_all_toys(self) -> bool:
        """解锁所有玩具（强制道具解锁判定为已解锁）"""
        if not self.toy_unlock_addr:
            return False
        try:
            original = self._apply_force_true(self.toy_unlock_addr, TOY_ORIGINAL_BYTES)
            if original is None:
                return False
            self.original_toy_bytes = original
            self.toys_unlocked = True
            return True
        except Exception:
            logger.exception("解锁玩具补丁写入失败")
            return False

    def unlock_all_disks(self) -> bool:
        """解锁所有软盘（强制 FAPS 地图软盘判定为已解锁）"""
        if not self.disk_unlock_addr:
            return False
        try:
            original = self._apply_force_true(self.disk_unlock_addr, DISK_ORIGINAL_BYTES)
            if original is None:
                return False
            self.original_disk_bytes = original
            self.disks_unlocked = True
            return True
        except Exception:
            logger.exception("解锁软盘补丁写入失败")
            return False

    def _apply_patches(self, patches, label: str):
        """按 (RVA, 期望原字节, 补丁字节) 逐项校验后写入，返回 [(addr, 原字节)]；失败返回 None。"""
        if not self.gameassembly_base and not self.get_base_address():
            return None

        saved = []
        try:
            for offset, expected, patch in patches:
                addr = self.gameassembly_base + offset
                original = memory.read_bytes(addr, len(patch))
                if not original or len(original) < len(patch):
                    logger.warning("读取%s补丁目标 0x%X 失败，跳过", label, offset)
                    continue
                if original[:len(expected)] == expected:
                    memory.write_bytes(addr, patch)
                    saved.append((addr, original))
                elif original[:len(patch)] == patch:
                    # 已经是补丁态（例如上一次未恢复），记录期望原字节以便恢复
                    saved.append((addr, expected))
                else:
                    logger.warning(
                        "%s补丁目标 0x%X 字节不匹配（游戏可能已更新），跳过：%s",
                        label, offset, original.hex(" "),
                    )
                    continue
            return saved
        except Exception:
            logger.exception("%s补丁写入失败，回滚", label)
            for addr, original in reversed(saved):
                try:
                    memory.write_bytes(addr, original)
                except Exception:
                    logger.exception("回滚%s补丁 0x%X 失败", label, addr)
            return None

    def _restore_patches(self, saved, patches, label: str) -> bool:
        """还原补丁；saved 缺失时对当前仍是补丁态的目标用已知原字节兜底。"""
        if not saved:
            if not self.gameassembly_base and not self.get_base_address():
                return False
            saved = []
            for offset, expected, patch in patches:
                addr = self.gameassembly_base + offset
                current = memory.read_bytes(addr, len(patch))
                if current and current[:len(patch)] == patch:
                    saved.append((addr, expected))
            if not saved:
                return False
        try:
            for addr, original in saved:
                memory.write_bytes(addr, original)
            return True
        except Exception:
            logger.exception("恢复%s修改失败", label)
            return False

    def enable_infinite_money(self) -> bool:
        """启用无限金钱：把显示路径直接读取的几个函数/指令改为固定返回大数。"""
        saved = self._apply_patches(MONEY_PATCHES, "无限金钱")
        if not saved:
            return False
        self.original_money_patches = saved
        self.infinite_money_enabled = True
        return True

    def restore_original(self) -> tuple[bool, bool, bool, bool, bool, bool]:
        """恢复原始代码"""
        return (
            self.restore_costume_unlock(),
            self.restore_infinite_ammo(),
            self.restore_app_unlock(),
            self.restore_toys_unlock(),
            self.restore_disks_unlock(),
            self.restore_infinite_money(),
        )

    def restore_costume_unlock(self) -> bool:
        """仅恢复“解锁全部皮肤”相关修改"""
        if not self.unlock_addr:
            return False
        try:
            ok = self._restore_force_true(self.unlock_addr, self.original_unlock_bytes,
                                          UNLOCK_ORIGINAL_BYTES)
            if ok:
                self.costume_unlocked = False
            return ok
        except Exception:
            logger.exception("恢复皮肤解锁修改失败")
            return False

    def restore_infinite_ammo(self) -> bool:
        """仅恢复“无限子弹”相关修改"""
        if not self.ammo_check_addr:
            return False
        try:
            ok = self._restore_force_true(self.ammo_check_addr, self.original_ammo_bytes,
                                          AMMO_ORIGINAL_BYTES)
            if ok:
                self.infinite_ammo_enabled = False
            return ok
        except Exception:
            logger.exception("恢复无限子弹修改失败")
            return False

    def restore_app_unlock(self) -> bool:
        """仅恢复“解锁全部手机 APP”相关修改"""
        if not self.app_unlock_addr:
            return False
        try:
            ok = self._restore_force_true(self.app_unlock_addr, self.original_app_unlock_bytes,
                                          APP_ORIGINAL_BYTES)
            if ok:
                self.apps_unlocked = False
            return ok
        except Exception:
            logger.exception("恢复手机 APP 解锁修改失败")
            return False

    def restore_toys_unlock(self) -> bool:
        """仅恢复“解锁全部玩具”相关修改"""
        if not self.toy_unlock_addr:
            return False
        try:
            ok = self._restore_force_true(self.toy_unlock_addr, self.original_toy_bytes,
                                          TOY_ORIGINAL_BYTES)
            if ok:
                self.toys_unlocked = False
            return ok
        except Exception:
            logger.exception("恢复玩具解锁修改失败")
            return False

    def restore_disks_unlock(self) -> bool:
        """仅恢复“解锁全部软盘”相关修改"""
        if not self.disk_unlock_addr:
            return False
        try:
            ok = self._restore_force_true(self.disk_unlock_addr, self.original_disk_bytes,
                                          DISK_ORIGINAL_BYTES)
            if ok:
                self.disks_unlocked = False
            return ok
        except Exception:
            logger.exception("恢复软盘解锁修改失败")
            return False

    def restore_infinite_money(self) -> bool:
        """仅恢复“无限金钱”相关修改"""
        ok = self._restore_patches(self.original_money_patches, MONEY_PATCHES, "无限金钱")
        if ok:
            self.original_money_patches = None
            self.infinite_money_enabled = False
        return ok
