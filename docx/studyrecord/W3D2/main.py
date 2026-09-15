import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMdiArea,
    QMdiSubWindow,
)

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from monitor_setup_dialog import MyMonitorSetupDialog
from belt_monitor import MyBeltMonitorForm


def setup_logger():
    os.makedirs('./log', exist_ok=True)
    logger = logging.getLogger('belt_logger')
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = RotatingFileHandler(
            './log/belt_monitor.log', maxBytes=1024 * 1024, backupCount=10, encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


class MainWindow(QMainWindow):
    def __init__(self, cfgfile: str = './conf/config.yaml'):
        super().__init__()
        self.cfgfile = cfgfile
        self.logger = logging.getLogger('belt_logger')

        self.setWindowTitle('多输送带智能监控与参数配置系统')
        self.resize(1200, 850)

        self.mdi = QMdiArea()
        self.mdi.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdi.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setCentralWidget(self.mdi)

        self.sub_windows = {}

        self._init_actions()
        self._init_menus()
        self._init_toolbars()
        self.statusBar().showMessage('系统就绪')

    def _init_actions(self):
        icon_b1 = QIcon('./icons/camera_belt1.png') if os.path.exists('./icons/camera_belt1.png') else QIcon()
        icon_b2 = QIcon('./icons/camera_belt2.png') if os.path.exists('./icons/camera_belt2.png') else QIcon()
        icon_b3 = QIcon('./icons/camera_belt3.png') if os.path.exists('./icons/camera_belt3.png') else QIcon()

        self.belt1_action = QAction(icon_b1, '皮带 1 监控', self, checkable=True)
        self.belt1_action.triggered.connect(self.addBelt1Monitor)

        self.belt2_action = QAction(icon_b2, '皮带 2 监控', self, checkable=True)
        self.belt2_action.triggered.connect(self.addBelt2Monitor)

        self.belt3_action = QAction(icon_b3, '皮带 3 监控', self, checkable=True)
        self.belt3_action.triggered.connect(self.addBelt3Monitor)

        self.confBelt1Action = QAction('配置皮带 1', self)
        self.confBelt1Action.triggered.connect(self.confBelt1)

        self.confBelt2Action = QAction('配置皮带 2', self)
        self.confBelt2Action.triggered.connect(self.confBelt2)

        self.confBelt3Action = QAction('配置皮带 3', self)
        self.confBelt3Action.triggered.connect(self.confBelt3)

        self.tileAction = QAction('窗口平铺', self)
        self.tileAction.triggered.connect(self.mdi.tileSubWindows)

        self.cascadeAction = QAction('窗口层叠', self)
        self.cascadeAction.triggered.connect(self.mdi.cascadeSubWindows)

        self.exitAction = QAction('退出系统', self)
        self.exitAction.triggered.connect(self.close)

    def _init_menus(self):
        menubar = self.menuBar()

        monitor_menu = menubar.addMenu('监控视图')
        monitor_menu.addAction(self.belt1_action)
        monitor_menu.addAction(self.belt2_action)
        monitor_menu.addAction(self.belt3_action)
        monitor_menu.addSeparator()
        monitor_menu.addAction(self.tileAction)
        monitor_menu.addAction(self.cascadeAction)
        monitor_menu.addSeparator()
        monitor_menu.addAction(self.exitAction)

        self.configMenu = menubar.addMenu('系统配置')
        self.configMenu.addAction(self.confBelt1Action)
        self.configMenu.addAction(self.confBelt2Action)
        self.configMenu.addAction(self.confBelt3Action)

    def _init_toolbars(self):
        toolbar = self.addToolBar('主工具栏')
        toolbar.addAction(self.belt1_action)
        toolbar.addAction(self.belt2_action)
        toolbar.addAction(self.belt3_action)
        toolbar.addSeparator()
        toolbar.addAction(self.confBelt1Action)
        toolbar.addAction(self.confBelt2Action)
        toolbar.addAction(self.confBelt3Action)

    def _toggle_monitor(self, belt_id: int, state: bool, action: QAction, title: str):
        if state:
            widget = MyBeltMonitorForm(belt_id, self.cfgfile)
            sub_win = QMdiSubWindow()
            sub_win.setWidget(widget)
            sub_win.setWindowTitle(title)
            sub_win.resize(600, 480)
            self.mdi.addSubWindow(sub_win)
            sub_win.show()

            sub_win.destroyed.connect(lambda: action.setChecked(False))
            self.sub_windows[belt_id] = sub_win
            self.logger.info(f'Opened monitor window for belt_{belt_id}')
        else:
            if belt_id in self.sub_windows:
                sub_win = self.sub_windows.pop(belt_id)
                sub_win.close()
                self.logger.info(f'Closed monitor window for belt_{belt_id}')

    def addBelt1Monitor(self, state):
        self._toggle_monitor(0, state, self.belt1_action, '皮带 1 监控')

    def addBelt2Monitor(self, state):
        self._toggle_monitor(1, state, self.belt2_action, '皮带 2 监控')

    def addBelt3Monitor(self, state):
        self._toggle_monitor(2, state, self.belt3_action, '皮带 3 监控')

    def confBelt1(self):
        self._open_config(0)

    def confBelt2(self):
        self._open_config(1)

    def confBelt3(self):
        self._open_config(2)

    def _open_config(self, belt_id: int):
        self.logger.info(f'Opening configuration dialog for belt_{belt_id}')
        dialog = MyMonitorSetupDialog(belt_id, self.cfgfile, self)
        dialog.setModal(True)
        dialog.exec()

    def closeEvent(self, event):
        for sub_win in list(self.sub_windows.values()):
            if sub_win.widget():
                sub_win.widget().close()
        self.logger.info('MainWindow closed.')
        event.accept()


if __name__ == '__main__':
    setup_logger()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
