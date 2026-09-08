#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO 实例分割工业模型训练与断点续训脚本 (train.py)
支持指定数据集配置、超参数动态调优、设备选择以及训练中断恢复 (Resume)
"""

import os
import sys
import argparse
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description="YOLO 实例分割模型训练与断点续训")
    parser.add_argument("--model", type=str, default="W2D1/models/best.pt", help="基础模型权重或模型结构文件")
    parser.add_argument("--data", type=str, default="W2D2/dataset_split/data.yaml", help="数据集 data.yaml 路径")
    parser.add_argument("--epochs", type=int, default=15, help="训练轮数")
    parser.add_argument("--imgsz", type=int, default=320, help="输入图像尺寸")
    parser.add_argument("--batch", type=int, default=8, help="批处理大小")
    parser.add_argument("--project", type=str, default="W2D2/runs/segment", help="训练产物保存主目录")
    parser.add_argument("--name", type=str, default="train_belt", help="本次训练实验命名")
    parser.add_argument("--resume", action="store_true", help="是否从上一次意外中断的权重恢复训练")
    parser.add_argument("--resume_model", type=str, default="", help="恢复训练指定的 last.pt 路径")
    parser.add_argument("--device", type=str, default="cpu", help="计算设备，可选 cpu 或 mps")
    return parser.parse_args()


def main():
    args = parse_args()
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    project_dir = os.path.abspath(os.path.join(workspace, args.project))
    data_yaml = os.path.abspath(os.path.join(workspace, args.data))

    if args.resume or args.resume_model:
        ckpt_path = args.resume_model or os.path.join(project_dir, args.name, "weights", "last.pt")
        ckpt_path = os.path.abspath(ckpt_path)
        if not os.path.exists(ckpt_path):
            print(f"[ERROR] 恢复训练权重不存在: {ckpt_path}")
            sys.exit(1)
        print(f"[INFO] 正在从中断检查点恢复训练: {ckpt_path}")
        model = YOLO(ckpt_path)
        model.train(resume=True)
    else:
        model_path = os.path.abspath(os.path.join(workspace, args.model))
        if not os.path.exists(model_path):
            print(f"[ERROR] 基础模型权重不存在: {model_path}")
            sys.exit(1)
        print(f"[INFO] 初始化模型: {model_path}")
        print(f"[INFO] 数据集配置: {data_yaml}")
        print(f"[INFO] 训练轮数: {args.epochs}, 图像尺寸: {args.imgsz}, 批大小: {args.batch}")

        model = YOLO(model_path)
        results = model.train(
            data=data_yaml,
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            project=project_dir,
            name=args.name,
            device=args.device,
            workers=2,
            exist_ok=True,
            verbose=True
        )
        print("[SUCCESS] 训练流水线成功结束！")


if __name__ == "__main__":
    main()
