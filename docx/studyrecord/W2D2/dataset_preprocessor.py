#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
面向对象工业视觉数据集预处理系统 (DatasetPreprocessor)
支持 LabelMe JSON 多边形实例分割与 Pascal VOC XML 目标检测标注解析、
坐标越界防御截断、基于种子可复现的随机数据集划分 (Train/Val/Test)、
标准 YOLO 目录结构生成、Ultralytics data.yaml 配置文件导出及结构化统计清单。
"""

import os
import sys
import json
import random
import shutil
import logging
import argparse
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# 配置工程日志记录器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("DatasetPreprocessor")


class DatasetPreprocessor:
    """工业视觉深度学习数据集预处理流水线核心类"""

    SUPPORTED_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}

    def __init__(
        self,
        data_dir: str,
        save_dir: str,
        class_mapping: Dict[str, int],
        train_ratio: float = 0.8,
        val_ratio: float = 0.2,
        test_ratio: float = 0.0,
        task_mode: str = "segment",
        random_seed: Optional[int] = 42
    ):
        """
        初始化数据集预处理器

        Args:
            data_dir: 原始图像与标注文件所在目录
            save_dir: 预处理后 YOLO 格式数据集目标保存目录
            class_mapping: 类别名称到类别 ID 的映射字典，如 {"belt": 0}
            train_ratio: 训练集划分比例（默认 0.8）
            val_ratio: 验证集划分比例（默认 0.2）
            test_ratio: 测试集划分比例（默认 0.0）
            task_mode: 任务模式，"segment" (实例分割) 或 "detect" (目标检测)
            random_seed: 随机种子，确保数据集划分严格可复现
        """
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"原始数据源目录不存在: {data_dir}")

        if not class_mapping or not isinstance(class_mapping, dict):
            raise ValueError("class_mapping 必须是非空的字典对象")

        total_ratio = train_ratio + val_ratio + test_ratio
        if not (0.99 <= total_ratio <= 1.01):
            raise ValueError(f"划分比例之和必须为 1.0，当前总和为: {total_ratio:.4f}")

        if train_ratio <= 0.0 or val_ratio <= 0.0:
            raise ValueError("train_ratio 与 val_ratio 必须大于 0.0")

        if task_mode not in ("segment", "detect"):
            raise ValueError(f"不支持的 task_mode: {task_mode}，必须为 'segment' 或 'detect'")

        self.data_dir = os.path.abspath(data_dir)
        self.save_dir = os.path.abspath(save_dir)
        self.class_mapping = class_mapping
        self.train_ratio = float(train_ratio)
        self.val_ratio = float(val_ratio)
        self.test_ratio = float(test_ratio)
        self.task_mode = task_mode
        self.random_seed = random_seed

    def scan_matched_pairs(self) -> List[Dict[str, str]]:
        """
        扫描源目录并配对图像与标注文件（同名匹配）

        Returns:
            配对成功的字典列表，包含 'image_path', 'ann_path', 'stem'
        """
        image_map = {}
        for entry in os.scandir(self.data_dir):
            if entry.is_file():
                ext = os.path.splitext(entry.name)[1].lower()
                stem = os.path.splitext(entry.name)[0]
                if ext in self.SUPPORTED_IMAGE_EXTS:
                    image_map[stem] = entry.path

        matched_pairs = []
        for stem, img_path in sorted(image_map.items()):
            target_ext = '.json' if self.task_mode == 'segment' else (
                '.xml' if os.path.exists(os.path.join(self.data_dir, stem + '.xml')) else '.json'
            )
            ann_path = os.path.join(self.data_dir, stem + target_ext)
            if os.path.exists(ann_path):
                matched_pairs.append({
                    'stem': stem,
                    'image_path': img_path,
                    'ann_path': ann_path,
                    'ann_type': target_ext
                })

        logger.info(f"扫描源目录: {self.data_dir}，共匹配到 {len(matched_pairs)} 组完整图像-标注对")
        return matched_pairs

    def parse_labelme_json(self, json_path: str, img_w: int, img_h: int) -> List[Dict[str, Any]]:
        """
        解析 LabelMe 多边形 JSON 文件并归一化坐标

        Args:
            json_path: JSON 标注文件路径
            img_w: 图像宽度
            img_h: 图像高度

        Returns:
            有效实例列表，每个元素包含 class_id 与归一化多边形点序列
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        width = data.get('imageWidth') or img_w
        height = data.get('imageHeight') or img_h

        if width <= 0 or height <= 0:
            raise ValueError(f"标注文件尺寸异常: width={width}, height={height} ({json_path})")

        instances = []
        for shape in data.get('shapes', []):
            label = shape.get('label')
            if label not in self.class_mapping:
                continue

            raw_points = shape.get('points', [])
            if len(raw_points) < 3:
                logger.warning(f"跳过退化多边形（顶点数 < 3）: {json_path}")
                continue

            # 坐标防越界截断与归一化
            norm_points = []
            for pt in raw_points:
                x = max(0.0, min(float(pt[0]), float(width)))
                y = max(0.0, min(float(pt[1]), float(height)))
                norm_points.extend([round(x / width, 6), round(y / height, 6)])

            instances.append({
                'class_id': self.class_mapping[label],
                'class_name': label,
                'normalized_points': norm_points
            })

        return instances

    def parse_voc_xml(self, xml_path: str, img_w: int, img_h: int) -> List[Dict[str, Any]]:
        """
        解析 Pascal VOC XML 文件并计算归一化 Bounding Box

        Args:
            xml_path: XML 标注文件路径
            img_w: 图像宽度
            img_h: 图像高度

        Returns:
            有效实例列表，每个元素包含 class_id 与归一化 (x_center, y_center, w, h)
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        size_node = root.find('size')
        if size_node is not None:
            w_node = size_node.find('width')
            h_node = size_node.find('height')
            width = int(w_node.text) if w_node is not None and w_node.text else img_w
            height = int(h_node.text) if h_node is not None and h_node.text else img_h
        else:
            width, height = img_w, img_h

        if width <= 0 or height <= 0:
            raise ValueError(f"XML 尺寸异常: {xml_path}")

        instances = []
        for obj in root.findall('object'):
            name_node = obj.find('name')
            if name_node is None or name_node.text not in self.class_mapping:
                continue

            cls_name = name_node.text
            bndbox = obj.find('bndbox')
            if bndbox is None:
                continue

            xmin = max(0.0, min(float(bndbox.find('xmin').text), float(width)))
            ymin = max(0.0, min(float(bndbox.find('ymin').text), float(height)))
            xmax = max(0.0, min(float(bndbox.find('xmax').text), float(width)))
            ymax = max(0.0, min(float(bndbox.find('ymax').text), float(height)))

            bw = xmax - xmin
            bh = ymax - ymin
            if bw <= 0 or bh <= 0:
                continue

            cx = xmin + bw / 2.0
            cy = ymin + bh / 2.0

            instances.append({
                'class_id': self.class_mapping[cls_name],
                'class_name': cls_name,
                'bbox': [
                    round(cx / width, 6),
                    round(cy / height, 6),
                    round(bw / width, 6),
                    round(bh / height, 6)
                ]
            })

        return instances

    def split_dataset(self, pairs: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """
        基于确定性随机种子进行 Train / Val / Test 独立划分

        Args:
            pairs: 配对列表

        Returns:
            子集字典，包含 'train', 'val', 以及可选的 'test'
        """
        shuffled = list(pairs)
        if self.random_seed is not None:
            rng = random.Random(self.random_seed)
            rng.shuffle(shuffled)
        else:
            random.shuffle(shuffled)

        total = len(shuffled)
        n_train = int(round(total * self.train_ratio))
        if n_train >= total:
            n_train = total - 1

        train_set = shuffled[:n_train]
        remaining = shuffled[n_train:]

        if self.test_ratio > 0.0:
            n_val = int(round(total * self.val_ratio))
            val_set = remaining[:n_val]
            test_set = remaining[n_val:]
        else:
            val_set = remaining
            test_set = []

        return {
            'train': train_set,
            'val': val_set,
            'test': test_set
        }

    def process_and_export(self) -> Dict[str, Any]:
        """
        执行端到端预处理流水线并导出标准 YOLO 数据集结构与配置文件

        Returns:
            处理全流程的统计元数据字典
        """
        pairs = self.scan_matched_pairs()
        if not pairs:
            raise RuntimeError(f"在 {self.data_dir} 中未找到任何可用的图像-标注对")

        splits = self.split_dataset(pairs)

        # 准备目标目录
        os.makedirs(self.save_dir, exist_ok=True)
        stats = {
            'total_pairs': len(pairs),
            'train_count': len(splits['train']),
            'val_count': len(splits['val']),
            'test_count': len(splits['test']),
            'class_instance_counts': {k: 0 for k in self.class_mapping},
            'split_instance_counts': {
                'train': {k: 0 for k in self.class_mapping},
                'val': {k: 0 for k in self.class_mapping},
                'test': {k: 0 for k in self.class_mapping}
            }
        }

        for split_name, subset in splits.items():
            if not subset:
                continue

            img_dir = os.path.join(self.save_dir, split_name, 'images')
            lbl_dir = os.path.join(self.save_dir, split_name, 'labels')
            os.makedirs(img_dir, exist_ok=True)
            os.makedirs(lbl_dir, exist_ok=True)

            for item in subset:
                src_img = item['image_path']
                dest_img = os.path.join(img_dir, os.path.basename(src_img))
                shutil.copy2(src_img, dest_img)

                img_w, img_h = 1920, 1080
                try:
                    import cv2
                    mat = cv2.imread(src_img)
                    if mat is not None:
                        img_h, img_w = mat.shape[:2]
                except Exception:
                    pass

                ann_path = item['ann_path']
                if item['ann_type'] == '.json':
                    instances = self.parse_labelme_json(ann_path, img_w, img_h)
                else:
                    instances = self.parse_voc_xml(ann_path, img_w, img_h)

                txt_path = os.path.join(lbl_dir, item['stem'] + '.txt')
                with open(txt_path, 'w', encoding='utf-8') as tf:
                    for inst in instances:
                        cls_id = inst['class_id']
                        cls_name = inst['class_name']
                        stats['class_instance_counts'][cls_name] += 1
                        stats['split_instance_counts'][split_name][cls_name] += 1

                        if self.task_mode == 'segment' and 'normalized_points' in inst:
                            pts_str = " ".join([f"{p:.6f}" for p in inst['normalized_points']])
                            tf.write(f"{cls_id} {pts_str}\n")
                        elif 'bbox' in inst:
                            bb_str = " ".join([f"{b:.6f}" for b in inst['bbox']])
                            tf.write(f"{cls_id} {bb_str}\n")

        # 生成 Ultralytics 规范 data.yaml
        yaml_content = self.generate_yaml()
        stats['data_yaml_path'] = os.path.join(self.save_dir, 'data.yaml')

        # 生成结构化报告
        summary_txt_path = os.path.join(self.save_dir, 'summary.txt')
        summary_json_path = os.path.join(self.save_dir, 'summary.json')

        with open(summary_json_path, 'w', encoding='utf-8') as jf:
            json.dump(stats, jf, indent=2, ensure_ascii=False)

        with open(summary_txt_path, 'w', encoding='utf-8') as sf:
            sf.write("=====================================================\n")
            sf.write("       YOLO 工业视觉数据集预处理汇总报告             \n")
            sf.write("=====================================================\n")
            sf.write(f"任务模式: {self.task_mode.upper()}\n")
            sf.write(f"根路径: {self.save_dir}\n")
            sf.write(f"总样本数: {stats['total_pairs']} (Train: {stats['train_count']}, Val: {stats['val_count']}, Test: {stats['test_count']})\n")
            sf.write(f"划分比例: Train={self.train_ratio:.2f}, Val={self.val_ratio:.2f}, Test={self.test_ratio:.2f}\n")
            sf.write("-----------------------------------------------------\n")
            sf.write("各类别实例统计:\n")
            for cls_name, total_inst in stats['class_instance_counts'].items():
                train_inst = stats['split_instance_counts']['train'].get(cls_name, 0)
                val_inst = stats['split_instance_counts']['val'].get(cls_name, 0)
                sf.write(f"  - {cls_name:<15}: 总计 {total_inst:>4} | 训练集 {train_inst:>4} | 验证集 {val_inst:>4}\n")
            sf.write("=====================================================\n")

        logger.info(f"预处理流水线执行完成！输出目录: {self.save_dir}")
        return stats

    def generate_yaml(self) -> str:
        """生成 Ultralytics 规范的 data.yaml 配置文件"""
        yaml_path = os.path.join(self.save_dir, 'data.yaml')
        names_dict = {v: k for k, v in self.class_mapping.items()}

        content = [
            f"# Ultralytics YOLO 数据集配置文件 - 自动生成",
            f"path: {self.save_dir}",
            f"train: train/images",
            f"val: val/images",
            f"test: {'test/images' if self.test_ratio > 0.0 else ''}",
            f"",
            f"names:"
        ]
        for cls_id in sorted(names_dict.keys()):
            content.append(f"  {cls_id}: {names_dict[cls_id]}")

        yaml_str = "\n".join(content) + "\n"
        with open(yaml_path, 'w', encoding='utf-8') as yf:
            yf.write(yaml_str)

        return yaml_str


def build_arg_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="工业输送带与通用视觉数据集自动化预处理系统",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--data_dir", type=str, required=True, help="原始样本与标注所在目录")
    parser.add_argument("--save_dir", type=str, required=True, help="预处理后输出保存目录")
    parser.add_argument("--train_ratio", type=float, default=0.8, help="训练集比例")
    parser.add_argument("--val_ratio", type=float, default=0.2, help="验证集比例")
    parser.add_argument("--test_ratio", type=float, default=0.0, help="测试集比例")
    parser.add_argument("--task_mode", type=str, default="segment", choices=["segment", "detect"], help="任务模式")
    parser.add_argument("--label_name", type=str, default="belt", help="主检测/分割目标标签名")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    class_map = {args.label_name: 0}
    processor = DatasetPreprocessor(
        data_dir=args.data_dir,
        save_dir=args.save_dir,
        class_mapping=class_map,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        task_mode=args.task_mode,
        random_seed=args.seed
    )

    try:
        stats = processor.process_and_export()
        print(f"\n[SUCCESS] 数据预处理完成！总计处理 {stats['total_pairs']} 张样本。")
        print(f"  训练集: {stats['train_count']} 张 | 验证集: {stats['val_count']} 张")
        print(f"  配置文件: {stats['data_yaml_path']}")
    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
