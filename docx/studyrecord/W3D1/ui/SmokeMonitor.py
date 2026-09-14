# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'SmokeMonitor.ui'
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

class Ui_SmokeMonitorForm(object):
    def setupUi(self, SmokeMonitorForm):
        if not SmokeMonitorForm.objectName():
            SmokeMonitorForm.setObjectName(u"SmokeMonitorForm")
        SmokeMonitorForm.resize(800, 600)
        self.gridLayout = QGridLayout(SmokeMonitorForm)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_img = QLabel(SmokeMonitorForm)
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

        self.label_smoke = QLabel(SmokeMonitorForm)
        self.label_smoke.setObjectName(u"label_smoke")

        self.horizontalLayout.addWidget(self.label_smoke)

        self.lcdNumber_smoke = QLCDNumber(SmokeMonitorForm)
        self.lcdNumber_smoke.setObjectName(u"lcdNumber_smoke")
        self.lcdNumber_smoke.setMinimumSize(QSize(80, 30))
        self.lcdNumber_smoke.setDigitCount(5)

        self.horizontalLayout.addWidget(self.lcdNumber_smoke)

        self.label_fire = QLabel(SmokeMonitorForm)
        self.label_fire.setObjectName(u"label_fire")

        self.horizontalLayout.addWidget(self.label_fire)

        self.lcdNumber_fire = QLCDNumber(SmokeMonitorForm)
        self.lcdNumber_fire.setObjectName(u"lcdNumber_fire")
        self.lcdNumber_fire.setMinimumSize(QSize(80, 30))
        self.lcdNumber_fire.setDigitCount(5)

        self.horizontalLayout.addWidget(self.lcdNumber_fire)

        self.label_tip = QLabel(SmokeMonitorForm)
        self.label_tip.setObjectName(u"label_tip")

        self.horizontalLayout.addWidget(self.label_tip)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.pushButton_save_video = QPushButton(SmokeMonitorForm)
        self.pushButton_save_video.setObjectName(u"pushButton_save_video")

        self.horizontalLayout_2.addWidget(self.pushButton_save_video)

        self.pushButton_snapshot = QPushButton(SmokeMonitorForm)
        self.pushButton_snapshot.setObjectName(u"pushButton_snapshot")

        self.horizontalLayout_2.addWidget(self.pushButton_snapshot)

        self.pushButton_open_video = QPushButton(SmokeMonitorForm)
        self.pushButton_open_video.setObjectName(u"pushButton_open_video")

        self.horizontalLayout_2.addWidget(self.pushButton_open_video)


        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)


        self.retranslateUi(SmokeMonitorForm)

        QMetaObject.connectSlotsByName(SmokeMonitorForm)
    # setupUi

    def retranslateUi(self, SmokeMonitorForm):
        SmokeMonitorForm.setWindowTitle(QCoreApplication.translate("SmokeMonitorForm", u"\u70df\u706b\u76d1\u63a7", None))
        self.label_img.setText(QCoreApplication.translate("SmokeMonitorForm", u"\u76d1\u63a7\u89c6\u9891", None))
        self.label_smoke.setText(QCoreApplication.translate("SmokeMonitorForm", u"\u70df\uff1a", None))
        self.label_fire.setText(QCoreApplication.translate("SmokeMonitorForm", u"\u706b\uff1a", None))
        self.label_tip.setText(QCoreApplication.translate("SmokeMonitorForm", u"\u63d0\u793a\uff1a", None))
        self.pushButton_save_video.setText(QCoreApplication.translate("SmokeMonitorForm", u"\u4fdd\u5b58\u89c6\u9891", None))
        self.pushButton_snapshot.setText(QCoreApplication.translate("SmokeMonitorForm", u"\u4fdd\u5b58\u5feb\u7167", None))
        self.pushButton_open_video.setText(QCoreApplication.translate("SmokeMonitorForm", u"\u6253\u5f00\u89c6\u9891", None))
    # retranslateUi

