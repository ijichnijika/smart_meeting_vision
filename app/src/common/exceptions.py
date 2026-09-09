"""
系统业务与运行异常定义。
"""


class MeetingVisionError(Exception):
    """系统全局异常基类。"""
    def __init__(self, message: str, code: str = "SYSTEM_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self):
        return f"[{self.code}] {self.message}"


class VideoSourceError(MeetingVisionError):
    """视频流接入或解码异常（如摄像头未授权、文件损坏或路径不存在）"""
    def __init__(self, message: str):
        super().__init__(message, code="VIDEO_SOURCE_ERROR")


class ModelLoadError(MeetingVisionError):
    """深度学习模型权重加载或推理加速设备异常"""
    def __init__(self, message: str):
        super().__init__(message, code="MODEL_LOAD_ERROR")


class AttendeeNotFoundError(MeetingVisionError):
    """参会人员不存在或花名册未匹配异常"""
    def __init__(self, attendee_id: str):
        super().__init__(f"未找到工号/学号为 '{attendee_id}' 的参会人员记录", code="ATTENDEE_NOT_FOUND")
        self.attendee_id = attendee_id


class TrackingBindingError(MeetingVisionError):
    """目标跟踪编号与参会人员绑定冲突或非法挂载异常"""
    def __init__(self, message: str):
        super().__init__(message, code="TRACKING_BINDING_ERROR")


class ReportExportError(MeetingVisionError):
    """考勤报表写入或导出异常（如文件被占用、格式异常）"""
    def __init__(self, message: str):
        super().__init__(message, code="REPORT_EXPORT_ERROR")
