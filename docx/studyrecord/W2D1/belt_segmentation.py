"""
工业输送带边缘实例分割与检测系统 (Belt Edge Segmentation System)
基于 Ultralytics YOLO 实例分割模型 (YOLO11s-seg) 实现工业输送带边缘高精度检测与轮廓多边形提取。
"""

import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any, Optional, Union
import numpy as np
import cv2
from ultralytics import YOLO


class BeltSegmentationDetector:
    """
    面向对象的工业输送带边缘分割检测器
    封装 YOLO 实例分割模型的加载、批量推理、轮廓与边缘解析、可视化渲染与元数据导出。
    """

    def __init__(self, model_path: str, conf_threshold: float = 0.25, device: Optional[str] = None):
        """
        初始化输送带边缘检测器

        :param model_path: YOLO 分割模型权重文件路径 (.pt)
        :param conf_threshold: 目标置信度阈值 (默认 0.25)
        :param device: 推理设备 ('cpu', 'mps', 'cuda', 默认为自动选择)
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型权重文件不存在: {model_path}")
        
        self.model_path = os.path.abspath(model_path)
        self.conf_threshold = float(conf_threshold)
        if not (0.0 <= self.conf_threshold <= 1.0):
            raise ValueError(f"置信度阈值必须在 [0.0, 1.0] 区间内, 实际为: {conf_threshold}")

        self.device = device
        self.model = YOLO(self.model_path)

        # 校验模型任务类型
        if getattr(self.model, "task", None) != "segment":
            print(f"[警告] 模型任务类型为 {self.model.task}，预期为 segment")

    def predict_single(self, image_path: str, save_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        对单张图片执行输送带边缘分割与轮廓提取

        :param image_path: 输入图像路径
        :param save_dir: 可视化结果保存目录（若为 None 则不保存）
        :return: 包含边缘多边形、边界框、置信度等结构化分析结果的字典
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图像文件不存在: {image_path}")

        start_time = time.time()
        results = self.model.predict(
            source=image_path,
            conf=self.conf_threshold,
            device=self.device,
            verbose=False
        )
        elapsed_ms = (time.time() - start_time) * 1000.0

        if not results:
            raise RuntimeError(f"模型未能返回有效预测结果: {image_path}")

        result = results[0]
        orig_img = result.orig_img  # BGR 格式图像
        h, w = orig_img.shape[:2]

        detections = []
        masks_count = 0
        boxes = result.boxes
        masks = result.masks

        if boxes is not None and len(boxes) > 0:
            for i in range(len(boxes)):
                box = boxes[i]
                conf = float(box.conf[0].item())
                cls_id = int(box.cls[0].item())
                cls_name = self.model.names.get(cls_id, str(cls_id))
                xyxy = [round(float(v), 2) for v in box.xyxy[0].tolist()]

                detection_item = {
                    "detection_id": i + 1,
                    "class_id": cls_id,
                    "class_name": cls_name,
                    "confidence": round(conf, 4),
                    "bbox_xyxy": xyxy,
                    "bbox_width": round(xyxy[2] - xyxy[0], 2),
                    "bbox_height": round(xyxy[3] - xyxy[1], 2),
                    "has_mask": False,
                    "polygon_points_count": 0,
                    "polygon_points": [],
                    "contour_area_pixels": 0.0
                }

                # 提取实例分割轮廓多边形顶点
                if masks is not None and i < len(masks.xy):
                    poly_coords = masks.xy[i]  # shape: (N, 2)
                    if len(poly_coords) > 0:
                        detection_item["has_mask"] = True
                        detection_item["polygon_points_count"] = len(poly_coords)
                        detection_item["polygon_points"] = [
                            [round(float(pt[0]), 2), round(float(pt[1]), 2)] for pt in poly_coords
                        ]
                        pts_np = np.array(poly_coords, dtype=np.int32)
                        area = cv2.contourArea(pts_np)
                        perimeter = cv2.arcLength(pts_np, True)
                        detection_item["contour_area_pixels"] = round(area, 2)
                        detection_item["contour_perimeter_pixels"] = round(perimeter, 2)
                        masks_count += 1

                detections.append(detection_item)

        output_image_path = None
        if save_dir is not None:
            os.makedirs(save_dir, exist_ok=True)
            filename = os.path.basename(image_path)
            output_image_path = os.path.join(save_dir, filename)

            # 绘制带有分割掩膜与边框标注的可视化图像
            annotated_img = result.plot(line_width=2, font_size=1)
            
            # 增强绘制：使用高对比度绿色描绘输送带边缘外轮廓线，强化边缘视觉辨识度
            if masks is not None:
                for poly_coords in masks.xy:
                    if len(poly_coords) > 0:
                        pts_np = np.array(poly_coords, dtype=np.int32).reshape((-1, 1, 2))
                        cv2.polylines(annotated_img, [pts_np], isClosed=True, color=(0, 255, 0), thickness=2)

            cv2.imwrite(output_image_path, annotated_img)

        return {
            "image_path": os.path.abspath(image_path),
            "image_name": os.path.basename(image_path),
            "image_resolution": {"width": w, "height": h},
            "inference_time_ms": round(elapsed_ms, 2),
            "detections_count": len(detections),
            "masks_count": masks_count,
            "output_image_path": output_image_path,
            "detections": detections
        }

    def predict_batch(self, image_paths: List[str], output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        批量处理图像列表并生成全量分割分析结果

        :param image_paths: 图像路径列表
        :param output_dir: 输出目录
        :return: 所有图像的推理详情列表
        """
        batch_results = []
        for img_path in image_paths:
            res = self.predict_single(img_path, save_dir=output_dir)
            batch_results.append(res)

        if output_dir is not None:
            report_path = os.path.join(output_dir, "belt_segmentation_results.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump({
                    "model_path": self.model_path,
                    "confidence_threshold": self.conf_threshold,
                    "total_images_processed": len(image_paths),
                    "summary": [
                        {
                            "image": item["image_name"],
                            "confidence": item["detections"][0]["confidence"] if item["detections"] else 0.0,
                            "points_count": item["detections"][0]["polygon_points_count"] if item["detections"] else 0,
                            "area_pixels": item["detections"][0]["contour_area_pixels"] if item["detections"] else 0.0,
                            "output_file": item["output_image_path"]
                        } for item in batch_results
                    ],
                    "details": batch_results
                }, f, ensure_ascii=False, indent=2)
            print(f"[信息] 批量边缘分割元数据已保存至: {report_path}")

        return batch_results


