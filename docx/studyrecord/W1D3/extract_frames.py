"""
监控视频抽帧与数据集准备工具
支持按目标帧数均匀抽帧、按时间间隔抽帧及按帧步长抽帧，输出符合标注规范的数据集与元数据索引。
"""

import os
import sys
import json
import argparse
import time
from typing import List, Dict, Optional
import cv2


class VideoFrameExtractor:
    """视频抽帧处理器"""

    def __init__(self, video_path: str, output_dir: str):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件未找到: {video_path}")
        
        self.video_path = video_path
        self.video_name = os.path.splitext(os.path.basename(video_path))[0]
        self.output_dir = os.path.join(output_dir, self.video_name)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 读取视频元信息
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        self.fps = cap.get(cv2.CAP_PROP_FPS) or 1.0
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration_sec = self.total_frames / self.fps if self.fps > 0 else 0.0
        cap.release()

    def get_video_info(self) -> Dict:
        """获取视频基本元数据"""
        return {
            "video_name": self.video_name,
            "video_path": self.video_path,
            "fps": round(self.fps, 2),
            "total_frames": self.total_frames,
            "resolution": f"{self.width}x{self.height}",
            "duration_sec": round(self.duration_sec, 2)
        }

    def extract_uniform_count(self, target_count: int, quality: int = 95) -> List[Dict]:
        """
        按指定数量在全视频范围内均匀抽帧
        :param target_count: 期望抽取的总帧数
        :param quality: JPG 保存质量 (0-100)
        :return: 抽帧记录列表
        """
        if target_count <= 0:
            raise ValueError("抽帧数量必须大于 0")
        
        if self.total_frames <= 0:
            return []

        actual_count = min(target_count, self.total_frames)
        # 为规避某些容器尾部未完全索引帧的读取失败，在 [0, total_frames - 25] 内安全均匀取点
        safe_max_frame = max(0, self.total_frames - 25)
        if actual_count == 1:
            frame_indices = [0]
        else:
            step = safe_max_frame / (actual_count - 1)
            frame_indices = [int(round(i * step)) for i in range(actual_count)]
            frame_indices = sorted(list(set(frame_indices)))
            while len(frame_indices) < actual_count:
                frame_indices.append(frame_indices[-1] + 1)

        return self._extract_specific_indices(frame_indices, quality=quality)

    def extract_by_interval(self, interval_sec: float, quality: int = 95) -> List[Dict]:
        """
        按时间间隔抽帧 (如每 N 秒抽取 1 帧)
        :param interval_sec: 时间间隔(秒)
        :param quality: JPG 保存质量
        :return: 抽帧记录列表
        """
        if interval_sec <= 0:
            raise ValueError("时间间隔必须大于 0")
        
        frame_step = max(1, int(round(self.fps * interval_sec)))
        frame_indices = list(range(0, self.total_frames, frame_step))
        return self._extract_specific_indices(frame_indices, quality=quality)

    def _extract_specific_indices(self, frame_indices: List[int], quality: int = 95) -> List[Dict]:
        """按指定的帧索引列表进行抽取与存储"""
        extracted_records = []
        target_set = set(frame_indices)
        
        cap = cv2.VideoCapture(self.video_path)
        current_frame_idx = 0
        saved_count = 0

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]

        print(f"[{self.video_name}] 开始抽帧: 计划抽取 {len(frame_indices)} 帧...")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            if current_frame_idx in target_set:
                saved_count += 1
                timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
                if timestamp_ms == 0 and self.fps > 0:
                    timestamp_ms = int((current_frame_idx / self.fps) * 1000)

                filename = f"{self.video_name}_{saved_count:04d}_f{current_frame_idx:06d}.jpg"
                save_path = os.path.join(self.output_dir, filename)

                cv2.imwrite(save_path, frame, encode_param)

                record = {
                    "sample_id": saved_count,
                    "filename": filename,
                    "file_path": save_path,
                    "frame_index": current_frame_idx,
                    "timestamp_ms": timestamp_ms,
                    "timestamp_str": f"{timestamp_ms / 1000.0:.2f}s",
                    "width": frame.shape[1],
                    "height": frame.shape[0]
                }
                extracted_records.append(record)

            current_frame_idx += 1
            if current_frame_idx > max(frame_indices, default=-1):
                break

        cap.release()
        print(f"[{self.video_name}] 抽帧完成: 成功保存 {len(extracted_records)} 帧到 {self.output_dir}")
        return extracted_records


def batch_extract_videos(
    video_paths: List[str],
    output_dir: str,
    target_count_per_video: Optional[int] = 50,
    interval_sec: Optional[float] = None
) -> Dict:
    """批量视频抽帧入口"""
    start_time = time.time()
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_videos": len(video_paths),
        "total_extracted_frames": 0,
        "videos": {}
    }

    for v_path in video_paths:
        try:
            extractor = VideoFrameExtractor(v_path, output_dir)
            video_info = extractor.get_video_info()

            if interval_sec is not None and interval_sec > 0:
                records = extractor.extract_by_interval(interval_sec)
            else:
                target_cnt = target_count_per_video if target_count_per_video else 50
                records = extractor.extract_uniform_count(target_cnt)

            video_info["extracted_count"] = len(records)
            video_info["frames"] = records
            summary["videos"][extractor.video_name] = video_info
            summary["total_extracted_frames"] += len(records)
        except Exception as e:
            print(f"处理视频 {v_path} 出错: {e}", file=sys.stderr)

    summary["elapsed_time_sec"] = round(time.time() - start_time, 2)

    # 导出元数据清单
    metadata_path = os.path.join(output_dir, "dataset_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n抽帧任务汇总已保存至: {metadata_path}")
    print(f"总计处理视频数: {summary['total_videos']}, 总提取图片数: {summary['total_extracted_frames']}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="监控视频抽帧与数据集生成工具")
    parser.add_argument("--video_dir", type=str, default="W1D3/video", help="视频所在目录")
    parser.add_argument("--output_dir", type=str, default="W1D3/dataset", help="抽帧图片输出目录")
    parser.add_argument("--videos", nargs="+", default=["belt.mp4", "fire_smoke.avi"], help="指定要处理的视频文件名列表")
    parser.add_argument("--count_per_video", type=int, default=50, help="每个视频抽取的图片数量（默认 50 张）")
    parser.add_argument("--interval_sec", type=float, default=None, help="抽帧时间间隔（秒，优先级高于 count_per_video）")
    
    args = parser.parse_args()

    selected_video_paths = []
    for v_name in args.videos:
        # 支持相对路径或直接在 video_dir 下查找
        if os.path.exists(v_name):
            selected_video_paths.append(v_name)
        else:
            candidate = os.path.join(args.video_dir, os.path.basename(v_name))
            if os.path.exists(candidate):
                selected_video_paths.append(candidate)
            else:
                print(f"警告: 视频文件不存在，跳过: {v_name}", file=sys.stderr)

    if not selected_video_paths:
        print("错误: 未找到有效的视频文件！", file=sys.stderr)
        sys.exit(1)

    batch_extract_videos(
        video_paths=selected_video_paths,
        output_dir=args.output_dir,
        target_count_per_video=args.count_per_video,
        interval_sec=args.interval_sec
    )


if __name__ == "__main__":
    main()
