"""
Pytest 全局共享 Fixtures 与 Qt 环境配置
"""

import os
import pytest
from PySide6.QtWidgets import QApplication

# 确保所有测试均在无头环境下高速执行
os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """保证整个测试会话期间全局唯一且合法的 QApplication 实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(["--platform", "offscreen"])
    yield app
