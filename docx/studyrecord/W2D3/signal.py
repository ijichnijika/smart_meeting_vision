import sys
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton, QWidget


class MainWindow(QWidget):
    closeSignal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("信号与槽示例")
        self.resize(250, 120)

        button = QPushButton("点击关闭窗口", self)
        button.setGeometry(50, 40, 150, 40)
        button.clicked.connect(self.onClicked)
        self.closeSignal.connect(self.onClose)

    def onClicked(self):
        self.closeSignal.emit()

    def onClose(self):
        QMessageBox.information(self, "提示", "接收到自定义关闭信号，窗口即将退出！", QMessageBox.StandardButton.Yes)
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
