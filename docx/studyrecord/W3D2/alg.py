from __future__ import annotations
import math
from typing import Optional, Tuple
import numpy as np


def calculate_angle(
    line1: Tuple[Tuple[float, float], Tuple[float, float]],
    line2: Tuple[Tuple[float, float], Tuple[float, float]],
) -> float:
    """
    计算两条线段之间的最小夹角
    :param line1: ((x1, y1), (x2, y2))
    :param line2: ((x3, y3), (x4, y4))
    :return: 角度值（0-90度）
    """
    vec1 = np.array([line1[0][0] - line1[1][0], line1[0][1] - line1[1][1]], dtype=np.float64)
    vec2 = np.array([line2[0][0] - line2[1][0], line2[0][1] - line2[1][1]], dtype=np.float64)

    dot_product = float(np.dot(vec1, vec2))
    norm1 = float(np.linalg.norm(vec1))
    norm2 = float(np.linalg.norm(vec2))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    cos_theta = dot_product / (norm1 * norm2)
    cos_theta = float(np.clip(cos_theta, -1.0, 1.0))
    theta_deg = float(np.degrees(np.arccos(cos_theta)))

    return min(theta_deg, 180.0 - theta_deg)


def get_border(
    keypts: np.ndarray,
    border_left_p0: Tuple[int, int],
    border_left_p1: Tuple[int, int],
    border_right_p0: Tuple[int, int],
    border_right_p1: Tuple[int, int],
    min_length: float = 300.0,
) -> Tuple[Optional[Tuple[Tuple[int, int], Tuple[int, int]]], Optional[Tuple[Tuple[int, int], Tuple[int, int]]]]:
    """
    从折线逼近顶点中提取输送带的左边界与右边界
    :param keypts: 折线近似后的顶点的列表:(((x0,y0)),((x1,y1)),...((xn,yn)))
    :param border_left_p0: 预设左边界的起点坐标 (x, y)
    :param border_left_p1: 预设左边界的终点坐标 (x, y)
    :param border_right_p0: 预设右边界的起点坐标 (x, y)
    :param border_right_p1: 预设右边界的终点坐标 (x, y)
    :param min_length: 边长过滤阈值 (默认300)
    :return: (reco_border_left, reco_border_right)
    """
    if keypts is None or len(keypts) < 2:
        return None, None

    pts = []
    for item in keypts:
        if isinstance(item, (list, tuple, np.ndarray)):
            sub = item[0] if len(item) == 1 and isinstance(item[0], (list, tuple, np.ndarray)) else item
            pts.append((int(sub[0]), int(sub[1])))

    n = len(pts)
    if n < 2:
        return None, None

    reco_border_list = []
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        d = math.hypot(x1 - x0, y1 - y0)
        line = ((x0, y0), (x1, y1))
        angle_with_left = calculate_angle(line, (border_left_p0, border_left_p1))
        angle_with_right = calculate_angle(line, (border_right_p0, border_right_p1))
        reco_border_list.append({
            "id": i,
            "angle_left": angle_with_left,
            "angle_right": angle_with_right,
            "d": d,
            "line": line,
        })

    sorted_left = sorted(reco_border_list, key=lambda item: item["angle_left"])
    sorted_right = sorted(reco_border_list, key=lambda item: item["angle_right"])

    reco_border_left = None
    reco_border_left_id = -1
    for one in sorted_left:
        if one["d"] > min_length:
            reco_border_left_id = one["id"]
            reco_border_left = one["line"]
            break

    reco_border_right = None
    reco_border_right_id = -1
    for one in sorted_right:
        if one["d"] > min_length:
            reco_border_right_id = one["id"]
            reco_border_right = one["line"]
            break

    if reco_border_left is not None and reco_border_right is not None and reco_border_left_id != reco_border_right_id:
        return reco_border_left, reco_border_right

    return None, None


def mid_line(
    line1: Tuple[Tuple[int, int], Tuple[int, int]],
    line2: Tuple[Tuple[int, int], Tuple[int, int]],
) -> tuple[None, None] | tuple[tuple[int, int], tuple[int, int]]:
    """
    已知上边和下边跟水平线平行的梯形的两条边上的两条线段：line1, line2
    求梯形的上边和下边的中心点坐标
    :param line1: 左边界两个端点坐标 ((x0, y0), (x1, y1))
    :param line2: 右边界两个端点坐标 ((x2, y2), (x3, y3))
    :return: ((top_mid_x, top_y), (bottom_mid_x, bottom_y))
    """
    x0, y0 = line1[0]
    x1, y1 = line1[1]
    points_of_line1 = [(x0, y0), (x1, y1)]

    x2, y2 = line2[0]
    x3, y3 = line2[1]
    points_of_line2 = [(x2, y2), (x3, y3)]

    # y = mx + b
    if x0 != x1:
        m0 = (y1 - y0) / (x1 - x0)
        b0 = y1 - m0 * x1
        if m0 == 0:
            return None, None
        points_of_line1.append(((y2 - b0) / m0, y2))
        points_of_line1.append(((y3 - b0) / m0, y3))
    else:
        points_of_line1.append((x0, y2))
        points_of_line1.append((x0, y3))

    if x2 != x3:
        m1 = (y3 - y2) / (x3 - x2)
        b1 = y3 - m1 * x3
        if m1 == 0:
            return None, None
        points_of_line2.append(((y0 - b1) / m1, y0))
        points_of_line2.append(((y1 - b1) / m1, y1))
    else:
        points_of_line2.append((x3, y0))
        points_of_line2.append((x3, y1))

    sorted_points_of_line1 = sorted(points_of_line1, key=lambda x: x[1])
    sorted_points_of_line2 = sorted(points_of_line2, key=lambda x: x[1])

    p0 = sorted_points_of_line1[0]
    p1 = sorted_points_of_line1[3]
    p2 = sorted_points_of_line2[0]
    p3 = sorted_points_of_line2[3]
    top_mid_x = int((p0[0] + p2[0]) / 2)
    bottom_mid_x = int((p1[0] + p3[0]) / 2)
    return (top_mid_x, int(p0[1])), (bottom_mid_x, int(p1[1]))


