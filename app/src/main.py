"""
智能会议签到与出勤分析系统启动入口。
"""

import os
import sys

# 限制底层线性代数库多线程并发
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import signal
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.src.common import get_logger
from app.src.ui import MainWindow

logger = get_logger("app_main")


def main():
    """主程序入口。"""
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    logger.info("正在启动 Smart Meeting Vision 桌面客户端...")

    app = QApplication(sys.argv)
    app.setApplicationName("SmartMeetingVision")
    app.setOrganizationName("NJIT-SE232")

    # Qt 的 C++ 事件循环会阻塞 Python 信号传递，通过周期性定时器唤醒 Python 解释器处理 SIGINT
    interrupt_timer = QTimer()
    interrupt_timer.timeout.connect(lambda: None)
    interrupt_timer.start(500)

    window = MainWindow(enable_yolo=True)
    window.show()

    logger.info("主窗口已呈现，进入 Qt 应用程序主循环。")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
