"""
mpii_to_coco.py - Converts MPII-Style JSON to COCO Keypoints JSON
RescueSwarm Pose Dataset (NIDAR 2.0 Track 1)

Schema Mapping:
- Maps 12 shared joints from MPII to COCO
- Sets nose, eyes, ears (indices 0..4) to v=0 with x=0, y=0
- Drops pelvis, thorax, upper_neck, head_top
- Recomputes segmentation polygon using build_outline.py
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any

# Ensure tools directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_outline import build_body_outline


MPII_TO_COCO_MAPPING = {
    12: 6,   # r_shoulder -> right_shoulder
    13: 5,   # l_shoulder -> left_shoulder
    11: 8,   # r_elbow -> right_elbow
    14: 7,   # l_elbow -> left_elbow
    10: 10,  # r_wrist -> right_wrist
    15: 9,   # l_wrist -> left_wrist
    2: 12,   # r_hip -> right_hip
    3: 11,   # l_hip -> left_hip
    1: 14,   # r_knee -> right_knee
    4: 13,   # l_knee -> left_knee
    0: 16,   # r_ankle -> right_ankle
    5: 15,   # l_ankle -> left_ankle
}

COCO_CATEGORIES = [
    {
        "id": 1,
        "name": "person",
        "supercategory": "person",
        "keypoints": [
            "nose", "left_eye", "right_eye", "left_ear", "right_ear",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_hip", "right_hip",
            "left_knee", "right_knee", "left_ankle", "right_ankle"
        ],
        "skeleton": [
            [16, 14], [14, 12], [17, 15], [15, 13], [12, 13],
            [6, 12], [7, 13], [6, 7], [6, 8], [7, 9],
            [8, 10], [9, 11], [2, 3], [1, 2], [1, 3],
            [2, 4], [3, 5], [4, 6], [5, 7]
        ]
    }
]


def convert_mpii_to_coco(mpii_records: List[Dict[str, Any]], image_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convert MPII-style JSON list to standard COCO Keypoints dictionary."""
    images = []
    annotations = []
    ann_id_counter = 1

    for img_idx, rec in enumerate(mpii_records, start=1):
        image_name = rec["image"]["name"]
        
        # Image dimensions from metadata if available, else default placeholder
        meta = (image_metadata or {}).get(image_name, {})
        width = meta.get("width", 1280)
        height = meta.get("height", 720)
        lic_id = meta.get("license", 1)
        source_url = meta.get("source_url", "")
        source_type = meta.get("source_type", "source_b_synthetic")

        image_entry = {
            "id": img_idx,
            "file_name": image_name,
            "width": width,
            "height": height,
            "license": lic_id,
            "source_url": source_url,
            "source_type": source_type
        }
        images.append(image_entry)

        for rect in rec.get("annorect", []):
            points_dict = {p["id"]: p for p in rect.get("annopoints", {}).get("point", [])}
            
            # Reconstruct 17 COCO keypoints: default 0,0,0
            kpts_51 = [0.0] * 51
            num_kpts = 0

            # Map the 12 shared joints
            for mpii_id, coco_idx in MPII_TO_COCO_MAPPING.items():
                if mpii_id in points_dict:
                    pt = points_dict[mpii_id]
                    vis = pt.get("is_visible", 0)
                    x = pt.get("x", 0.0)
                    y = pt.get("y", 0.0)
                    # COCO visibility: 2 if visible, 1 if occluded/labeled, 0 if not labeled
                    v = 2 if vis > 0 else 0
                    if v == 0:
                        x, y = 0.0, 0.0
                    else:
                        num_kpts += 1
                    kpts_51[coco_idx * 3] = x
                    kpts_51[coco_idx * 3 + 1] = y
                    kpts_51[coco_idx * 3 + 2] = v

            # Head joints 0..4 (nose, eyes, ears) stay 0,0,0

            # BBox
            bbox = rect.get("bbox")
            if not bbox:
                # Compute bbox from visible keypoints
                vis_coords = [(kpts_51[i * 3], kpts_51[i * 3 + 1]) for i in range(17) if kpts_51[i * 3 + 2] > 0]
                if vis_coords:
                    xs = [c[0] for c in vis_coords]
                    ys = [c[1] for c in vis_coords]
                    min_x, max_x = min(xs), max(xs)
                    min_y, max_y = min(ys), max(ys)
                    bbox = [min_x - 5, min_y - 5, max(10, max_x - min_x + 10), max(10, max_y - min_y + 10)]
                else:
                    bbox = [0, 0, 50, 50]

            # Generate segmentation using build_outline
            seg, area, _ = build_body_outline(kpts_51, bbox, width, height)

            extra = rect.get("extra", {})
            activity = rect.get("activity", {})
            posture = activity.get("category", "unknown")

            ann_entry = {
                "id": extra.get("annotation_id", ann_id_counter),
                "image_id": img_idx,
                "category_id": 1,
                "keypoints": kpts_51,
                "num_keypoints": num_kpts,
                "bbox": [round(float(v), 2) for v in bbox],
                "segmentation": seg,
                "area": area,
                "iscrowd": 0,
                "posture": posture,
                "camera_view": extra.get("camera_view", "oblique"),
                "altitude_band": extra.get("altitude_band", "mid"),
                "occlusion": extra.get("occlusion", "none"),
                "label_source": extra.get("label_source", "converted_from_mpii"),
                "review_status": extra.get("review_status", "reviewed")
            }
            annotations.append(ann_entry)
            ann_id_counter += 1

    coco_data = {
        "info": {
            "description": "RescueSwarm Pose Dataset (COCO Keypoints format)",
            "version": "0.1",
            "year": 2026,
            "contributor": "RescueSwarm Team (NIDAR 2.0)",
            "date_created": "2026-10-12"
        },
        "licenses": [
            {"id": 1, "name": "RescueSwarm Multi-License (See LICENSE_LEDGER.csv)", "url": ""}
        ],
        "images": images,
        "annotations": annotations,
        "categories": COCO_CATEGORIES
    }

    return coco_data


def main():
    parser = argparse.ArgumentParser(description="Convert MPII-style JSON to COCO Keypoints JSON")
    parser.add_argument("--mpii_input", required=True, help="Path to input MPII json")
    parser.add_argument("--coco_output", required=True, help="Path to output COCO json")
    args = parser.parse_args()

    with open(args.mpii_input, "r", encoding="utf-8") as f:
        mpii_records = json.load(f)

    coco_data = convert_mpii_to_coco(mpii_records)

    os.makedirs(os.path.dirname(os.path.abspath(args.coco_output)), exist_ok=True)
    with open(args.coco_output, "w", encoding="utf-8") as f:
        json.dump(coco_data, f, indent=2)

    print(f"Successfully converted {len(mpii_records)} images to {args.coco_output}")


if __name__ == "__main__":
    main()
