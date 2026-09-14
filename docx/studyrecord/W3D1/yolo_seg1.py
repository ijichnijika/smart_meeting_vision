import os
import sys
import cv2
import numpy as np
from ultralytics import YOLO

from alg import calculate_angle, get_border


def run_yolo_seg(
    model_path: str = "W2D1/models/best.pt",
    video_path: str = "W3D1/video/test.mp4",
    device: str = "cpu",
):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model weight file not found: {model_path}")

    print(f"Loading YOLO model from: {model_path}")
    model = YOLO(model_path)
    print("Model loaded successfully.")

    frame = None
    if os.path.exists(video_path):
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()

    if frame is None:
        frame = np.full((1080, 1920, 3), 45, dtype=np.uint8)
        cv2.fillPoly(
            frame,
            [np.array([[570, 447], [309, 1074], [1179, 1074], [939, 447]], dtype=np.int32)],
            (120, 120, 120),
        )

    results = model.predict(frame, conf=0.25, device=device, verbose=False)
    if not results:
        print("No detection results returned.")
        return

    result = results[0]
    masks = result.masks
    boxes = result.boxes

    if masks is None or len(masks.xy) == 0:
        print("No segmentation masks detected.")
        return

    pixel_coords = masks.xy
    cls = boxes.cls if boxes is not None else [0] * len(pixel_coords)

    print(f"Detected masks count: {len(pixel_coords)}")

    border_left_p0, border_left_p1 = (580, 422), (342, 967)
    border_right_p0, border_right_p1 = (929, 438), (1152, 1009)

    annotated_img = frame.copy()

    for i in range(len(pixel_coords)):
        cls_id = int(cls[i].item()) if hasattr(cls[i], "item") else int(cls[i])
        if cls_id == 0:
            pts = np.asarray(pixel_coords[i], dtype=np.int32)
            print(f"Mask {i+1}: before approxPolyDP vertex count: {len(pts)}")

            keypts = cv2.approxPolyDP(pts, 10, True)
            print(f"Mask {i+1}: after approxPolyDP vertex count: {len(keypts)}")

            cv2.drawContours(annotated_img, [keypts], 0, (0, 0, 255), 2)
            for k in range(len(keypts)):
                pt = tuple(keypts[k][0])
                cv2.circle(annotated_img, pt, 6, (0, 255, 0), -1)

            left_border, right_border = get_border(
                keypts,
                border_left_p0,
                border_left_p1,
                border_right_p0,
                border_right_p1,
                min_length=200,
            )

            print(f"Extracted Left Border: {left_border}")
            print(f"Extracted Right Border: {right_border}")

            if left_border is not None:
                cv2.line(annotated_img, left_border[0], left_border[1], (255, 255, 0), 3)
            if right_border is not None:
                cv2.line(annotated_img, right_border[0], right_border[1], (0, 255, 255), 3)

    out_dir = "W3D1/output"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "yolo_seg1_result.jpg")
    cv2.imwrite(out_file, annotated_img)
    print(f"Visualization saved to: {out_file}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    run_yolo_seg()
