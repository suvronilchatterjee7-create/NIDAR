"""
coco_to_mpii.py - Converts COCO Keypoint Annotations to MPII-Style JSON
RescueSwarm Pose Dataset (NIDAR 2.0 Track 1)

Schema Mapping:
- COCO 17 keypoints -> MPII 16 joints
- Computes derived pelvis (midpoint of hips) and thorax (midpoint of shoulders)
- Generates objpos, scale, and activity metadata
"""

import os
import json
import argparse
from typing import Dict, List, Any


# 12 Shared joints mapping: COCO_idx -> MPII_id
# MPII ids:
# 0: r_ankle, 1: r_knee, 2: r_hip, 3: l_hip, 4: l_knee, 5: l_ankle
# 6: pelvis (derived), 7: thorax (derived), 8: upper_neck, 9: head_top
# 10: r_wrist, 11: r_elbow, 12: r_shoulder, 13: l_shoulder, 14: l_elbow, 15: l_wrist
COCO_TO_MPII_MAPPING = {
    6: 12,   # right_shoulder -> r_shoulder
    5: 13,   # left_shoulder -> l_shoulder
    8: 11,   # right_elbow -> r_elbow
    7: 14,   # left_elbow -> l_elbow
    10: 10,  # right_wrist -> r_wrist
    9: 15,   # left_wrist -> l_wrist
    12: 2,   # right_hip -> r_hip
    11: 3,   # left_hip -> l_hip
    14: 1,   # right_knee -> r_knee
    13: 4,   # left_knee -> l_knee
    16: 0,   # right_ankle -> r_ankle
    15: 5,   # left_ankle -> l_ankle
}

ACTIVITY_DESCRIPTIONS = {
    "upright": "standing or walking in search area",
    "seated": "seated awaiting rescue",
    "lying": "lying on ground casualty",
    "crouching": "crouching under cover",
    "unknown": "unspecified posture"
}


