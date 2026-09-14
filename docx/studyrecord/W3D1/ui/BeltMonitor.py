# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'BeltMonitor.ui'
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

class Ui_BeltMonitorForm(object):
    def setupUi(self, BeltMonitorForm):
        if not BeltMonitorForm.objectName():
            BeltMonitorForm.setObjectName(u"BeltMonitorForm")
        BeltMonitorForm.resize(800, 600)
        self.gridLayout = QGridLayout(BeltMonitorForm)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_img = QLabel(BeltMonitorForm)
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

        self.label_angle = QLabel(BeltMonitorForm)
        self.label_angle.setObjectName(u"label_angle")

        self.horizontalLayout.addWidget(self.label_angle)

        self.lcdNumber_angle = QLCDNumber(BeltMonitorForm)
        self.lcdNumber_angle.setObjectName(u"lcdNumber_angle")
        self.lcdNumber_angle.setMinimumSize(QSize(80, 30))
        self.lcdNumber_angle.setDigitCount(6)

        self.horizontalLayout.addWidget(self.lcdNumber_angle)

        self.label_distance = QLabel(BeltMonitorForm)
        self.label_distance.setObjectName(u"label_distance")

        self.horizontalLayout.addWidget(self.label_distance)

        self.lcdNumber_distance = QLCDNumber(BeltMonitorForm)
        self.lcdNumber_distance.setObjectName(u"lcdNumber_distance")
        self.lcdNumber_distance.setMinimumSize(QSize(80, 30))
        self.lcdNumber_distance.setDigitCount(6)

        self.horizontalLayout.addWidget(self.lcdNumber_distance)

        self.label_tip = QLabel(BeltMonitorForm)
        self.label_tip.setObjectName(u"label_tip")

        self.horizontalLayout.addWidget(self.label_tip)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.pushButton_save_video = QPushButton(BeltMonitorForm)
        self.pushButton_save_video.setObjectName(u"pushButton_save_video")

        self.horizontalLayout_2.addWidget(self.pushButton_save_video)

        self.pushButton_snapshot = QPushButton(BeltMonitorForm)
        self.pushButton_snapshot.setObjectName(u"pushButton_snapshot")

        self.horizontalLayout_2.addWidget(self.pushButton_snapshot)

        self.pushButton_open_video = QPushButton(BeltMonitorForm)
        self.pushButton_open_video.setObjectName(u"pushButton_open_video")

        self.horizontalLayout_2.addWidget(self.pushButton_open_video)


        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)


        self.retranslateUi(BeltMonitorForm)

        QMetaObject.connectSlotsByName(BeltMonitorForm)
    # setupUi

    def retranslateUi(self, BeltMonitorForm):
        BeltMonitorForm.setWindowTitle(QCoreApplication.translate("BeltMonitorForm", u"\u76ae\u5e26\u76d1\u63a7\u6444\u50cf\u5934", None))
        self.label_img.setText(QCoreApplication.translate("BeltMonitorForm", u"\u76d1\u63a7\u89c6\u9891", None))
        self.label_angle.setText(QCoreApplication.translate("BeltMonitorForm", u"\u504f\u79fb\u89d2\u5ea6", None))
        self.label_distance.setText(QCoreApplication.translate("BeltMonitorForm", u"\u504f\u79fb\u8ddd\u79bb", None))
        self.label_tip.setText(QCoreApplication.translate("BeltMonitorForm", u"\u63d0\u793a\uff1a", None))
        self.pushButton_save_video.setText(QCoreApplication.translate("BeltMonitorForm", u"\u4fdd\u5b58\u89c6\u9891", None))
        self.pushButton_snapshot.setText(QCoreApplication.translate("BeltMonitorForm", u"\u4fdd\u5b58\u5feb\u7167", None))
        self.pushButton_open_video.setText(QCoreApplication.translate("BeltMonitorForm", u"\u6253\u5f00\u89c6\u9891", None))
    # retranslateUi

