"""
系统全局配置与路径管理模块。
"""

import os
import sys
from pathlib import Path


def _get_base_dir() -> Path:
    """获取打包静态资源根目录。"""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", sys.executable)).resolve()
    return Path(__file__).resolve().parent.parent


def _get_data_dir() -> Path:
    """获取应用可写数据根目录（兼容打包后只读应用包沙盒）。"""
    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "SmartMeetingVision"
        elif sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
            return base / "SmartMeetingVision"
        else:
            return Path.home() / ".smart_meeting_vision"
    return Path(__file__).resolve().parent.parent / "data"


BASE_DIR = _get_base_dir()
DATA_DIR = _get_data_dir()

# 只读静态资源目录（权重与示例视频优先从静态包或本地项目读取）
WEIGHTS_DIR = BASE_DIR / "data" / "weights"
DEMO_VIDEOS_DIR = BASE_DIR / "data" / "demo_videos"

# 可写运行时目录
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
REPORTS_DIR = DATA_DIR / "reports"
LOGS_DIR = DATA_DIR / "logs"
DB_PATH = DATA_DIR / "meeting_vision.db"


def ensure_data_dirs():
    """创建运行时所需的可写数据目录，由应用启动入口显式调用。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


# 优先选用标准权重，缺失时按体积逐级降级回退至轻量模型
DEFAULT_YOLO_WEIGHTS = WEIGHTS_DIR / "yolov8n.pt"
if not DEFAULT_YOLO_WEIGHTS.exists():
    DEFAULT_YOLO_WEIGHTS = WEIGHTS_DIR / "best.pt"

BEHAVIOR_WEIGHTS = WEIGHTS_DIR / "best.pt"

POSE_WEIGHTS = WEIGHTS_DIR / "yolov8n-pose.pt"

DEFAULT_DEMO_VIDEO = DEMO_VIDEOS_DIR / "meeting_cctv_continuous_stream.mp4"
if not DEFAULT_DEMO_VIDEO.exists():
    DEFAULT_DEMO_VIDEO = DEMO_VIDEOS_DIR / "meeting_surveillance_long_1.mp4"

APP_NAME = "Smart Meeting Vision"
APP_SUBTITLE = "智能会议签到与出勤分析系统"
APP_VERSION = "1.0.0"

WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 760
DEFAULT_WINDOW_WIDTH = 1380
DEFAULT_WINDOW_HEIGHT = 860

LEFT_PANEL_WIDTH = 290
RIGHT_PANEL_WIDTH = 330

# 会议远景中被遮挡人员置信度偏低，由后续追踪器二次确认；高IoU阈值防止肩并肩邻座包围框被NMS误抑制
CONF_THRESHOLD = 0.15
IOU_THRESHOLD = 0.65
TARGET_FPS = 30

# 自动截图与行为告警防抖参数
ALERT_COOLDOWN_SECONDS = 30.0          # 单目标分心行为告警与截图冷却时间 (秒)
DISTRACTION_CONFIRM_FRAMES = 3         # 触发分心告警所需连续确认帧数 (过滤单帧误检)
SEAT_LEAVE_COOLDOWN_SECONDS = 30.0     # 单工位离席告警与截图冷却时间 (秒)
MIN_SNAPSHOT_INTERVAL = 3.0            # 全局最小截图间隔 (秒)，防止并发爆刷截图
SEAT_ABSENT_DEBOUNCE_FRAMES = 30       # 工位离席防抖帧数 (约 1 秒防抖缓冲)
SEAT_RECOVERY_FRAMES = 3               # 工位恢复在席所需连续确认帧数 (防止单帧噪点闪烁)
SEAT_ABSENT_SECONDS = 4.0              # 工位离席持续秒数判定阈值
ENABLE_AUTO_SNAPSHOT = True            # 是否启用告警触发时自动截取证据快照


INITIAL_ATTENDEES = [
    {"id": "EMP001", "name": "夏一帆", "department": "研发一部", "role": "项目负责人", "status": "present", "track_id": "#1"},
    {"id": "EMP002", "name": "张文远", "department": "研发一部", "role": "视觉算法工程师", "status": "present", "track_id": "#2"},
    {"id": "EMP003", "name": "李晓冉", "department": "产品设计部", "role": "UI/UX 设计师", "status": "present", "track_id": "#3"},
    {"id": "EMP004", "name": "王浩宇", "department": "研发二部", "role": "前端工程师", "status": "present", "track_id": "#4"},
    {"id": "EMP005", "name": "陈梓萱", "department": "质量保障部", "role": "测试工程师", "status": "present", "track_id": "#5"},
    {"id": "EMP006", "name": "周思廷", "department": "研发一部", "role": "架构师", "status": "absent", "track_id": None},
    {"id": "EMP007", "name": "黄建勋", "department": "项目管理部", "role": "Scrum Master", "status": "present", "track_id": "#6"},
    {"id": "EMP008", "name": "赵梦洁", "department": "人力资源部", "role": "考勤专员", "status": "present", "track_id": "#7"},
    {"id": "EMP009", "name": "孙启航", "department": "运维支持部", "role": "系统工程师", "status": "absent", "track_id": None},
    {"id": "EMP010", "name": "杨嘉怡", "department": "产品设计部", "role": "产品助理", "status": "present", "track_id": "#8"},
    {"id": "EMP011", "name": "吴博文", "department": "研发二部", "role": "后端开发", "status": "present", "track_id": "#9"},
    {"id": "EMP012", "name": "刘宇轩", "department": "研发二部", "role": "移动端开发", "status": "absent", "track_id": None},
]
