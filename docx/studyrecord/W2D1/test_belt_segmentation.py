"""
工业输送带边缘实例分割系统单元测试套件 (Unit Tests for Belt Segmentation)
覆盖模型初始化、单图分割推理、轮廓与多边形解析、批量处理、结果持久化与异常防御验证。
"""

import os
import sys
import json
import unittest

# 将当前目录加入路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from belt_segmentation import BeltSegmentationDetector


class TestBeltSegmentationDetector(unittest.TestCase):
    """输送带边缘分割检测器单元测试类"""

    @classmethod
    def setUpClass(cls):
        cls.model_path = os.path.join(CURRENT_DIR, "models", "best.pt")
        cls.images_dir = os.path.join(CURRENT_DIR, "images")
        cls.test_output_dir = os.path.join(CURRENT_DIR, "test_output")
        cls.sample_image = os.path.join(cls.images_dir, "image1.jpg")

        assert os.path.exists(cls.model_path), f"测试依赖的模型不存在: {cls.model_path}"
        assert os.path.exists(cls.sample_image), f"测试依赖的图像不存在: {cls.sample_image}"

        cls.detector = BeltSegmentationDetector(model_path=cls.model_path, conf_threshold=0.25)

    def test_01_model_initialization(self):
        """测试模型正常加载与基础属性"""
        self.assertIsNotNone(self.detector.model)
        self.assertEqual(self.detector.conf_threshold, 0.25)
        self.assertEqual(self.detector.model.task, "segment")

    def test_02_invalid_model_path(self):
        """测试非法模型文件路径异常抛出"""
        fake_path = os.path.join(CURRENT_DIR, "models", "non_existent.pt")
        with self.assertRaises(FileNotFoundError):
            BeltSegmentationDetector(model_path=fake_path)

    def test_03_invalid_conf_threshold(self):
        """测试置信度超出 [0.0, 1.0] 时的参数防御校验"""
        with self.assertRaises(ValueError):
            BeltSegmentationDetector(model_path=self.model_path, conf_threshold=1.5)
        with self.assertRaises(ValueError):
            BeltSegmentationDetector(model_path=self.model_path, conf_threshold=-0.1)

    def test_04_single_image_prediction(self):
        """测试单张图像边缘分割推理精度与多边形轮廓属性"""
        result = self.detector.predict_single(self.sample_image, save_dir=self.test_output_dir)

        self.assertIn("image_name", result)
        self.assertEqual(result["image_name"], "image1.jpg")
        self.assertEqual(result["image_resolution"]["width"], 1920)
        self.assertEqual(result["image_resolution"]["height"], 1080)
        self.assertGreater(result["detections_count"], 0)
        self.assertGreater(result["masks_count"], 0)

        # 校验首个检测目标
        first_det = result["detections"][0]
        self.assertGreaterEqual(first_det["confidence"], 0.90)  # 高置信度
        self.assertTrue(first_det["has_mask"])
        self.assertGreater(first_det["polygon_points_count"], 100)  # 丰富边缘点
        self.assertGreater(first_det["contour_area_pixels"], 100000.0)  # 输送带面积合理
        self.assertTrue(os.path.exists(result["output_image_path"]))

    def test_05_batch_prediction_and_json_export(self):
        """测试批量图像推理与结构化元数据 JSON 导出"""
        images = [
            os.path.join(self.images_dir, f) for f in ["image1.jpg", "image100.jpg", "image1201.jpg"]
        ]
        results = self.detector.predict_batch(images, output_dir=self.test_output_dir)

        self.assertEqual(len(results), 3)
        json_report_path = os.path.join(self.test_output_dir, "belt_segmentation_results.json")
        self.assertTrue(os.path.exists(json_report_path))

        with open(json_report_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["total_images_processed"], 3)
        self.assertEqual(len(data["summary"]), 3)
        for item in data["summary"]:
            self.assertGreater(item["confidence"], 0.90)
            self.assertGreater(item["points_count"], 300)
            self.assertTrue(os.path.exists(item["output_file"]))

    def test_06_non_existent_image_exception(self):
        """测试输入不存在的图像路径时防御报错"""
        with self.assertRaises(FileNotFoundError):
            self.detector.predict_single(os.path.join(self.images_dir, "ghost.jpg"))


if __name__ == "__main__":
    unittest.main()
