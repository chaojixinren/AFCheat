"""运行中进程的枚举与过滤。"""

import logging
from dataclasses import dataclass
from typing import List

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """进程信息数据类"""

    pid: int
    name: str
    exe_path: str = ""
    memory_info: str = ""


def enumerate_processes() -> List[ProcessInfo]:
    """枚举所有运行中的进程（过滤掉系统进程和内存占用很小的进程）。"""
    processes: List[ProcessInfo] = []

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

    except Exception:
        logger.exception("枚举进程失败")
        return processes
