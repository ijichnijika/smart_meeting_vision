"""
界面样式主题与色彩规范。
"""


class ThemeColors:
    WINDOW_BG = "#F8FAFC"
    PANEL_BG = "#FFFFFF"
    PANEL_MUTED = "#F1F5F9"
    SURFACE_HOVER = "#F8FAFC"
    SURFACE_ACTIVE = "#E2E8F0"

    BORDER_SUBTLE = "#F1F5F9"
    BORDER_LIGHT = "#E2E8F0"
    BORDER_MUTED = "#CBD5E1"
    BORDER_FOCUS = "#2563EB"

    TEXT_PRIMARY = "#0F172A"
    TEXT_SECONDARY = "#334155"
    TEXT_MUTED = "#64748B"
    TEXT_PLACEHOLDER = "#94A3B8"

    PRIMARY = "#2563EB"
    PRIMARY_HOVER = "#1D4ED8"
    PRIMARY_ACTIVE = "#1E40AF"
    PRIMARY_LIGHT = "#EFF6FF"
    PRIMARY_BORDER = "#BFDBFE"

    SUCCESS = "#059669"
    SUCCESS_BG = "#ECFDF5"
    SUCCESS_BORDER = "#A7F3D0"
    SUCCESS_TEXT = "#047857"

    WARNING = "#D97706"
    WARNING_BG = "#FFFBEB"
    WARNING_BORDER = "#FDE68A"
    WARNING_TEXT = "#B45309"

    DANGER = "#DC2626"
    DANGER_BG = "#FEF2F2"
    DANGER_BORDER = "#FECACA"
    DANGER_TEXT = "#991B1B"

    CANVAS_BG = "#0B0F19"
    CANVAS_GRID = "#182032"
    BOX_PERSON = "#3B82F6"
    BOX_DISTRACT = "#DC2626"
    BOX_SELECTED = "#8B5CF6"
    BOX_SEAT = "#059669"

    AVATAR_PALETTE = [
        ("#EEF2FF", "#4338CA"),
        ("#ECFDF5", "#047857"),
        ("#F0FDF4", "#15803D"),
        ("#FEF3C7", "#B45309"),
        ("#F1F5F9", "#334155"),
        ("#FAF5FF", "#7E22CE"),
        ("#EFF6FF", "#1D4ED8"),
        ("#FFF1F2", "#BE123C"),
    ]



