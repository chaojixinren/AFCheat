"""全局常量：游戏偏移量、补丁字节、进程标识、界面配色与文案。

集中放这里，方便换游戏版本时一处修改。
"""

# ---------------------------------------------------------------------------
# 游戏 / 内存
# ---------------------------------------------------------------------------
GAME_MODULE = "GameAssembly.dll"

# Amazing Frog PC 版本函数偏移（相对 GameAssembly.dll 基址）
UNLOCK_OFFSET = 0x740AF0   # IsCostumeItemUnlocked
AMMO_OFFSET = 0x65BAF0     # get_infiniteAmmo

# 强制函数返回 true：mov rax, 1; ret
FORCE_RETURN_TRUE = bytes([0x48, 0xC7, 0xC0, 0x01, 0x00, 0x00, 0x00, 0xC3])

# 函数首字节可能是这些值之一（用于粗判偏移是否命中函数入口）
FUNCTION_PROLOGUE_BYTES = (0x40, 0x48, 0x55, 0xE9)

# 尝试匹配的进程名（大小写不敏感），兼容不同版本/平台的命名
GAME_PROCESS_NAMES = (
    "AmazingFrog.exe",
    "Amazing Frog.exe",
    "AmazingFrog",
    "Amazing Frog",
    "amazingfrog.exe",
    "amazing frog.exe",
)

# ---------------------------------------------------------------------------
# 窗口
# ---------------------------------------------------------------------------
WINDOW_TITLE = "AFCheat v1.0 -by 超級の新人"
WINDOW_SIZE = "1000x800"
WINDOW_MINSIZE = (960, 720)

AUTHOR_INFO = (
    "本程序仅供学习交流，请勿倒卖。作者：超級の新人 | QQ：3488993732 | "
    "群：364969455 | 适用 QMMT part 6.35"
)

# ---------------------------------------------------------------------------
# 字体
# ---------------------------------------------------------------------------
FONT_FAMILY = "Microsoft YaHei"
FONT_MONO = "Consolas"
FONT_EMOJI = "Segoe UI Emoji"

# ---------------------------------------------------------------------------
# 配色
# ---------------------------------------------------------------------------
COLOR_BG = "#f0f2f5"          # 窗口背景
COLOR_CARD = "#ffffff"        # 卡片背景
COLOR_SUBTLE = "#f8fafc"      # 卡片标题栏 / 浅底
COLOR_SUBTLE_ALT = "#f1f5f9"  # 作者信息条 / 表头
COLOR_BORDER = "#e2e8f0"
COLOR_TEXT = "#0f172a"        # 主标题
COLOR_TEXT_STRONG = "#334155"
COLOR_TEXT_MUTED = "#64748b"
COLOR_TEXT_SOFT = "#475569"
COLOR_ROW_ALT = "#f8fafc"     # 表格斑马纹
COLOR_ROW_SELECT = "#e0f2fe"  # 表格选中行

# 按钮主题色：(底色, 悬停, 按下)
COLOR_PRIMARY = ("#3b82f6", "#2563eb", "#1d4ed8")
COLOR_SUCCESS = ("#10b981", "#059669", "#047857")
COLOR_WARNING = ("#f59e0b", "#d97706", "#b45309")
COLOR_DANGER = ("#ef4444", "#dc2626", "#b91c1c")

COLOR_ACCENT = COLOR_PRIMARY[0]
COLOR_STATUS = COLOR_SUCCESS[1]
