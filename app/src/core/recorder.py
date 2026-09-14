"""
视频录制与图像抓拍管道模块，提供线程安全的文件写入与落盘服务。
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

from app.config import REPORTS_DIR, SNAPSHOTS_DIR, TARGET_FPS
from app.src.common.logger import get_logger

logger = get_logger("recorder")


class VideoRecorder:
    """线程安全的带标注视频录制器，封装 OpenCV VideoWriter 生命周期。"""

    def __init__(self, fps: float = float(TARGET_FPS)):
        self.fps = fps
        self.is_recording = False
        self._record_path: Optional[str] = None
        self._video_writer: Optional[cv2.VideoWriter] = None
        self._lock = threading.Lock()

    @property
    def record_path(self) -> Optional[str]:
        return self._record_path

    def start(self, save_path: Optional[str] = None) -> str:
        """启动视频录制。"""
        if save_path is None:
            ts = time.strftime("%Y%m%d_%H%M%S")
            save_path = str(REPORTS_DIR / f"recorded_vision_{ts}.mp4")

        with self._lock:
            self._record_path = save_path
            self.is_recording = True

        logger.info(f"视频录制任务已就绪: {save_path}")
        return save_path

    def write(self, frame: np.ndarray):
        """将单帧图像写入视频文件。"""
        with self._lock:
            if not self.is_recording or self._record_path is None:
                return
            if self._video_writer is None:
                h, w = frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                self._video_writer = cv2.VideoWriter(self._record_path, fourcc, self.fps, (w, h))
            if self._video_writer.isOpened():
                self._video_writer.write(frame)

    def stop(self) -> Optional[str]:
        """停止录制并释放 VideoWriter 资源。"""
        with self._lock:
            self.is_recording = False
            path = self._record_path
            if self._video_writer is not None:
                self._video_writer.release()
                self._video_writer = None
        logger.info(f"视频录制任务已结束: {path}")
        return path

    def toggle(self, save_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """切换录制状态。"""
        if self.is_recording:
            p = self.stop()
            return False, p
        else:
            p = self.start(save_path)
            return True, p


class SnapshotManager:
    """视频帧高清物理抓拍与落盘管理。"""

    @staticmethod
    def save_snapshot(frame: Optional[np.ndarray], save_path: Optional[str] = None) -> Optional[str]:
        """将当前帧保存为图像文件。"""
        if frame is None:
            return None
        if save_path is None:
            ts = time.strftime("%Y%m%d_%H%M%S")
            save_path = str(SNAPSHOTS_DIR / f"manual_snap_{ts}.jpg")

        out_path = Path(save_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), frame)
        logger.info(f"画面抓拍快照已保存: {out_path}")
        return str(out_path)
