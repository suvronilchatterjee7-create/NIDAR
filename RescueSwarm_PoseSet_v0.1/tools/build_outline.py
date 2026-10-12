"""
build_outline.py - Deterministic Body Outline (Exo-Skeleton Polygon) Generator
RescueSwarm Pose Dataset (NIDAR 2.0 Track 1)

Generates clean, non-self-intersecting segmentation polygons from 17 COCO keypoints.
Handles all postures (upright, seated, lying, crouching) and occlusions/missing points.
"""

from typing import List, Tuple, Dict, Any
import numpy as np
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
from shapely.ops import unary_union


COCO_SKELETON_PAIRS = [
    (5, 7), (7, 9),    # left arm
    (6, 8), (8, 10),   # right arm
    (11, 13), (13, 15), # left leg
    (12, 14), (14, 16), # right leg
    (5, 6),            # shoulders
    (11, 12),          # hips
    (5, 11), (6, 12),  # torso sides
    (0, 1), (0, 2), (1, 3), (2, 4), # face
]


def bbox_to_polygon(bbox: List[float]) -> List[float]:
    """Convert [x, y, w, h] bbox to polygon coordinate list [x1, y1, x2, y2, ...]."""
    x, y, w, h = bbox
    return [
        round(float(x), 2), round(float(y), 2),
        round(float(x + w), 2), round(float(y), 2),
        round(float(x + w), 2), round(float(y + h), 2),
        round(float(x), 2), round(float(y + h), 2)
    ]


