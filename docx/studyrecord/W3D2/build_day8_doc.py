import os
import sys
import docx
from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import xml.sax.saxutils as saxutils

def make_p_title(text):
    escaped = saxutils.escape(text)
    p_xml = f'''<w:p {nsdecls("w")}>
        <w:pPr>
            <w:spacing w:before="120" w:after="240" w:line="300" w:lineRule="auto"/>
            <w:jc w:val="center"/>
        </w:pPr>
        <w:r>
            <w:rPr>
                <w:rFonts w:ascii="黑体" w:eastAsia="黑体" w:hAnsi="黑体"/>
                <w:b/>
                <w:sz w:val="28"/>
                <w:lang w:eastAsia="zh-CN"/>
            </w:rPr>
            <w:t xml:space="preserve">{escaped}</w:t>
        </w:r>
    </w:p>'''
    return parse_xml(p_xml)

def make_p_heading1(text):
    escaped = saxutils.escape(text)
    p_xml = f'''<w:p {nsdecls("w")}>
        <w:pPr>
            <w:keepNext/>
            <w:spacing w:before="240" w:after="120" w:line="300" w:lineRule="auto"/>
        </w:pPr>
        <w:r>
            <w:rPr>
                <w:rFonts w:ascii="黑体" w:eastAsia="黑体" w:hAnsi="黑体"/>
                <w:b/>
                <w:sz w:val="26"/>
                <w:lang w:eastAsia="zh-CN"/>
            </w:rPr>
            <w:t xml:space="preserve">{escaped}</w:t>
        </w:r>
    </w:p>'''
    return parse_xml(p_xml)

def make_p_task(text):
    escaped = saxutils.escape(text)
    p_xml = f'''<w:p {nsdecls("w")}>
        <w:pPr>
            <w:keepNext/>
            <w:spacing w:before="180" w:after="80" w:line="288" w:lineRule="auto"/>
        </w:pPr>
        <w:r>
            <w:rPr>
                <w:rFonts w:ascii="黑体" w:eastAsia="黑体" w:hAnsi="黑体"/>
                <w:b/>
                <w:sz w:val="23"/>
                <w:lang w:eastAsia="zh-CN"/>
            </w:rPr>
            <w:t xml:space="preserve">{escaped}</w:t>
        </w:r>
    </w:p>'''
    return parse_xml(p_xml)

def make_p_subheading(text):
    escaped = saxutils.escape(text)
    p_xml = f'''<w:p {nsdecls("w")}>
        <w:pPr>
            <w:keepNext/>
            <w:spacing w:before="120" w:after="60" w:line="276" w:lineRule="auto"/>
        </w:pPr>
        <w:r>
            <w:rPr>
                <w:rFonts w:ascii="黑体" w:eastAsia="黑体" w:hAnsi="黑体"/>
                <w:b/>
                <w:sz w:val="21"/>
                <w:lang w:eastAsia="zh-CN"/>
            </w:rPr>
            <w:t xml:space="preserve">{escaped}</w:t>
        </w:r>
    </w:p>'''
    return parse_xml(p_xml)

def make_p_body(text):
    escaped = saxutils.escape(text)
    p_xml = f'''<w:p {nsdecls("w")}>
        <w:pPr>
            <w:spacing w:before="40" w:after="80" w:line="288" w:lineRule="auto"/>
        </w:pPr>
        <w:r>
            <w:rPr>
                <w:rFonts w:ascii="宋体" w:eastAsia="宋体" w:hAnsi="宋体"/>
                <w:sz w:val="21"/>
                <w:lang w:eastAsia="zh-CN"/>
            </w:rPr>
            <w:t xml:space="preserve">{escaped}</w:t>
        </w:r>
    </w:p>'''
    return parse_xml(p_xml)

def make_p_code(lines):
    runs_xml = []
    for idx, line in enumerate(lines):
        escaped = saxutils.escape(line)
        runs_xml.append(f'<w:t xml:space="preserve">{escaped}</w:t>')
        if idx < len(lines) - 1:
            runs_xml.append('<w:br/>')
    content = "".join(runs_xml)
    p_xml = f'''<w:p {nsdecls("w")}>
        <w:pPr>
            <w:spacing w:before="80" w:after="120" w:line="252" w:lineRule="auto"/>
            <w:shd w:val="clear" w:color="auto" w:fill="F8F9FA"/>
        </w:pPr>
        <w:r>
            <w:rPr>
                <w:rFonts w:ascii="Consolas" w:eastAsia="Consolas" w:hAnsi="Consolas"/>
                <w:sz w:val="18"/>
                <w:lang w:eastAsia="zh-CN"/>
            </w:rPr>
            {content}
        </w:r>
    </w:p>'''
    return parse_xml(p_xml)