def convert_coco_to_mpii(coco_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert a loaded COCO dataset dict into MPII-style JSON structure."""
    images_by_id = {img["id"]: img for img in coco_data.get("images", [])}
    annotations_by_image = {}
    for ann in coco_data.get("annotations", []):
        img_id = ann["image_id"]
        annotations_by_image.setdefault(img_id, []).append(ann)

    mpii_records = []

    for img_id, img_info in images_by_id.items():
        image_name = img_info["file_name"]
        anns = annotations_by_image.get(img_id, [])

        annorect_list = []
        for ann in anns:
            kpts = ann.get("keypoints", [])
            bbox = ann.get("bbox", [0, 0, 0, 0])
            posture = ann.get("posture", "unknown")
            activity_text = ACTIVITY_DESCRIPTIONS.get(posture, f"{posture} casualty")

            points = []
            parsed_kpts = {}
            for i in range(17):
                if i * 3 + 2 < len(kpts):
                    x = float(kpts[i * 3])
                    y = float(kpts[i * 3 + 1])
                    v = int(kpts[i * 3 + 2])
                    parsed_kpts[i] = (x, y, v)
                else:
                    parsed_kpts[i] = (0.0, 0.0, 0)

            # Map the 12 shared joints
            for coco_idx, mpii_id in COCO_TO_MPII_MAPPING.items():
                x, y, v = parsed_kpts[coco_idx]
                is_vis = 1 if v > 0 else 0
                points.append({
                    "id": mpii_id,
                    "x": round(x, 2),
                    "y": round(y, 2),
                    "is_visible": is_vis
                })

            # Derived: Pelvis (id 6) = midpoint of hips (COCO 11: left_hip, 12: right_hip)
            l_hip_x, l_hip_y, l_hip_v = parsed_kpts[11]
            r_hip_x, r_hip_y, r_hip_v = parsed_kpts[12]
            if l_hip_v > 0 and r_hip_v > 0:
                pelvis_x = round((l_hip_x + r_hip_x) / 2.0, 2)
                pelvis_y = round((l_hip_y + r_hip_y) / 2.0, 2)
                pelvis_vis = 1
            elif l_hip_v > 0:
                pelvis_x, pelvis_y, pelvis_vis = round(l_hip_x, 2), round(l_hip_y, 2), 1
            elif r_hip_v > 0:
                pelvis_x, pelvis_y, pelvis_vis = round(r_hip_x, 2), round(r_hip_y, 2), 1
            else:
                pelvis_x, pelvis_y, pelvis_vis = 0.0, 0.0, 0

            points.append({
                "id": 6,
                "x": pelvis_x,
                "y": pelvis_y,
                "is_visible": pelvis_vis,
                "derived": True
            })

            # Derived: Thorax (id 7) = midpoint of shoulders (COCO 5: left_shoulder, 6: right_shoulder)
            l_sh_x, l_sh_y, l_sh_v = parsed_kpts[5]
            r_sh_x, r_sh_y, r_sh_v = parsed_kpts[6]
            if l_sh_v > 0 and r_sh_v > 0:
                thorax_x = round((l_sh_x + r_sh_x) / 2.0, 2)
                thorax_y = round((l_sh_y + r_sh_y) / 2.0, 2)
                thorax_vis = 1
            elif l_sh_v > 0:
                thorax_x, thorax_y, thorax_vis = round(l_sh_x, 2), round(l_sh_y, 2), 1
            elif r_sh_v > 0:
                thorax_x, thorax_y, thorax_vis = round(r_sh_x, 2), round(r_sh_y, 2), 1
            else:
                thorax_x, thorax_y, thorax_vis = 0.0, 0.0, 0

            points.append({
                "id": 7,
                "x": thorax_x,
                "y": thorax_y,
                "is_visible": thorax_vis,
                "derived": True
            })

            # Upper neck (id 8) & head_top (id 9)
            points.append({"id": 8, "x": 0.0, "y": 0.0, "is_visible": 0})
            points.append({"id": 9, "x": 0.0, "y": 0.0, "is_visible": 0})

            # Sort points by joint ID (0 to 15)
            points.sort(key=lambda p: p["id"])

            # Compute objpos (center) and scale (bbox_height / 200.0)
            bx, by, bw, bh = bbox
            objpos_x = round(bx + bw / 2.0, 2)
            objpos_y = round(by + bh / 2.0, 2)
            scale = round(max(0.1, bh / 200.0), 3)

            annorect_entry = {
                "annopoints": {"point": points},
                "objpos": {"x": objpos_x, "y": objpos_y},
                "scale": scale,
                "bbox": [round(float(v), 2) for v in bbox],
                "activity": {
                    "category": posture,
                    "activity": activity_text
                },
                "extra": {
                    "annotation_id": ann.get("id"),
                    "camera_view": ann.get("camera_view"),
                    "altitude_band": ann.get("altitude_band"),
                    "occlusion": ann.get("occlusion"),
                    "label_source": ann.get("label_source"),
                    "review_status": ann.get("review_status")
                }
            }
            annorect_list.append(annorect_entry)

        mpii_records.append({
            "image": {"name": image_name},
            "annorect": annorect_list
        })

    return mpii_records


def main():
    parser = argparse.ArgumentParser(description="Convert COCO Keypoint JSON to MPII-style JSON")
    parser.add_argument("--coco_input", required=True, help="Path to input COCO json")
    parser.add_argument("--mpii_output", required=True, help="Path to output MPII json")
    args = parser.parse_args()

    with open(args.coco_input, "r", encoding="utf-8") as f:
        coco_data = json.load(f)

    mpii_records = convert_coco_to_mpii(coco_data)

    os.makedirs(os.path.dirname(os.path.abspath(args.mpii_output)), exist_ok=True)
    with open(args.mpii_output, "w", encoding="utf-8") as f:
        json.dump(mpii_records, f, indent=2)

    print(f"Successfully converted {len(mpii_records)} images to {args.mpii_output}")


if __name__ == "__main__":
    main()