def calculate_dist(
    org_mid_line: Tuple[Tuple[int, int], Tuple[int, int]],
    reco_mid_line: Tuple[Tuple[int, int], Tuple[int, int]],
    org_border_left: Tuple[Tuple[int, int], Tuple[int, int]],
    org_border_right: Tuple[Tuple[int, int], Tuple[int, int]],
    belt_width: float,
) -> float:
    """
    计算偏移距离，取两条中线的最大距离，像素距离根据皮带实际宽度换算
    :param org_mid_line: 预设边缘的中线，如：((x0, y0), (x1, y1))
    :param reco_mid_line: 识别边缘的中线，如: ((x2, y2), (x3, y3))
    :param org_border_left: 预设边缘的左边缘，如 ((x4, y4), (x5, y5))
    :param org_border_right: 预设边缘的右边缘，如 ((x6, y6), (x7, y7))
    :param belt_width: 皮带的宽度，如 200 (mm) 或 2.0 (m)
    :return: 偏移距离
    """
    org_mid_line_p0, org_mid_line_p1 = org_mid_line
    if org_mid_line_p0[0] != org_mid_line_p1[0]:
        m_org_mid_line = (org_mid_line_p1[1] - org_mid_line_p0[1]) / (org_mid_line_p1[0] - org_mid_line_p0[0])
        b_org_mid_line = org_mid_line_p1[1] - m_org_mid_line * org_mid_line_p1[0]
        org_mid_line_is_vertline = False
    else:
        org_mid_line_is_vertline = True

    reco_mid_line_p0, reco_mid_line_p1 = reco_mid_line
    if reco_mid_line_p0[0] != reco_mid_line_p1[0]:
        m_reco_mid_line = (reco_mid_line_p1[1] - reco_mid_line_p0[1]) / (reco_mid_line_p1[0] - reco_mid_line_p0[0])
        b_reco_mid_line = reco_mid_line_p1[1] - m_reco_mid_line * reco_mid_line_p1[0]
        reco_mid_line_is_vertline = False
    else:
        reco_mid_line_is_vertline = True

    org_border_left_p0, org_border_left_p1 = org_border_left
    if org_border_left_p0[0] != org_border_left_p1[0]:
        m_org_border_left = (org_border_left_p1[1] - org_border_left_p0[1]) / (org_border_left_p1[0] - org_border_left_p0[0])
        b_org_border_left = org_border_left_p1[1] - m_org_border_left * org_border_left_p1[0]
        org_border_left_is_vertline = False
    else:
        org_border_left_is_vertline = True

    org_border_right_p0, org_border_right_p1 = org_border_right
    if org_border_right_p0[0] != org_border_right_p1[0]:
        m_org_border_right = (org_border_right_p1[1] - org_border_right_p0[1]) / (org_border_right_p1[0] - org_border_right_p0[0])
        b_org_border_right = org_border_right_p1[1] - m_org_border_right * org_border_right_p1[0]
        org_border_right_is_vertline = False
    else:
        org_border_right_is_vertline = True

    if org_border_left_is_vertline or org_border_right_is_vertline or org_mid_line_is_vertline or reco_mid_line_is_vertline:
        return 0.0

    start_y = int(min(reco_mid_line_p0[1], reco_mid_line_p1[1]))
    end_y = int(max(reco_mid_line_p0[1], reco_mid_line_p1[1]))
    max_dist = 0.0
    for y in range(start_y, end_y):
        d_pixel_mid_line = abs((y - b_org_mid_line) / m_org_mid_line - (y - b_reco_mid_line) / m_reco_mid_line)
        d_pixel_border_line = abs((y - b_org_border_left) / m_org_border_left - (y - b_org_border_right) / m_org_border_right)
        if d_pixel_border_line > 0:
            dist = (d_pixel_mid_line / d_pixel_border_line) * belt_width
            if dist > max_dist:
                max_dist = dist

    return max_dist
