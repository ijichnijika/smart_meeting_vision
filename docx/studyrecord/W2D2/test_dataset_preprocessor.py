#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据预处理系统端到端自动化单元测试套件 (TestDatasetPreprocessor)
涵盖初始化参数防呆、文件对匹配、LabelMe JSON 与 VOC XML 格式解析、
多边形坐标归一化、随机可复现划分、data.yaml 结构校验及端到端流水线。
"""

import os
import sys
import json
import shutil
import unittest
import tempfile

# 确保能检索到当前目录下的待测模块
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
if CURR_DIR not in sys.path:
    sys.path.insert(0, CURR_DIR)

from dataset_preprocessor import DatasetPreprocessor


class TestDatasetPreprocessor(unittest.TestCase):
    """工业视觉数据集预处理器单元测试类"""

    @classmethod
    def setUpClass(cls):
        """创建用于测试的独立临时数据沙箱环境"""
        cls.test_dir = tempfile.mkdtemp(prefix="yolo_test_sandbox_")
        cls.raw_data_dir = os.path.join(cls.test_dir, "raw")
        cls.export_dir = os.path.join(cls.test_dir, "export")
        os.makedirs(cls.raw_data_dir, exist_ok=True)

        # 构造模拟测试图像 (1920x1080)
        # 写入 5 组模拟图像与 LabelMe JSON 标注
        for i in range(1, 6):
            stem = f"sample_{i:04d}"
            # 模拟图片二进制占位
            img_path = os.path.join(cls.raw_data_dir, f"{stem}.jpg")
            with open(img_path, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 200)

            # 模拟 LabelMe 多边形 JSON
            json_data = {
                "version": "5.5.0",
                "shapes": [
                    {
                        "label": "belt",
                        "points": [
                            [300.0, 1000.0],
                            [500.0, 400.0],
                            [900.0, 400.0],
                            [1100.0, 1000.0]
                        ],
                        "shape_type": "polygon"
                    }
                ],
                "imagePath": f"{stem}.jpg",
                "imageHeight": 1080,
                "imageWidth": 1920
            }
            with open(os.path.join(cls.raw_data_dir, f"{stem}.json"), "w", encoding="utf-8") as jf:
                json.dump(json_data, jf)

        # 构造单组 VOC XML 标注用于检测模式验证
        xml_content = """<annotation>
            <filename>sample_voc.jpg</filename>
            <size><width>1920</width><height>1080</height><depth>3</depth></size>
            <object>
                <name>crane</name>
                <bndbox><xmin>100</xmin><ymin>200</ymin><xmax>500</xmax><ymax>800</ymax></bndbox>
            </object>
        </annotation>"""
        with open(os.path.join(cls.raw_data_dir, "sample_voc.jpg"), "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 200)
        with open(os.path.join(cls.raw_data_dir, "sample_voc.xml"), "w", encoding="utf-8") as xf:
            xf.write(xml_content)

    @classmethod
    def tearDownClass(cls):
        """清理临时测试沙箱"""
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_01_initialization_defenses(self):
        """测试入参防呆与异常输入防御拦截"""
        # 测试不存在的数据源目录
        with self.assertRaises(FileNotFoundError):
            DatasetPreprocessor(
                data_dir="invalid_non_existent_dir_path",
                save_dir=self.export_dir,
                class_mapping={"belt": 0}
            )

        # 测试非法 class_mapping
        with self.assertRaises(ValueError):
            DatasetPreprocessor(
                data_dir=self.raw_data_dir,
                save_dir=self.export_dir,
                class_mapping={}
            )

        # 测试划分比例和非 1.0
        with self.assertRaises(ValueError):
            DatasetPreprocessor(
                data_dir=self.raw_data_dir,
                save_dir=self.export_dir,
                class_mapping={"belt": 0},
                train_ratio=0.7,
                val_ratio=0.1  # 0.8 != 1.0
            )

        # 测试非法 task_mode
        with self.assertRaises(ValueError):
            DatasetPreprocessor(
                data_dir=self.raw_data_dir,
                save_dir=self.export_dir,
                class_mapping={"belt": 0},
                task_mode="unsupported_mode"
            )

    def test_02_scan_matched_pairs(self):
        """测试源数据扫描与图像-标注配对机制"""
        preprocessor = DatasetPreprocessor(
            data_dir=self.raw_data_dir,
            save_dir=self.export_dir,
            class_mapping={"belt": 0},
            task_mode="segment"
        )
        pairs = preprocessor.scan_matched_pairs()
        self.assertEqual(len(pairs), 5)
        for p in pairs:
            self.assertTrue(os.path.exists(p['image_path']))
            self.assertTrue(os.path.exists(p['ann_path']))
            self.assertEqual(p['ann_type'], '.json')

    def test_03_labelme_json_parsing(self):
        """测试 LabelMe 多边形坐标归一化与防越界截断"""
        preprocessor = DatasetPreprocessor(
            data_dir=self.raw_data_dir,
            save_dir=self.export_dir,
            class_mapping={"belt": 0}
        )
        sample_json = os.path.join(self.raw_data_dir, "sample_0001.json")
        instances = preprocessor.parse_labelme_json(sample_json, img_w=1920, img_h=1080)
        self.assertEqual(len(instances), 1)
        inst = instances[0]
        self.assertEqual(inst['class_id'], 0)
        self.assertEqual(inst['class_name'], 'belt')
        pts = inst['normalized_points']
        self.assertEqual(len(pts), 8)  # 4 个顶点，8 个坐标值
        for coord in pts:
            self.assertGreaterEqual(coord, 0.0)
            self.assertLessEqual(coord, 1.0)

    def test_04_voc_xml_parsing(self):
        """测试 Pascal VOC XML 解析与中心点 Bounding Box 归一化"""
        preprocessor = DatasetPreprocessor(
            data_dir=self.raw_data_dir,
            save_dir=self.export_dir,
            class_mapping={"crane": 0},
            task_mode="detect"
        )
        sample_xml = os.path.join(self.raw_data_dir, "sample_voc.xml")
        instances = preprocessor.parse_voc_xml(sample_xml, img_w=1920, img_h=1080)
        self.assertEqual(len(instances), 1)
        bbox = instances[0]['bbox']
        self.assertEqual(len(bbox), 4)
        for val in bbox:
            self.assertGreater(val, 0.0)
            self.assertLess(val, 1.0)

    def test_05_reproducible_split(self):
        """测试基于随机种子的确定性划分与样本隔离性"""
        preprocessor_a = DatasetPreprocessor(
            data_dir=self.raw_data_dir,
            save_dir=self.export_dir,
            class_mapping={"belt": 0},
            train_ratio=0.8,
            val_ratio=0.2,
            random_seed=12345
        )
        preprocessor_b = DatasetPreprocessor(
            data_dir=self.raw_data_dir,
            save_dir=self.export_dir,
            class_mapping={"belt": 0},
            train_ratio=0.8,
            val_ratio=0.2,
            random_seed=12345
        )
        pairs = preprocessor_a.scan_matched_pairs()
        split_a = preprocessor_a.split_dataset(pairs)
        split_b = preprocessor_b.split_dataset(pairs)

        # 验证确定性可复现
        self.assertEqual(
            [x['stem'] for x in split_a['train']],
            [x['stem'] for x in split_b['train']]
        )
        # 验证训练集与验证集无交集
        train_stems = set(x['stem'] for x in split_a['train'])
        val_stems = set(x['stem'] for x in split_a['val'])
        self.assertEqual(len(train_stems.intersection(val_stems)), 0)

    def test_06_data_yaml_generation(self):
        """测试 Ultralytics 规范 data.yaml 配置文件生成"""
        preprocessor = DatasetPreprocessor(
            data_dir=self.raw_data_dir,
            save_dir=self.export_dir,
            class_mapping={"belt": 0}
        )
        os.makedirs(self.export_dir, exist_ok=True)
        yaml_str = preprocessor.generate_yaml()
        yaml_file = os.path.join(self.export_dir, "data.yaml")
        self.assertTrue(os.path.exists(yaml_file))
        self.assertIn("names:", yaml_str)
        self.assertIn("0: belt", yaml_str)
        self.assertIn("train: train/images", yaml_str)
        self.assertIn("val: val/images", yaml_str)

    def test_07_end_to_end_pipeline(self):
        """测试端到端预处理流水线导出、文件目录树与汇总报告"""
        target_dir = os.path.join(self.test_dir, "full_run_export")
        preprocessor = DatasetPreprocessor(
            data_dir=self.raw_data_dir,
            save_dir=target_dir,
            class_mapping={"belt": 0},
            train_ratio=0.8,
            val_ratio=0.2,
            random_seed=42
        )
        stats = preprocessor.process_and_export()
        self.assertEqual(stats['total_pairs'], 5)
        self.assertEqual(stats['train_count'], 4)
        self.assertEqual(stats['val_count'], 1)

        # 检查生成的文件树
        self.assertTrue(os.path.exists(os.path.join(target_dir, "train", "images")))
        self.assertTrue(os.path.exists(os.path.join(target_dir, "train", "labels")))
        self.assertTrue(os.path.exists(os.path.join(target_dir, "val", "images")))
        self.assertTrue(os.path.exists(os.path.join(target_dir, "val", "labels")))
        self.assertTrue(os.path.exists(os.path.join(target_dir, "data.yaml")))
        self.assertTrue(os.path.exists(os.path.join(target_dir, "summary.json")))
        self.assertTrue(os.path.exists(os.path.join(target_dir, "summary.txt")))


if __name__ == "__main__":
    unittest.main()
