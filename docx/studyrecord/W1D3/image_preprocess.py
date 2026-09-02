"""
OpenCV 图像基础处理与增强工具
包含图像滤波降噪（均值/高斯/中值/双边）、二值化处理（OTSU/自适应）、形态学操作与边缘检测。
"""

import os
import cv2
import numpy as np
from typing import Dict, Tuple


class ImagePreprocessor:
    """图像处理与特征增强工具集"""

    @staticmethod
    def load_image(image_path: str) -> np.ndarray:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图像未找到: {image_path}")
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法解析图像: {image_path}")
        return img

    @staticmethod
    def apply_filters(img: np.ndarray, ksize: int = 5) -> Dict[str, np.ndarray]:
        """
        对比均值滤波、高斯滤波、中值滤波与双边滤波
        """
        results = {
            "original": img,
            "mean_filter": cv2.blur(img, (ksize, ksize)),
            "gaussian_filter": cv2.GaussianBlur(img, (ksize, ksize), 0),
            "median_filter": cv2.medianBlur(img, ksize),
            "bilateral_filter": cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)
        }
        return results

    @staticmethod
    def apply_thresholding(img: np.ndarray) -> Dict[str, np.ndarray]:
        """
        二值化处理：全局阈值、OTSU 阈值及自适应阈值
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        
        _, thresh_binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        _, thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thresh_adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        return {
            "gray": gray,
            "binary_fixed": thresh_binary,
            "binary_otsu": thresh_otsu,
            "binary_adaptive": thresh_adaptive
        }

    @staticmethod
    def apply_morphology(img: np.ndarray, kernel_size: int = 5) -> Dict[str, np.ndarray]:
        """
        形态学操作：腐蚀、膨胀、开运算、闭运算、形态学梯度
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
        
        return {
            "eroded": cv2.erode(binary, kernel, iterations=1),
            "dilated": cv2.dilate(binary, kernel, iterations=1),
            "opened": cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel),
            "closed": cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel),
            "gradient": cv2.morphologyEx(binary, cv2.MORPH_GRADIENT, kernel)
        }

    @staticmethod
    def detect_edges(img: np.ndarray) -> Dict[str, np.ndarray]:
        """
        边缘检测算子：Canny, Sobel, Laplacian
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny
        canny = cv2.Canny(blurred, 50, 150)
        
        # Sobel
        sobelx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
        sobel_combined = cv2.magnitude(sobelx, sobely)
        sobel_8u = np.uint8(np.clip(sobel_combined, 0, 255))

        # Laplacian
        laplacian = cv2.Laplacian(blurred, cv2.CV_64F)
        laplacian_8u = np.uint8(np.clip(np.absolute(laplacian), 0, 255))

        return {
            "canny": canny,
            "sobel": sobel_8u,
            "laplacian": laplacian_8u
        }


def demo_preprocess_sample(image_path: str, output_dir: str = "W1D3/preprocess_demo"):
    """演示图像预处理效果并保存"""
    os.makedirs(output_dir, exist_ok=True)
    img = ImagePreprocessor.load_image(image_path)
    
    # 滤波
    filtered = ImagePreprocessor.apply_filters(img)
    for name, res in filtered.items():
        cv2.imwrite(os.path.join(output_dir, f"filter_{name}.jpg"), res)

    # 边缘
    edges = ImagePreprocessor.detect_edges(img)
    for name, res in edges.items():
        cv2.imwrite(os.path.join(output_dir, f"edge_{name}.jpg"), res)

    print(f"图像预处理样例已输出至: {output_dir}")


if __name__ == "__main__":
    sample_file = "W1D3/dataset/belt/belt_0001_f000000.jpg"
    if os.path.exists(sample_file):
        demo_preprocess_sample(sample_file)
    else:
        print("未检测到样本图像，将在抽帧后执行演示。")
