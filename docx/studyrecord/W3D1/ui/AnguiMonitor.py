# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'AnguiMonitor.ui'
##
## Created by: Qt User Interface Compiler version 6.10.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLCDNumber,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QWidget)

class Ui_AnguiMonitorForm(object):
    def setupUi(self, AnguiMonitorForm):
        if not AnguiMonitorForm.objectName():
            AnguiMonitorForm.setObjectName(u"AnguiMonitorForm")
        AnguiMonitorForm.resize(800, 600)
        self.gridLayout = QGridLayout(AnguiMonitorForm)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_img = QLabel(AnguiMonitorForm)
        self.label_img.setObjectName(u"label_img")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.label_img.sizePolicy().hasHeightForWidth())
        self.label_img.setSizePolicy(sizePolicy)
        self.label_img.setMinimumSize(QSize(480, 320))
        self.label_img.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.label_img, 0, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_1)

        self.label_helmet = QLabel(AnguiMonitorForm)
        self.label_helmet.setObjectName(u"label_helmet")

        self.horizontalLayout.addWidget(self.label_helmet)

        self.lcdNumber_helmet = QLCDNumber(AnguiMonitorForm)
        self.lcdNumber_helmet.setObjectName(u"lcdNumber_helmet")
        self.lcdNumber_helmet.setMinimumSize(QSize(80, 30))
        self.lcdNumber_helmet.setDigitCount(5)

        self.horizontalLayout.addWidget(self.lcdNumber_helmet)

        self.label_no_helmet = QLabel(AnguiMonitorForm)
        self.label_no_helmet.setObjectName(u"label_no_helmet")

        self.horizontalLayout.addWidget(self.label_no_helmet)

        self.lcdNumber_no_helmet = QLCDNumber(AnguiMonitorForm)
        self.lcdNumber_no_helmet.setObjectName(u"lcdNumber_no_helmet")
        self.lcdNumber_no_helmet.setMinimumSize(QSize(80, 30))
        self.lcdNumber_no_helmet.setDigitCount(5)

        self.horizontalLayout.addWidget(self.lcdNumber_no_helmet)

        self.label_tip = QLabel(AnguiMonitorForm)
        self.label_tip.setObjectName(u"label_tip")

        self.horizontalLayout.addWidget(self.label_tip)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.pushButton_save_video = QPushButton(AnguiMonitorForm)
        self.pushButton_save_video.setObjectName(u"pushButton_save_video")

        self.horizontalLayout_2.addWidget(self.pushButton_save_video)

        self.pushButton_snapshot = QPushButton(AnguiMonitorForm)
        self.pushButton_snapshot.setObjectName(u"pushButton_snapshot")

        self.horizontalLayout_2.addWidget(self.pushButton_snapshot)

        self.pushButton_open_video = QPushButton(AnguiMonitorForm)
        self.pushButton_open_video.setObjectName(u"pushButton_open_video")

        self.horizontalLayout_2.addWidget(self.pushButton_open_video)


        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)


        self.retranslateUi(AnguiMonitorForm)

        QMetaObject.connectSlotsByName(AnguiMonitorForm)
    # setupUi

    def retranslateUi(self, AnguiMonitorForm):
        AnguiMonitorForm.setWindowTitle(QCoreApplication.translate("AnguiMonitorForm", u"\u5b89\u5168\u5e3d\u4f69\u6234\u76d1\u63a7", None))
        self.label_img.setText(QCoreApplication.translate("AnguiMonitorForm", u"\u76d1\u63a7\u89c6\u9891", None))
        self.label_helmet.setText(QCoreApplication.translate("AnguiMonitorForm", u"\u5e26\u5b89\u5168\u5e3d\uff1a", None))
        self.label_no_helmet.setText(QCoreApplication.translate("AnguiMonitorForm", u"\u4e0d\u5e26\u5b89\u5168\u5e3d\uff1a", None))
        self.label_tip.setText(QCoreApplication.translate("AnguiMonitorForm", u"\u63d0\u793a\uff1a", None))
        self.pushButton_save_video.setText(QCoreApplication.translate("AnguiMonitorForm", u"\u4fdd\u5b58\u89c6\u9891", None))
        self.pushButton_snapshot.setText(QCoreApplication.translate("AnguiMonitorForm", u"\u4fdd\u5b58\u5feb\u7167", None))
        self.pushButton_open_video.setText(QCoreApplication.translate("AnguiMonitorForm", u"\u6253\u5f00\u89c6\u9891", None))
    # retranslateUi

