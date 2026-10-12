"""
visualize.py - Overlay Visualizer for Skeleton, Outline & Annotations
RescueSwarm Pose Dataset (NIDAR 2.0 Track 1)

Renders skeleton bones, 17 keypoint joints, bounding boxes, and body outline
polygons onto images, exporting high-fidelity overlays to qa/overlays/.
"""

import os
import sys
import json
import argparse
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Any


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_ROOT = os.path.abspath(os.path.join(TOOLS_DIR, ".."))
IMAGES_DIR = os.path.join(DATASET_ROOT, "images")
ANNOTATIONS_COCO_DIR = os.path.join(DATASET_ROOT, "annotations", "coco")
QA_OVERLAYS_DIR = os.path.join(DATASET_ROOT, "qa", "overlays")


# Skeleton bone connections (1-indexed COCO pairs)
COCO_SKELETON = [
    (16, 14), (14, 12), (17, 15), (15, 13), (12, 13),
    (6, 12), (7, 13), (6, 7), (6, 8), (7, 9),
    (8, 10), (9, 11), (2, 3), (1, 2), (1, 3),
    (2, 4), (3, 5), (4, 6), (5, 7)
]

# Distinct colors for bones
BONE_COLORS = [
    (255, 60, 60), (255, 120, 0), (0, 220, 220), (0, 150, 255), (255, 220, 0),
    (180, 0, 255), (255, 0, 180), (50, 255, 50), (0, 255, 120), (120, 255, 0),
    (255, 180, 180), (180, 255, 255), (255, 255, 100), (200, 100, 255),
    (100, 200, 255), (255, 150, 200), (150, 255, 200), (220, 220, 220), (240, 180, 60)
]

POSTURE_TAG_COLORS = {
    "lying": (255, 50, 50),       # Red for casualty lying
    "seated": (255, 165, 0),     # Orange for seated
    "crouching": (255, 215, 0),  # Gold for crouching
    "upright": (50, 205, 50),    # Green for upright
    "unknown": (180, 180, 180)
}


def render_overlay(img: Image.Image, annotations: List[Dict[str, Any]]) -> Image.Image:
    """Render skeleton, body outline polygon, and bbox labels on the image."""
    base_img = img.convert("RGBA")
    overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for ann in annotations:
        kpts = ann.get("keypoints", [])
        bbox = ann.get("bbox", [])
        seg = ann.get("segmentation", [])
        posture = ann.get("posture", "unknown")
        tag_color = POSTURE_TAG_COLORS.get(posture, (200, 200, 200))

        # 1. Draw Body Outline Polygon (semi-transparent fill + bright border)
        if seg and len(seg[0]) >= 6:
            poly_coords = []
            for i in range(0, len(seg[0]), 2):
                poly_coords.append((seg[0][i], seg[0][i+1]))
            # Outline fill: 35% opacity
            fill_rgba = (tag_color[0], tag_color[1], tag_color[2], 75)
            line_rgba = (tag_color[0], tag_color[1], tag_color[2], 230)
            draw.polygon(poly_coords, fill=fill_rgba, outline=line_rgba, width=2)

        # 2. Draw Bounding Box (dashed or thin line)
        if len(bbox) == 4:
            bx, by, bw, bh = bbox
            draw.rectangle([bx, by, bx + bw, by + bh], outline=(tag_color[0], tag_color[1], tag_color[2], 160), width=1)
            # Label banner
            label_text = f"ID:{ann.get('id')} {posture.upper()} | {ann.get('camera_view')} | {ann.get('altitude_band')}"
            draw.rectangle([bx, max(0, by - 18), bx + len(label_text)*7 + 6, max(0, by)], fill=(20, 20, 20, 200))
            draw.text((bx + 3, max(0, by - 16)), label_text, fill=(255, 255, 255, 255))

        # 3. Draw Skeleton Bones
        pts = {}
        for i in range(17):
            pts[i + 1] = (kpts[i * 3], kpts[i * 3 + 1], int(kpts[i * 3 + 2]))

        for idx, (p1_id, p2_id) in enumerate(COCO_SKELETON):
            p1 = pts.get(p1_id, (0, 0, 0))
            p2 = pts.get(p2_id, (0, 0, 0))
            if p1[2] > 0 and p2[2] > 0:
                color = BONE_COLORS[idx % len(BONE_COLORS)]
                draw.line([(p1[0], p1[1]), (p2[0], p2[1])], fill=color + (240,), width=3)

        # 4. Draw Keypoint Joints
        for i in range(1, 18):
            px, py, pv = pts[i]
            if pv > 0:
                joint_color = (255, 255, 0, 255) if pv == 2 else (255, 140, 0, 255)
                r = 4
                draw.ellipse([px - r, py - r, px + r, py + r], fill=joint_color, outline=(0, 0, 0, 255), width=1)

    combined = Image.alpha_composite(base_img, overlay).convert("RGB")
    return combined


def generate_qa_overlays(num_samples: int = 35):
    """Generate visual overlay samples across train, val, test splits."""
    os.makedirs(QA_OVERLAYS_DIR, exist_ok=True)
    print(f"[*] Generating {num_samples} visual inspection overlays in {QA_OVERLAYS_DIR}...")

    generated = 0
    splits = ["train", "val", "test"]

    for s in splits:
        coco_p = os.path.join(ANNOTATIONS_COCO_DIR, f"person_keypoints_{s}.json")
        if not os.path.isfile(coco_p):
            continue

        with open(coco_p, "r", encoding="utf-8") as f:
            c_data = json.load(f)

        anns_by_img = {}
        for ann in c_data.get("annotations", []):
            anns_by_img.setdefault(ann["image_id"], []).append(ann)

        imgs = c_data.get("images", [])
        sample_imgs = imgs[:15] if s == "train" else imgs[:10]

        for img_info in sample_imgs:
            if generated >= num_samples:
                break
            img_id = img_info["id"]
            fn = img_info["file_name"]
            img_path = os.path.join(IMAGES_DIR, s, fn)
            if not os.path.isfile(img_path):
                continue

            orig_img = Image.open(img_path)
            anns = anns_by_img.get(img_id, [])
            overlay_img = render_overlay(orig_img, anns)

            out_path = os.path.join(QA_OVERLAYS_DIR, f"overlay_{fn}")
            overlay_img.save(out_path, format="JPEG", quality=90)
            generated += 1

    print(f"[+] Generated {generated} overlays in {QA_OVERLAYS_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render skeleton and outline overlays")
    parser.add_argument("--num", type=int, default=35, help="Number of overlays to generate")
    args = parser.parse_args()
    generate_qa_overlays(args.num)