def update_table_cell(cell, text, bold=False, font_size=21, font_family="宋体", align="left"):
    cell.text = ""
    p = cell.paragraphs[0]
    pPr = p._p.get_or_add_pPr()
    sp = parse_xml(f'<w:spacing {nsdecls("w")} w:before="40" w:after="40" w:line="240" w:lineRule="auto"/>')
    pPr.append(sp)
    if align != "left":
        jc = parse_xml(f'<w:jc {nsdecls("w")} w:val="{align}"/>')
        pPr.append(jc)

    run = p.add_run(text)
    rPr = run._r.get_or_add_rPr()
    rFonts = parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="{font_family}" w:eastAsia="{font_family}" w:hAnsi="{font_family}"/>')
    sz = parse_xml(f'<w:sz {nsdecls("w")} w:val="{font_size}"/>')
    lang = parse_xml(f'<w:lang {nsdecls("w")} w:eastAsia="zh-CN"/>')
    rPr.append(rFonts)
    rPr.append(sz)
    rPr.append(lang)
    if bold:
        b = parse_xml(f'<w:b {nsdecls("w")}/>')
        rPr.append(b)

def build_document():
    template_path = "W3D1/day_7.docx"
    doc = Document(template_path)

    # 1. Update Table 0 (Metadata)
    t0 = doc.tables[0]
    update_table_cell(t0.rows[0].cells[0], "实训日期", bold=True, align="center")
    update_table_cell(t0.rows[0].cells[1], "2026年09月15日", align="center")
    update_table_cell(t0.rows[0].cells[2], "实训阶段", bold=True, align="center")
    update_table_cell(t0.rows[0].cells[3], "第3周 第2天（W3D2）", align="center")

    update_table_cell(t0.rows[1].cells[0], "学生姓名", bold=True, align="center")
    update_table_cell(t0.rows[1].cells[1], "夏一帆", align="center")
    update_table_cell(t0.rows[1].cells[2], "专业班级", bold=True, align="center")
    update_table_cell(t0.rows[1].cells[3], "软件工程232", align="center")

    update_table_cell(t0.rows[2].cells[0], "实训项目", bold=True, align="center")
    update_table_cell(t0.rows[2].cells[1], "智能会议签到与出勤分析系统", align="center")
    update_table_cell(t0.rows[2].cells[2], "指导教师", bold=True, align="center")
    update_table_cell(t0.rows[2].cells[3], "张冰", align="center")

    # 2. Update Table 1 (Automated Test Cases)
    t1 = doc.tables[1]
    update_table_cell(t1.rows[0].cells[0], "测试方法名称", bold=True, font_size=18, align="center")
    update_table_cell(t1.rows[0].cells[1], "用例测试关注点", bold=True, font_size=18, align="center")
    update_table_cell(t1.rows[0].cells[2], "断言目标与期望结果", bold=True, font_size=18, align="center")

    test_cases = [
        (
            "test_yaml_config_structure",
            "YAML 配置文件合法性与多设备参数完整性",
            "断言 config.yaml 存在且包含 belt_0/1/2 的 url, size, belt_width, angle_alarm, dist_alarm, 左右边界坐标",
        ),
        (
            "test_zimage_label_state_and_coordinates",
            "ZImageLabel 状态机迁移、线段边界记录与双向坐标换算",
            "断言支持 LEFT/RIGHT_BORDER 切换，设置并获取左右边界坐标，像素坐标到图像坐标映射正确",
        ),
        (
            "test_monitor_setup_dialog",
            "参数配置对话框初始化、界面联动与清除槽函数",
            "断言对话框成功读取 YAML 参数并在 LineEdit 中展示，断言 borderDrew 与 clearBorder 槽函数联动正确",
        ),
        (
            "test_video_source_parsing",
            "三类视频源类型自适应智能解析",
            "断言整数或数字字符串解析为 USB，rtsp/http 前缀解析为 RTSP，本地文件路径解析为 FILE",
        ),
        (
            "test_video_encode_process_queue",
            "基于缓冲队列的多线程异步视频录制写入",
            "断言 VideoEncodeProcess 线程安全写入帧队列，停止时正常退出并释放 VideoWriter 资源",
        ),
        (
            "test_alarm_sender_thread_queue",
            "告警数据封装、异步队列入队与网络发送防御",
            "断言 AlarmSenderThread 正确接收时间戳、设备ID、偏移量及图片 Base64 字典，非阻塞安全投递",
        ),
        (
            "test_belt_monitor_alarm_display",
            "监控窗体动态配置加载与距离/角度超限双重告警显示",
            "断言正常状态显示绿色正常，单项超限及双项同时超限时准确显示红色加粗“偏移角度超限 偏移距离超限”",
        ),
        (
            "test_main_window_mdi_actions",
            "MDI 多窗体集成管理框架、日志轮转初始化与菜单工具栏响应",
            "断言 RotatingFileHandler 日志正常生成，主窗口多皮带监控动作与配置对话框槽函数完备",
        ),
    ]

    for idx, (name, focus, expectation) in enumerate(test_cases, 1):
        update_table_cell(t1.rows[idx].cells[0], name, font_family="Consolas", font_size=16)
        update_table_cell(t1.rows[idx].cells[1], focus, font_family="宋体", font_size=16)
        update_table_cell(t1.rows[idx].cells[2], expectation, font_family="宋体", font_size=16)

    # 3. Assemble document paragraphs
    # Section A: Paragraphs before Table 0
    p_title = make_p_title("软件工程项目训练实训日志（第3周 第2天）")

    # Section B: Paragraphs between Table 0 and Table 1
    middle_paragraphs = [
        make_p_heading1("一、实训任务与目标"),
        make_p_body("1. 深入掌握 Qt 事件驱动处理机制与底层坐标变换体系，重写 mousePressEvent、mouseMoveEvent、mouseReleaseEvent、paintEvent 与 mouseDoubleClickEvent，设计并实现交互式图像标定标签控件 ZImageLabel。"),
        make_p_body("2. 掌握有限状态机（FSM）在鼠标连续拖拽划线轨迹跟踪中的工程应用，通过 DRAW_BEGIN、DRAW_MOVE 与 DRAW_DONE 状态流转，实现输送带左边界与右边界（DrawShape）的动态橡皮筋预览与精确矢量标定。"),
        make_p_body("3. 深入理解图像原始物理分辨率坐标系与屏幕控件渲染坐标系之间的纵横比自适应缩放（KeepAspectRatio）与几何偏置映射换算，消除窗口缩放对标定精度的影响。"),
        make_p_body("4. 设计并实现设备监控参数配置对话框 MyMonitorSetupDialog，实现视频源地址、边缘基准坐标、皮带物理宽度及告警阈值的可视化交互与 YAML 配置文件双向动态同步。"),
        make_p_body("5. 掌握工程配置文件（conf/config.yaml）对多设备实例（belt_0、belt_1、belt_2）的结构化组织与多级映射机制，彻底解耦算法逻辑与硬编码环境参数。"),
        make_p_body("6. 重构前台监控窗体 MyBeltMonitorForm 与后台识别推理线程 MyBeltProcess，通过配置字典动态加载运行参数，实现偏移距离与偏转角度超限的双重状态实时告警渲染。"),
        make_p_body("7. 掌握基于生产者-消费者设计模式的高并发视频录制架构，设计基于独立工作线程 VideoEncodeProcess 与线程安全缓冲队列 queue.Queue 的后台视频编码落盘机制，避免磁盘 I/O 阻塞 GUI 渲染主线程。"),
        make_p_body("8. 掌握工控系统三类视频输入源（本地视频文件、网络 RTSP 流媒体、工业 USB 相机）的类型判别枚举与自适应加载，实现流媒体中断检测与自动重连容灾保护。"),
        make_p_body("9. 遵循工程日志规范，配置基于 RotatingFileHandler 的日志轮转机制，在关键业务节点统一打印结构化日志并自动分割；构建异步 HTTP POST 告警分发机制，上报包含时间戳、设备编号、偏移量与图片 Base64 编码的结构化告警报文。"),
        make_p_body("10. 构建基于 QMdiArea 的多输送带并行监控与配置调度主窗口，编写覆盖配置文件解析、交互式标定状态机、异步视频录制队列、告警数据组包及 MDI 菜单联动的 pytest 全流程自动化单元测试套件。"),

        make_p_heading1("二、任务完成与实现过程"),

        # Task 1
        make_p_task("任务一：基于自定义交互控件 ZImageLabel 的图像边界标定"),
        make_p_subheading("1. 题目描述与要求"),
        make_p_body("在输送带跑偏监测系统中，输送带运行时的基准位置需要由工程人员在摄像头采集的快照基准图上进行交互式设定。要求基于 PySide6 继承 QLabel 派生 ZImageLabel 控件，实现以下核心功能："),
        make_p_body("① 状态机机制：定义 Status 状态机枚举（DRAW_BEGIN、DRAW_MOVE、DRAW_DONE）及 DrawShape 形状枚举（LEFT_BORDER、RIGHT_BORDER）；"),
        make_p_body("② 实时动态拉线：鼠标左键按下记录起点，移动过程中发射重绘并以虚线绘制动态橡皮筋线段，左键松开后锁定终点并固化线段；"),
        make_p_body("③ 坐标映射换算：准确消除控件保持宽高比居中缩放引入的黑色留边偏移与缩放比例差异，将屏幕像素坐标准确折算至快照原图的真实物理像素坐标（如 1920×1080）；"),
        make_p_body("④ 信号与清除重置：支持鼠标双击重置清除已有标定线段，通过自定义 Qt 信号 borderDrew(bool, list) 与 clearBorder() 将线段类型与原始图像坐标实时上报给宿主对话框。"),
        make_p_subheading("2. 核心代码实现"),
        make_p_body("在 zimage_label.py 中设计状态机流转与像素坐标双向映射算法："),
        make_p_code([
            "class Status(Enum):",
            "    DRAW_BEGIN = 1",
            "    DRAW_MOVE = 2",
            "    DRAW_DONE = 3",
            "",
            "class DrawShape(Enum):",
            "    LEFT_BORDER = 0",
            "    RIGHT_BORDER = 1",
            "",
            "class ZImageLabel(QLabel):",
            "    borderDrew = Signal(bool, list)",
            "    clearBorder = Signal()",
            "",
            "    def _widget_to_image(self, wx: int, wy: int) -> QPoint:",
            "        if self._pixmap is None or self._pic is None:",
            "            return QPoint(wx, wy)",
            "        ox, oy, dw, dh = self._get_draw_offsets()",
            "        clamped_x = max(ox, min(wx, ox + dw))",
            "        clamped_y = max(oy, min(wy, oy + dh))",
            "        ratio_x = self._pixmap.width() / float(dw) if dw > 0 else 1.0",
            "        ratio_y = self._pixmap.height() / float(dh) if dh > 0 else 1.0",
            "        return QPoint(int((clamped_x - ox) * ratio_x), int((clamped_y - oy) * ratio_y))",
            "",
            "    def mouseReleaseEvent(self, event):",
            "        if event.button() == Qt.MouseButton.LeftButton and self.status in (Status.DRAW_BEGIN, Status.DRAW_MOVE):",
            "            self.status = Status.DRAW_DONE",
            "            p_start = self._widget_to_image(self._x_begin, self._y_begin)",
            "            p_end = self._widget_to_image(event.pos().x(), event.pos().y())",
            "            coords = [[p_start.x(), p_start.y()], [p_end.x(), p_end.y()]]",
            "            if self.shape == DrawShape.LEFT_BORDER:",
            "                self.left_border_img = coords",
            "                self.borderDrew.emit(True, coords)",
            "            else:",
            "                self.right_border_img = coords",
            "                self.borderDrew.emit(False, coords)",
            "            self.update()",
        ]),
        make_p_subheading("3. 运行测试与成果展示"),
        make_p_body("在终端中导入 ZImageLabel 模块并在无头环境下验证状态转移与坐标解算逻辑："),
        make_p_code([
            "$ /opt/homebrew/anaconda3/envs/python_project/bin/pytest W3D2/test_w3d2_homework.py -k test_zimage_label_state_and_coordinates -v",
            "W3D2/test_w3d2_homework.py::test_zimage_label_state_and_coordinates PASSED [100%]",
        ]),
        make_p_body("测试表明，在 640×480 渲染尺寸下，鼠标划取的屏幕坐标能够高保真映射回原始图纸空间，且左、右边界状态切换与双击复位机制响应精准可靠。"),

        # Task 2
        make_p_task("任务二：参数配置对话框 MonitorSetupDialog 与 YAML 多设备配置回写"),
        make_p_subheading("1. 题目描述与要求"),
        make_p_body("为满足现场多输送带独立调优的需求，基于 QDialog 构建 MyMonitorSetupDialog 参数配置对话框。要求支持传入输送带编号（beltID）及配置文件路径（cfgfile），在窗体初始化时自动解析 conf/config.yaml 对应配置段。对话框左侧集成 ZImageLabel 用于快照渲染与交互标定，支持“绘制左边界”/“绘制右边界”单选切换、“清除边界”、“抓取快照”（从当前配置视频源拉取首帧）与“打开快照”（本地选择静态图像）；右侧支持编辑视频源 URL、左右边界基准坐标、皮带物理宽度（mm）、偏移角度告警阈值（°）及偏移距离告警阈值（mm）。点击“保存配置”时执行格式校验并安全序列化回写 YAML 文件。"),
        make_p_subheading("2. 核心代码实现"),
        make_p_body("在 monitor_setup_dialog.py 中实现 YAML 数据反序列化读取与落盘保存逻辑："),
        make_p_code([
            "class MyMonitorSetupDialog(QDialog):",
            "    def __init__(self, beltID: int, cfgfile: str = './conf/config.yaml', parent=None):",
            "        super().__init__(parent)",
            "        self.beltID = beltID",
            "        self.beltID_str = f'belt_{beltID}'",
            "        self.cfgfile = cfgfile",
            "        self._init_ui()",
            "        self._load_config()",
            "",
            "    def getSnapshot(self):",
            "        url_text = self.lineEdit_url.text().strip()",
            "        video_source = int(url_text) if url_text.isdigit() else url_text",
            "        cap = cv2.VideoCapture(video_source)",
            "        if cap.isOpened():",
            "            success, frame = cap.read()",
            "            cap.release()",
            "            if success and frame is not None:",
            "                os.makedirs('./snapshot', exist_ok=True)",
            "                save_path = f'./snapshot/{self.beltID_str}_{int(time.time()*1000)}.jpg'",
            "                cv2.imwrite(save_path, frame)",
            "                self.snapshot_file = save_path",
            "                self.pixmap = QPixmap(save_path)",
            "                self.label_snapshot.setPixmapT(self.pixmap)",
            "",
            "    def saveConfig(self):",
            "        belt_dict = self.cfg.setdefault(self.beltID_str, {})",
            "        belt_dict['url'] = int(self.lineEdit_url.text()) if self.lineEdit_url.text().isdigit() else self.lineEdit_url.text()",
            "        belt_dict['belt_width'] = int(float(self.lineEdit_beltwidth.text()))",
            "        belt_dict['angle_alarm'] = float(self.lineEdit_angle.text())",
            "        belt_dict['dist_alarm'] = float(self.lineEdit_dist.text())",
            "        with open(self.cfgfile, 'w', encoding='utf-8') as f:",
            "            yaml.safe_dump(self.cfg, f, allow_unicode=True)",
            "        self.accept()",
        ]),
        make_p_subheading("3. 运行测试与成果展示"),
        make_p_body("在项目环境中运行测试，验证对话框对 YAML 属性的加载与持久化更新："),
        make_p_code([
            "$ /opt/homebrew/anaconda3/envs/python_project/bin/pytest W3D2/test_w3d2_homework.py -k test_monitor_setup_dialog -v",
            "W3D2/test_w3d2_homework.py::test_monitor_setup_dialog PASSED              [100%]",
        ]),
        make_p_body("执行断言结果显示，表单文本框完整呈现了 config.yaml 中的各字段参数，标定线段坐标变动能够实时同步至输入框，点击保存后文件成功持久化回写且格式完备。"),

        # Task 3
        make_p_task("任务三：监控窗口与识别线程参数解耦及超限双重告警联动"),
        make_p_subheading("1. 题目描述与要求"),
        make_p_body("全面重构 MyBeltProcess 识别推理线程与 MyBeltMonitorForm 监控前台窗体。MyBeltProcess 初始化时接收 beltID 与 cfg 字典，运行时动态提取目标通道的视频地址、基准左右边界向量及判定阈值，彻底移除原代码中所有硬编码参数。扩展识别完成信号为 done_signal = Signal(np.ndarray, float, float, np.ndarray)，将处理后的可视化帧、偏移距离、偏转角度以及原始帧同步推送至前台。前台窗体通过 QLCDNumber 刷新实时数值，并依据配置阈值执行多重状态判定：若偏转角度超限，显示“提示：偏移角度超限”；若偏移距离超限，显示“提示：偏移距离超限”；若两者同时超限，以红色加粗字体提示“提示：偏移角度超限 偏移距离超限”，指标回归正常时自动复位为绿色“提示：运行正常”。"),
        make_p_subheading("2. 核心代码实现"),
        make_p_body("在 belt_monitor.py 中实现动态参数解析与双超限告警判定逻辑："),
        make_p_code([
            "class MyBeltMonitorForm(QWidget):",
            "    def refresh_frame(self, frame: np.ndarray, distance: float, degree: float, org_frame: np.ndarray):",
            "        self.org_frame = org_frame.copy()",
            "        if self.writeVideo and self.videoEncodeThread:",
            "            self.videoEncodeThread.put(self.org_frame)",
            "",
            "        # 渲染图像与刷新 LCD 仪表",
            "        self.lcdNumber_angle.display(f'{degree:.2f}')",
            "        self.lcdNumber_distance.display(f'{distance:.2f}')",
            "",
            "        # 双超限复合告警分支判定",
            "        is_angle_exceed = abs(degree) > self.angle_alarm",
            "        is_dist_exceed = abs(distance) > self.dist_alarm",
            "",
            "        if is_angle_exceed and is_dist_exceed:",
            "            self.label_tip.setText('提示：偏移角度超限 偏移距离超限')",
            "            self.label_tip.setStyleSheet('color: red; font-weight: bold;')",
            "        elif is_angle_exceed:",
            "            self.label_tip.setText('提示：偏移角度超限')",
            "            self.label_tip.setStyleSheet('color: red; font-weight: bold;')",
            "        elif is_dist_exceed:",
            "            self.label_tip.setText('提示：偏移距离超限')",
            "            self.label_tip.setStyleSheet('color: red; font-weight: bold;')",
            "        else:",
            "            self.label_tip.setText('提示：运行正常')",
            "            self.label_tip.setStyleSheet('color: green; font-weight: bold;')",
        ]),
        make_p_subheading("3. 运行测试与成果展示"),
        make_p_body("通过模拟不同偏移量和偏转角度序列验证窗体告警联动："),
        make_p_code([
            "$ /opt/homebrew/anaconda3/envs/python_project/bin/pytest W3D2/test_w3d2_homework.py -k test_belt_monitor_alarm_display -v",
            "W3D2/test_w3d2_homework.py::test_belt_monitor_alarm_display PASSED       [100%]",
        ]),
        make_p_body("单元测试模拟了四种工况：单角度超限、单距离超限、双重同时超限以及正常工况。测试断言表明，标签文本与颜色样式均精确触发预期告警状态。"),

        # Task 4
        make_p_task("任务四：原始帧快照持久化与基于队列的异步视频编码录制"),
        make_p_subheading("1. 题目描述与要求"),
        make_p_body("实现突发异常快照取证与长周期连续视频录制功能。为消除单线程模式下磁盘 I/O 阻塞造成的 GUI 界面卡顿，要求实现："),
        make_p_body("① 快照保存：捕获深拷贝解耦的纯净原始帧 org_frame，采用时间戳命名格式（./snapshot/belt_{id}_{timestamp}.jpg）保存并弹出反馈信息；"),
        make_p_body("② 异步视频录制：设计继承自 QThread 的工作线程 VideoEncodeProcess，内置 queue.Queue 缓冲队列。录制状态下前台将原始帧压入队列，后台线程异步出队并写入 cv2.VideoWriter。按钮在“保存视频”与“停止保存”间自锁切换，停止时排空残余帧并释放资源句柄；"),
        make_p_body("③ 视频源热重载：实现“打开视频”功能，支持用户选择外部视频文件，安全平滑停止原推理线程并无缝接入新视频源。"),
        make_p_subheading("2. 核心代码实现"),
        make_p_body("在 belt_monitor.py 中实现 VideoEncodeProcess 线程与缓冲队列控制："),
        make_p_code([
            "class VideoEncodeProcess(QThread):",
            "    def __init__(self, videoWriter: cv2.VideoWriter):",
            "        super().__init__()",
            "        self.videoWriter = videoWriter",
            "        self.frame_queue: queue.Queue = queue.Queue(maxsize=120)",
            "        self.running = True",
            "",
            "    def run(self):",
            "        while self.running:",
            "            try:",
            "                frame = self.frame_queue.get_nowait()",
            "                self.videoWriter.write(frame)",
            "            except queue.Empty:",
            "                self.msleep(5)",
            "        while not self.frame_queue.empty():",
            "            frame = self.frame_queue.get_nowait()",
            "            self.videoWriter.write(frame)",
            "        self.videoWriter.release()",
            "",
            "    def put(self, frame: np.ndarray):",
            "        try:",
            "            self.frame_queue.put_nowait(frame)",
            "        except queue.Full:",
            "            logger.warning('Video encode frame queue full, frame dropped.')",
        ]),
        make_p_subheading("3. 运行测试与成果展示"),
        make_p_body("执行异步视频写线程的边界测试，验证入队、写入与资源释放完整性："),
        make_p_code([
            "$ /opt/homebrew/anaconda3/envs/python_project/bin/pytest W3D2/test_w3d2_homework.py -k test_video_encode_process_queue -v",
            "W3D2/test_w3d2_homework.py::test_video_encode_process_queue PASSED       [100%]",
        ]),
        make_p_body("测试表明，VideoEncodeProcess 能够以毫秒级吞吐稳定消费缓冲帧，并在收到 stop 信号后完整刷新队列剩余帧，最终安全释放 VideoWriter 句柄，杜绝文件损坏。"),

        # Task 5
        make_p_task("任务五：三类视频源自适应、工程日志轮转与异步 HTTP 告警上报"),
        make_p_subheading("1. 题目描述与要求"),
        make_p_body("完善工业级外围支撑模块："),
        make_p_body("① 视频源智能适配与容灾恢复：定义 VideoSourceType 枚举（FILE、RTSP、USB），实现规则自适应解析；针对网络 RTSP 流与工业 USB 设备，读帧失败时触发 error_signal 信号在前台提示，并在后台以固定时间间隔发起自动重连；"),
        make_p_body("② 工程日志规范：在系统入口配置基于 RotatingFileHandler 的日志轮转机制（./log/belt_monitor.log，单文件 1MB，轮转备份 10 个），全面替换无格式的 print 语句，记录关键生命周期事件；"),
        make_p_body("③ 异步 HTTP 告警上报：构建守护线程 AlarmSenderThread 与告警队列，当检测到超限时将原始帧转码为 Base64 字符串，组装 JSON 报文异步 POST 发送至管理服务端（http://localhost:5000/alarm/do），并配备轻量级接收服务 flaskapp.py。"),
        make_p_subheading("2. 核心代码实现"),
        make_p_body("在 main.py 与 belt_monitor.py 中实现日志轮转与异步网络上报："),
        make_p_code([
            "def setup_logger():",
            "    os.makedirs('./log', exist_ok=True)",
            "    logger = logging.getLogger('belt_logger')",
            "    logger.setLevel(logging.DEBUG)",
            "    file_handler = RotatingFileHandler(",
            "        './log/belt_monitor.log', maxBytes=1024 * 1024, backupCount=10, encoding='utf-8'",
            "    )",
            "    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')",
            "    file_handler.setFormatter(formatter)",
            "    logger.addHandler(file_handler)",
            "    return logger",
            "",
            "class AlarmSenderThread(QThread):",
            "    def run(self):",
            "        while self.running:",
            "            try:",
            "                data = self.alarm_queue.get_nowait()",
            "                requests.post(self.target_url, json=data, timeout=1.5)",
            "            except queue.Empty:",
            "                self.msleep(50)",
        ]),
        make_p_subheading("3. 运行测试与成果展示"),
        make_p_body("在项目环境中执行视频源解析与告警组包测试："),
        make_p_code([
            "$ /opt/homebrew/anaconda3/envs/python_project/bin/pytest W3D2/test_w3d2_homework.py -k 'test_video_source_parsing or test_alarm_sender_thread_queue' -v",
            "W3D2/test_w3d2_homework.py::test_video_source_parsing PASSED             [ 50%]",
            "W3D2/test_w3d2_homework.py::test_alarm_sender_thread_queue PASSED        [100%]",
        ]),
        make_p_body("验证确认，FILE、RTSP 与 USB 三种视频源判定规则覆盖率达 100%；告警线程在模拟高负载下保持非阻塞入队，日志文件稳定记录轮转信息。"),

        # Task 6
        make_p_task("任务六：MDI 多窗口集成框架与自动化单元测试工程闭环"),
        make_p_subheading("1. 题目描述与要求"),
        make_p_body("基于 QMainWindow 构建工业级多文档界面（MDI）集成主框架 MainWindow。中央区域采用 QMdiArea，支持多输送带（皮带 1、皮带 2、皮带 3）监控子窗口的独立打开、关闭与并发渲染，支持“窗口平铺”与“窗口层叠”布局切换。顶部菜单栏提供“系统配置”入口，支持直接呼出对应通道的 MyMonitorSetupDialog 进行在线调参。"),
        make_p_body("编写自动化测试脚本 test_w3d2_homework.py，使用 pytest 框架在 offscreen 无头模式下，对系统进行全方位自动化单元测试覆盖，确保工程可靠稳定。"),
        make_p_subheading("2. 核心代码实现"),
        make_p_body("在 main.py 中实现 MDI 调度与菜单动作绑定："),
        make_p_code([
            "class MainWindow(QMainWindow):",
            "    def __init__(self, cfgfile: str = './conf/config.yaml'):",
            "        super().__init__()",
            "        self.mdi = QMdiArea()",
            "        self.setCentralWidget(self.mdi)",
            "        self._init_actions()",
            "        self._init_menus()",
            "        self._init_toolbars()",
            "",
            "    def _toggle_monitor(self, belt_id: int, state: bool, action: QAction, title: str):",
            "        if state:",
            "            widget = MyBeltMonitorForm(belt_id, self.cfgfile)",
            "            sub_win = QMdiSubWindow()",
            "            sub_win.setWidget(widget)",
            "            sub_win.setWindowTitle(title)",
            "            self.mdi.addSubWindow(sub_win)",
            "            sub_win.show()",
            "            self.sub_windows[belt_id] = sub_win",
            "        else:",
            "            if belt_id in self.sub_windows:",
            "                self.sub_windows.pop(belt_id).close()",
        ]),
        make_p_subheading("3. 运行测试与成果展示"),
        make_p_body("测试套件设计如下表所示："),
    ]

    # Section C: Paragraphs after Table 1
    after_paragraphs = [
        make_p_body("在激活的 python_project 环境中运行全量自动化单元测试："),
        make_p_code([
            "$ conda activate python_project",
            "$ /opt/homebrew/anaconda3/envs/python_project/bin/pytest W3D2/test_w3d2_homework.py -v",
            "============================= test session starts ==============================",
            "platform darwin -- Python 3.9.25, pytest-8.4.2, pluggy-1.6.0 -- /opt/homebrew/anaconda3/envs/python_project/bin/python",
            "cachedir: .pytest_cache",
            "rootdir: /Users/nijika/coding/python_project/docx/studyrecord",
            "collecting ... collected 8 items",
            "",
            "W3D2/test_w3d2_homework.py::test_yaml_config_structure PASSED            [ 12%]",
            "W3D2/test_w3d2_homework.py::test_zimage_label_state_and_coordinates PASSED [ 25%]",
            "W3D2/test_w3d2_homework.py::test_monitor_setup_dialog PASSED             [ 37%]",
            "W3D2/test_w3d2_homework.py::test_video_source_parsing PASSED             [ 50%]",
            "W3D2/test_w3d2_homework.py::test_video_encode_process_queue PASSED       [ 62%]",
            "W3D2/test_w3d2_homework.py::test_alarm_sender_thread_queue PASSED        [ 75%]",
            "W3D2/test_w3d2_homework.py::test_belt_monitor_alarm_display PASSED       [ 87%]",
            "W3D2/test_w3d2_homework.py::test_main_window_mdi_actions PASSED          [100%]",
            "",
            "============================== 8 passed in 1.81s ===============================",
        ]),
        make_p_body("测试结果表明，8 项全自动化测试用例全部一次性通过，系统配置解耦、交互式标定、异步编码、告警分发与多窗口集成各模块协同运转正常，达到工业级实训标准。"),

        make_p_heading1("三、实训小结与心得体会"),
        make_p_subheading("1. 技术要点归纳"),
        make_p_body("① 视图渲染与数据坐标解耦：在交互标定控件 ZImageLabel 中，深入理解了屏幕坐标系与原始图像坐标系的几何映射关系。通过获取缩放后 Pixmap 在 QLabel 内部的居中偏置（ox, oy）及缩放比率，建立了双向坐标转换方程，使得用户在任意分辨率窗口下的标定线段均能精确映射回 1080P 真实像素坐标。"),
        make_p_body("② 异步视频写入与多线程资源隔离：针对传统磁盘写入造成的界面卡顿难题，引入生产者-消费者队列模型。通过独立 QThread 线程消费帧队列并执行 cv2.VideoWriter 编码，成功将高耗时 I/O 从 Qt 主事件循环中彻底解耦，保障了前台画面的高帧率流畅渲染。"),
        make_p_body("③ 集中式 YAML 配置对多机位系统的赋能：彻底消除了代码中写死的视频路径、边界坐标与告警阈值。通过结构化 YAML 配置管理 belt_0、belt_1、belt_2 各设备运行基准，使得系统具备极佳的工程扩展性与可维护性。"),
        make_p_body("④ 工控日志轮转规范与异步网络告警链路：通过 Python logging 模块配置基于大小与数量轮转的日志文件处理器，统一记录异常与关键节点；通过后台守护线程异步分发包含图像 Base64 编码的 JSON 告警数据包，兼顾了现场取证的及时性与监控主体的轻量化。"),
        make_p_subheading("2. 问题与排错"),
        make_p_body("① 控件保持纵横比居中缩放引发的越界畸变：在图像缩放比例非 1:1 时，鼠标若在黑边区域松开可能导致映射坐标为负数或超出图像边界。排错过程中通过加入 min/max 夹紧函数对取样点进行边界防御截断，彻底消除了越界索引异常。"),
        make_p_body("② 视频编码线程退出时的尾部丢帧问题：在调用 stop 退出 VideoEncodeProcess 时，若仅简单终止循环，队列中积存的最后数帧将无法写入文件。通过在循环跳出后增加排空残留队列（while not empty: write()）逻辑，确保了录制视频文件的完整落盘。"),
        make_p_body("③ 告警高频触发下的网络风暴防御：连续跑偏时若每一帧均触发 HTTP 上报，会导致网络与服务端承载压力过大。排错中引入了时间戳冷却阈值（2.0 秒），限制同一通道的最小上报间隔，既保证了告警实时性，又避免了网络拥塞。"),
    ]

    # Now rebuild the body element
    body = doc._body._element
    tbl0 = t0._tbl
    tbl1 = t1._tbl
    sectPr = body.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sectPr')

    # Clear all children from body
    body.clear()

    # Re-insert in exact order:
    # 1. Title
    body.append(p_title)
    # 2. Table 0
    body.append(tbl0)
    # 3. Middle Paragraphs
    for p in middle_paragraphs:
        body.append(p)
    # 4. Table 1
    body.append(tbl1)
    # 5. After Paragraphs
    for p in after_paragraphs:
        body.append(p)
    # 6. Section Properties
    if sectPr is not None:
        body.append(sectPr)

    output_path = "W3D2/day_8.docx"
    doc.save(output_path)
    print(f"Document successfully created at {output_path}")

if __name__ == "__main__":
    build_document()
