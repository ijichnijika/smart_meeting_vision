# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TruckMonitor.ui'
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

class Ui_TruckMonitorForm(object):
    def setupUi(self, TruckMonitorForm):
        if not TruckMonitorForm.objectName():
            TruckMonitorForm.setObjectName(u"TruckMonitorForm")
        TruckMonitorForm.resize(800, 600)
        self.gridLayout = QGridLayout(TruckMonitorForm)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_img = QLabel(TruckMonitorForm)
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

        self.label_crane = QLabel(TruckMonitorForm)
        self.label_crane.setObjectName(u"label_crane")

        self.horizontalLayout.addWidget(self.label_crane)

        self.lcdNumber_crane = QLCDNumber(TruckMonitorForm)
        self.lcdNumber_crane.setObjectName(u"lcdNumber_crane")
        self.lcdNumber_crane.setMinimumSize(QSize(80, 30))
        self.lcdNumber_crane.setDigitCount(5)

        self.horizontalLayout.addWidget(self.lcdNumber_crane)

        self.label_tower_crane = QLabel(TruckMonitorForm)
        self.label_tower_crane.setObjectName(u"label_tower_crane")

        self.horizontalLayout.addWidget(self.label_tower_crane)

        self.lcdNumber_tower_crane = QLCDNumber(TruckMonitorForm)
        self.lcdNumber_tower_crane.setObjectName(u"lcdNumber_tower_crane")
        self.lcdNumber_tower_crane.setMinimumSize(QSize(80, 30))
        self.lcdNumber_tower_crane.setDigitCount(5)

        self.horizontalLayout.addWidget(self.lcdNumber_tower_crane)

        self.label_tip = QLabel(TruckMonitorForm)
        self.label_tip.setObjectName(u"label_tip")

        self.horizontalLayout.addWidget(self.label_tip)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.pushButton_save_video = QPushButton(TruckMonitorForm)
        self.pushButton_save_video.setObjectName(u"pushButton_save_video")

        self.horizontalLayout_2.addWidget(self.pushButton_save_video)

        self.pushButton_snapshot = QPushButton(TruckMonitorForm)
        self.pushButton_snapshot.setObjectName(u"pushButton_snapshot")

        self.horizontalLayout_2.addWidget(self.pushButton_snapshot)

        self.pushButton_open_video = QPushButton(TruckMonitorForm)
        self.pushButton_open_video.setObjectName(u"pushButton_open_video")

        self.horizontalLayout_2.addWidget(self.pushButton_open_video)


        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)


        self.retranslateUi(TruckMonitorForm)

        QMetaObject.connectSlotsByName(TruckMonitorForm)
    # setupUi

    def retranslateUi(self, TruckMonitorForm):
        TruckMonitorForm.setWindowTitle(QCoreApplication.translate("TruckMonitorForm", u"\u5de5\u7a0b\u8f66\u76d1\u63a7", None))
        self.label_img.setText(QCoreApplication.translate("TruckMonitorForm", u"\u76d1\u63a7\u89c6\u9891", None))
        self.label_crane.setText(QCoreApplication.translate("TruckMonitorForm", u"\u540a\u8f66\uff1a", None))
        self.label_tower_crane.setText(QCoreApplication.translate("TruckMonitorForm", u"\u5854\u540a\uff1a", None))
        self.label_tip.setText(QCoreApplication.translate("TruckMonitorForm", u"\u63d0\u793a\uff1a", None))
        self.pushButton_save_video.setText(QCoreApplication.translate("TruckMonitorForm", u"\u4fdd\u5b58\u89c6\u9891", None))
        self.pushButton_snapshot.setText(QCoreApplication.translate("TruckMonitorForm", u"\u4fdd\u5b58\u5feb\u7167", None))
        self.pushButton_open_video.setText(QCoreApplication.translate("TruckMonitorForm", u"\u6253\u5f00\u89c6\u9891", None))
    # retranslateUi