def build_body_outline(keypoints: List[float], bbox: List[float], img_w: int = None, img_h: int = None) -> Tuple[List[List[float]], float, bool]:
    """
    Build a segmentation polygon from 17 COCO keypoints.
    
    Args:
        keypoints: 51 floats [x1, y1, v1, x2, y2, v2, ...]
        bbox: [x, y, w, h]
        img_w: optional image width for clamping
        img_h: optional image height for clamping
        
    Returns:
        (segmentation, area, is_fallback)
        segmentation is a list of coordinate lists: [[x1, y1, x2, y2, ...]]
        area is the polygon area
        is_fallback indicates whether a fallback bounding polygon was used
    """
    if len(keypoints) != 51:
        poly = bbox_to_polygon(bbox)
        area = float(bbox[2] * bbox[3])
        return [poly], area, True

    pts = []
    for i in range(17):
        x = float(keypoints[i * 3])
        y = float(keypoints[i * 3 + 1])
        v = int(keypoints[i * 3 + 2])
        pts.append((x, y, v))

    visible_pts = [(x, y) for (x, y, v) in pts if v > 0]
    
    # Degenerate case fallback
    if len(visible_pts) < 4:
        poly = bbox_to_polygon(bbox)
        area = float(max(1.0, bbox[2] * bbox[3]))
        return [poly], area, True

    # Compute adaptive limb radius based on bbox dimensions
    bw, bh = max(5.0, float(bbox[2])), max(5.0, float(bbox[3]))
    min_dim = min(bw, bh)
    max_dim = max(bw, bh)
    radius = max(3.0, min_dim * 0.14)
    head_radius = max(4.0, min_dim * 0.18)

    geoms = []

    # 1. Head cluster
    head_visible = [Point(x, y).buffer(head_radius) for i in range(5) if pts[i][2] > 0 for x, y, _ in [pts[i]]]
    if head_visible:
        geoms.extend(head_visible)

    # 2. Torso polygon / center
    torso_indices = [5, 6, 12, 11] # left_shoulder, right_shoulder, right_hip, left_hip
    torso_pts = [Point(pts[idx][0], pts[idx][1]) for idx in torso_indices if pts[idx][2] > 0]
    if len(torso_pts) >= 3:
        try:
            torso_poly = Polygon([(p.x, p.y) for p in torso_pts]).buffer(radius * 0.8)
            if torso_poly.is_valid and not torso_poly.is_empty:
                geoms.append(torso_poly)
        except Exception:
            pass

    # 3. Skeleton limbs (capsules)
    for p1_idx, p2_idx in COCO_SKELETON_PAIRS:
        p1 = pts[p1_idx]
        p2 = pts[p2_idx]
        if p1[2] > 0 and p2[2] > 0:
            dx = p1[0] - p2[0]
            dy = p1[1] - p2[1]
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > 1.0:
                limb = LineString([(p1[0], p1[1]), (p2[0], p2[1])]).buffer(radius)
                if limb.is_valid and not limb.is_empty:
                    geoms.append(limb)
            else:
                pt_geom = Point(p1[0], p1[1]).buffer(radius)
                geoms.append(pt_geom)

    # 4. Joint circles for all visible points
    for x, y, v in pts:
        if v > 0:
            geoms.append(Point(x, y).buffer(radius))

    if not geoms:
        poly = bbox_to_polygon(bbox)
        area = float(max(1.0, bbox[2] * bbox[3]))
        return [poly], area, True

    try:
        merged = unary_union(geoms)
        if not merged.is_valid:
            merged = merged.buffer(0)
            
        # If multipolygon or disconnected, bridge using convex hull or take largest with convex hull
        if isinstance(merged, MultiPolygon):
            # Take convex hull of all visible points dilated, or hull of union
            hull = merged.convex_hull
            # Blend between union and hull to avoid disconnected fragments
            merged = merged.buffer(radius * 0.5).buffer(-radius * 0.3)
            if isinstance(merged, MultiPolygon):
                # Pick largest polygon
                merged = max(merged.geoms, key=lambda p: p.area)

        # Simplify to clean up vertex count (around 16-32 points per person)
        simplified = merged.simplify(1.5, preserve_topology=True)
        if isinstance(simplified, MultiPolygon):
            simplified = max(simplified.geoms, key=lambda p: p.area)

        coords = list(simplified.exterior.coords)[:-1] # drop duplicate closing coordinate
        if len(coords) < 3:
            poly = bbox_to_polygon(bbox)
            area = float(max(1.0, bbox[2] * bbox[3]))
            return [poly], area, True

        flat_poly = []
        for x, y in coords:
            if img_w is not None:
                x = min(max(0.0, x), float(img_w))
            if img_h is not None:
                y = min(max(0.0, y), float(img_h))
            flat_poly.extend([round(float(x), 2), round(float(y), 2)])

        calc_area = round(float(simplified.area), 2)
        if calc_area <= 1.0:
            poly = bbox_to_polygon(bbox)
            return [poly], float(max(1.0, bbox[2] * bbox[3])), True

        return [flat_poly], calc_area, False

    except Exception:
        poly = bbox_to_polygon(bbox)
        area = float(max(1.0, bbox[2] * bbox[3]))
        return [poly], area, True


if __name__ == "__main__":
    # Self-test with sample skeleton
    sample_kpts = [
        100, 50, 2,  # nose
        95, 45, 2,   # l_eye
        105, 45, 2,  # r_eye
        90, 48, 2,   # l_ear
        110, 48, 2,  # r_ear
        85, 75, 2,   # l_shoulder
        115, 75, 2,  # r_shoulder
        75, 100, 2,  # l_elbow
        125, 100, 2, # r_elbow
        70, 125, 2,  # l_wrist
        130, 125, 2, # r_wrist
        90, 130, 2,  # l_hip
        110, 130, 2, # r_hip
        90, 170, 2,  # l_knee
        110, 170, 2, # r_knee
        90, 210, 2,  # l_ankle
        110, 210, 2  # r_ankle
    ]
    sample_bbox = [60, 40, 80, 180]
    poly, area, is_fallback = build_body_outline(sample_kpts, sample_bbox, 300, 300)
    print(f"Generated polygon points: {len(poly[0]) // 2}, Area: {area}, Fallback: {is_fallback}")