def main():
    parser = argparse.ArgumentParser(description="工业输送带边缘实例分割与识别程序")
    parser.add_argument("--model", type=str, default="W2D1/models/best.pt", help="YOLO 分割模型路径")
    parser.add_argument("--source", type=str, default="W2D1/images", help="待识别图像目录或单张图像路径")
    parser.add_argument("--conf", type=float, default=0.25, help="置信度阈值")
    parser.add_argument("--output", type=str, default="W2D1/output", help="识别结果输出保存目录")
    args = parser.parse_args()

    detector = BeltSegmentationDetector(model_path=args.model, conf_threshold=args.conf)

    if os.path.isdir(args.source):
        valid_exts = {".jpg", ".jpeg", ".png", ".bmp"}
        images = [
            os.path.join(args.source, f) for f in sorted(os.listdir(args.source))
            if os.path.splitext(f)[-1].lower() in valid_exts
        ]
    elif os.path.isfile(args.source):
        images = [args.source]
    else:
        print(f"[错误] 源文件/目录不存在: {args.source}")
        sys.exit(1)

    print(f"=== 开始输送带边缘分割识别 ===")
    print(f"模型路径: {args.model}")
    print(f"待处理图像数量: {len(images)}")
    print(f"输出目录: {args.output}")

    results = detector.predict_batch(images, output_dir=args.output)
    for r in results:
        print(f"\n图像: {r['image_name']} ({r['image_resolution']['width']}x{r['image_resolution']['height']})")
        print(f"推理耗时: {r['inference_time_ms']} ms")
        for d in r["detections"]:
            print(f"  [类别]: {d['class_name']} | 置信度: {d['confidence']*100:.2f}%")
            print(f"  [边界框]: {d['bbox_xyxy']}")
            print(f"  [边缘轮廓点数]: {d['polygon_points_count']} 点 | 轮廓面积: {d['contour_area_pixels']} 像素")
        if r["output_image_path"]:
            print(f"  [结果图像已保存]: {r['output_image_path']}")

    print(f"\n=== 全部识别完成 ===")


if __name__ == "__main__":
    main()
