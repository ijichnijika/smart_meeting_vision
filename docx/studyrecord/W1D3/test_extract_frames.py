"""
W1D3 视频抽帧与图像预处理单元测试
"""

import os
import shutil
import unittest
import numpy as np
import cv2
from W1D3.extract_frames import VideoFrameExtractor, batch_extract_videos
from W1D3.image_preprocess import ImagePreprocessor


class TestVideoFrameExtractor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = "W1D3/test_output"
        cls.belt_video = "W1D3/video/belt.mp4"
        cls.fire_video = "W1D3/video/fire_smoke.avi"
        os.makedirs(cls.test_dir, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def test_video_metadata_loading(self):
        """测试视频元数据读取是否正确"""
        extractor = VideoFrameExtractor(self.belt_video, self.test_dir)
        info = extractor.get_video_info()
        self.assertEqual(info["video_name"], "belt")
        self.assertEqual(info["fps"], 25.0)
        self.assertEqual(info["resolution"], "1920x1080")
        self.assertGreater(info["total_frames"], 40000)

    def test_extract_uniform_count(self):
        """测试按指定数量均匀抽帧"""
        extractor = VideoFrameExtractor(self.fire_video, self.test_dir)
        target_count = 5
        records = extractor.extract_uniform_count(target_count)
        
        self.assertEqual(len(records), target_count)
        for r in records:
            self.assertTrue(os.path.exists(r["file_path"]))
            self.assertTrue(r["filename"].startswith("fire_smoke_"))
            self.assertEqual(r["width"], 1280)
            self.assertEqual(r["height"], 720)

    def test_invalid_arguments(self):
        """测试异常输入拦截机制"""
        # 不存在的视频文件
        with self.assertRaises(FileNotFoundError):
            VideoFrameExtractor("non_existent_video.mp4", self.test_dir)

        # 抽帧数 <= 0
        extractor = VideoFrameExtractor(self.fire_video, self.test_dir)
        with self.assertRaises(ValueError):
            extractor.extract_uniform_count(0)

        with self.assertRaises(ValueError):
            extractor.extract_by_interval(-1.0)

    def test_image_preprocessing(self):
        """测试图像滤波、二值化与边缘算子"""
        # 创建一个测试图片
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.rectangle(test_img, (20, 20), (80, 80), (255, 255, 255), -1)

        # 滤波
        filters = ImagePreprocessor.apply_filters(test_img, ksize=3)
        self.assertIn("gaussian_filter", filters)
        self.assertEqual(filters["gaussian_filter"].shape, test_img.shape)

        # 二值化
        thresh = ImagePreprocessor.apply_thresholding(test_img)
        self.assertIn("binary_otsu", thresh)
        self.assertEqual(thresh["binary_otsu"].shape, (100, 100))

        # 边缘检测
        edges = ImagePreprocessor.detect_edges(test_img)
        self.assertIn("canny", edges)
        self.assertEqual(edges["canny"].shape, (100, 100))


if __name__ == "__main__":
    unittest.main()
