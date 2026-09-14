"""
视频采集流管理模块，负责 OpenCV VideoCapture 生命周期与重连。
"""

from __future__ import annotations

from typing import Optional, Tuple, Union
import cv2
import numpy as np

from app.src.common.logger import get_logger

logger = get_logger("video_capture")


class VideoCaptureStream:
    """封装 OpenCV 视频采集，支持摄像头、视频文件循环回放与动态切源。"""

    def __init__(self, video_source: Union[str, int] = 0):
        self.video_source = video_source
        self._cap: Optional[cv2.VideoCapture] = None

    def open(self) -> bool:
        """打开视频采集设备或本地视频文件。"""
        self.release()
        try:
            if isinstance(self.video_source, str) and self.video_source.isdigit():
                self._cap = cv2.VideoCapture(int(self.video_source))
            else:
                self._cap = cv2.VideoCapture(self.video_source)
            return self.is_opened()
        except Exception as e:
            logger.error(f"打开视频源失败 [{self.video_source}]: {e}")
            return False

    def is_opened(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def get_fps(self) -> float:
        """获取当前视频源的原生帧率，若不可用则默认返回 30.0。"""
        if self._cap is not None and self._cap.isOpened():
            fps = self._cap.get(cv2.CAP_PROP_FPS)
            if fps and fps > 0:
                return float(fps)
        return 30.0

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """读取单帧原始 OpenCV 图像，视频结束时自动重置以支持循环播放。"""
        if not self.is_opened():
            if not self.open():
                return False, None

        if self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if not ret and isinstance(self.video_source, str):
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self._cap.read()
            return ret, frame
        return False, None

    def change_source(self, new_source: Union[str, int]) -> bool:
        """切换视频数据源并重新打开。"""
        self.video_source = new_source
        return self.open()

    def release(self):
        """释放底层 VideoCapture 句柄。"""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