PURE_WHITE_STYLESHEET = f"""
/* 全局基础设置 */
QWidget {{
    background-color: transparent;
    color: {ThemeColors.TEXT_PRIMARY};
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
    outline: none;
}}

QMainWindow {{
    background-color: {ThemeColors.WINDOW_BG};
}}

/* 容器与面板卡片 */
QFrame.modern-card {{
    background-color: {ThemeColors.PANEL_BG};
    border: 1px solid {ThemeColors.BORDER_LIGHT};
    border-radius: 10px;
}}

QFrame#topNav {{
    background-color: {ThemeColors.PANEL_BG};
    border-bottom: 1px solid {ThemeColors.BORDER_LIGHT};
    padding: 0px 20px;
}}

/* 文本标题层级 */
QLabel.heading-1 {{
    font-size: 15px;
    font-weight: 700;
    color: {ThemeColors.TEXT_PRIMARY};
}}

QLabel.heading-2 {{
    font-size: 13px;
    font-weight: 600;
    color: {ThemeColors.TEXT_PRIMARY};
}}

QLabel.text-secondary {{
    font-size: 12px;
    color: {ThemeColors.TEXT_MUTED};
}}

QLabel.metric-value {{
    font-size: 24px;
    font-weight: 700;
    color: {ThemeColors.TEXT_PRIMARY};
}}

/* 核心主按钮 */
QPushButton#btnPrimary,
QPushButton[class="btn-primary"],
QPushButton.btn-primary {{
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #2563EB;
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton#btnPrimary:hover,
QPushButton[class="btn-primary"]:hover,
QPushButton.btn-primary:hover {{
    background-color: #1D4ED8;
    border-color: #1D4ED8;
}}
QPushButton#btnPrimary:pressed,
QPushButton[class="btn-primary"]:pressed,
QPushButton.btn-primary:pressed {{
    background-color: #1E40AF;
    border-color: #1E40AF;
}}

/* 次级操作按钮 */
QPushButton[class="btn-secondary"],
QPushButton.btn-secondary {{
    background-color: #FFFFFF;
    color: #334155;
    font-weight: 500;
    font-size: 12px;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 6px 12px;
}}
QPushButton[class="btn-secondary"]:hover,
QPushButton.btn-secondary:hover {{
    background-color: #F8FAFC;
    border-color: #CBD5E1;
    color: #0F172A;
}}
QPushButton[class="btn-secondary"]:pressed,
QPushButton.btn-secondary:pressed {{
    background-color: #E2E8F0;
}}

/* 危险/动作按钮 */
QPushButton[class="btn-danger"],
QPushButton.btn-danger {{
    background-color: #FEF2F2;
    color: #DC2626;
    font-weight: 500;
    border: 1px solid #FECACA;
    border-radius: 6px;
    padding: 6px 12px;
}}
QPushButton[class="btn-danger"]:hover,
QPushButton.btn-danger:hover {{
    background-color: #FEE2E2;
}}

/* 输入框 */
QLineEdit {{
    background-color: {ThemeColors.PANEL_BG};
    color: {ThemeColors.TEXT_PRIMARY};
    border: 1px solid {ThemeColors.BORDER_LIGHT};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    selection-background-color: {ThemeColors.PRIMARY_LIGHT};
    selection-color: {ThemeColors.PRIMARY};
}}
QLineEdit:hover {{
    border-color: {ThemeColors.BORDER_MUTED};
}}
QLineEdit:focus {{
    border: 1px solid {ThemeColors.BORDER_FOCUS};
    background-color: #FFFFFF;
}}
QLineEdit::placeholder {{
    color: {ThemeColors.TEXT_PLACEHOLDER};
}}

/* 下拉选择框 */
QComboBox {{
    background-color: {ThemeColors.PANEL_BG};
    color: {ThemeColors.TEXT_PRIMARY};
    border: 1px solid {ThemeColors.BORDER_LIGHT};
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
}}
QComboBox:hover {{
    border-color: {ThemeColors.BORDER_MUTED};
    background-color: {ThemeColors.SURFACE_HOVER};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {ThemeColors.PANEL_BG};
    border: 1px solid {ThemeColors.BORDER_LIGHT};
    border-radius: 6px;
    selection-background-color: {ThemeColors.PRIMARY_LIGHT};
    selection-color: {ThemeColors.PRIMARY};
    padding: 4px;
}}

/* 滚动条 */
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 5px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {ThemeColors.BORDER_MUTED};
    border-radius: 2.5px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ThemeColors.TEXT_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* 细分割线 */
QFrame.divider {{
    background-color: {ThemeColors.BORDER_LIGHT};
    max-height: 1px;
    border: none;
}}

/* 提示窗 */
QToolTip {{
    background-color: #0F172A;
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}}

/* 面板容器统一规则 */
AttendeePanel, QFrame#attendeePanel {{
    background-color: {ThemeColors.PANEL_BG};
    border-right: 1px solid {ThemeColors.BORDER_LIGHT};
}}

StatsPanel, QFrame#statsPanel {{
    background-color: {ThemeColors.PANEL_BG};
    border-left: 1px solid {ThemeColors.BORDER_LIGHT};
}}

ControlBar, QFrame#controlBar {{
    background-color: {ThemeColors.PANEL_BG};
    border: 1px solid {ThemeColors.BORDER_LIGHT};
    border-radius: 10px;
}}
"""
