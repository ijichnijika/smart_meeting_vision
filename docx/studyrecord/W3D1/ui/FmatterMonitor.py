# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'FmatterMonitor.ui'
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

class Ui_FmatterMonitorForm(object):
    def setupUi(self, FmatterMonitorForm):
        if not FmatterMonitorForm.objectName():
            FmatterMonitorForm.setObjectName(u"FmatterMonitorForm")
        FmatterMonitorForm.resize(800, 600)
        self.gridLayout = QGridLayout(FmatterMonitorForm)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_img = QLabel(FmatterMonitorForm)
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
        self.horizontalSpacer_1 = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_1)

        self.label_nest = QLabel(FmatterMonitorForm)
        self.label_nest.setObjectName(u"label_nest")

        self.horizontalLayout.addWidget(self.label_nest)

        self.lcdNumber_nest = QLCDNumber(FmatterMonitorForm)
        self.lcdNumber_nest.setObjectName(u"lcdNumber_nest")
        self.lcdNumber_nest.setMinimumSize(QSize(60, 30))
        self.lcdNumber_nest.setDigitCount(4)

        self.horizontalLayout.addWidget(self.lcdNumber_nest)

        self.label_kite = QLabel(FmatterMonitorForm)
        self.label_kite.setObjectName(u"label_kite")

        self.horizontalLayout.addWidget(self.label_kite)

        self.lcdNumber_kite = QLCDNumber(FmatterMonitorForm)
        self.lcdNumber_kite.setObjectName(u"lcdNumber_kite")
        self.lcdNumber_kite.setMinimumSize(QSize(60, 30))
        self.lcdNumber_kite.setDigitCount(4)

        self.horizontalLayout.addWidget(self.lcdNumber_kite)

        self.label_plastic = QLabel(FmatterMonitorForm)
        self.label_plastic.setObjectName(u"label_plastic")

        self.horizontalLayout.addWidget(self.label_plastic)

        self.lcdNumber_plastic = QLCDNumber(FmatterMonitorForm)
        self.lcdNumber_plastic.setObjectName(u"lcdNumber_plastic")
        self.lcdNumber_plastic.setMinimumSize(QSize(60, 30))
        self.lcdNumber_plastic.setDigitCount(4)

        self.horizontalLayout.addWidget(self.lcdNumber_plastic)

        self.label_balloon = QLabel(FmatterMonitorForm)
        self.label_balloon.setObjectName(u"label_balloon")

        self.horizontalLayout.addWidget(self.label_balloon)

        self.lcdNumber_balloon = QLCDNumber(FmatterMonitorForm)
        self.lcdNumber_balloon.setObjectName(u"lcdNumber_balloon")
        self.lcdNumber_balloon.setMinimumSize(QSize(60, 30))
        self.lcdNumber_balloon.setDigitCount(4)

        self.horizontalLayout.addWidget(self.lcdNumber_balloon)

        self.label_tip = QLabel(FmatterMonitorForm)
        self.label_tip.setObjectName(u"label_tip")

        self.horizontalLayout.addWidget(self.label_tip)

        self.horizontalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.pushButton_save_video = QPushButton(FmatterMonitorForm)
        self.pushButton_save_video.setObjectName(u"pushButton_save_video")

        self.horizontalLayout_2.addWidget(self.pushButton_save_video)

        self.pushButton_snapshot = QPushButton(FmatterMonitorForm)
        self.pushButton_snapshot.setObjectName(u"pushButton_snapshot")

        self.horizontalLayout_2.addWidget(self.pushButton_snapshot)

        self.pushButton_open_video = QPushButton(FmatterMonitorForm)
        self.pushButton_open_video.setObjectName(u"pushButton_open_video")

        self.horizontalLayout_2.addWidget(self.pushButton_open_video)


        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)


        self.retranslateUi(FmatterMonitorForm)

        QMetaObject.connectSlotsByName(FmatterMonitorForm)
    # setupUi

    def retranslateUi(self, FmatterMonitorForm):
        FmatterMonitorForm.setWindowTitle(QCoreApplication.translate("FmatterMonitorForm", u"\u5f02\u7269\u76d1\u63a7", None))
        self.label_img.setText(QCoreApplication.translate("FmatterMonitorForm", u"\u76d1\u63a7\u89c6\u9891", None))
        self.label_nest.setText(QCoreApplication.translate("FmatterMonitorForm", u"\u9e1f\u5de2\uff1a", None))
        self.label_kite.setText(QCoreApplication.translate("FmatterMonitorForm", u"\u98ce\u7b5d\uff1a", None))
        self.label_plastic.setText(QCoreApplication.translate("FmatterMonitorForm", u"\u5851\u6599\uff1a", None))
        self.label_balloon.setText(QCoreApplication.translate("FmatterMonitorForm", u"\u6c14\u7403\uff1a", None))
        self.label_tip.setText(QCoreApplication.translate("FmatterMonitorForm", u"\u63d0\u793a\uff1a", None))
        self.pushButton_save_video.setText(QCoreApplication.translate("FmatterMonitorForm", u"\u4fdd\u5b58\u89c6\u9891", None))
        self.pushButton_snapshot.setText(QCoreApplication.translate("FmatterMonitorForm", u"\u4fdd\u5b58\u5feb\u7167", None))
        self.pushButton_open_video.setText(QCoreApplication.translate("FmatterMonitorForm", u"\u6253\u5f00\u89c6\u9891", None))
    # retranslateUi

