"""
build_dataset.py - Master Pipeline for Building RescueSwarm Pose Dataset v0.1
RescueSwarm Pose Dataset (NIDAR 2.0 Track 1)

Generates 300 curated images (150 Source A open-licensed real photos, 150 Source B synthetic aerial casualty renders)
and outputs COCO Keypoints JSON, MPII-Style JSON, and LICENSE_LEDGER.csv.
"""

import os
import sys
import re
import csv
import json
import time
import random
import requests
from io import BytesIO
from PIL import Image
from typing import Dict, List, Tuple, Any

# Add current tools directory to path
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

from build_outline import build_body_outline
from generate_synthetic import generate_synthetic_scene
from fetch_source_a import (
    SEARCH_QUERIES, HEADERS, clean_html,
    classify_posture_and_attributes, sanity_check_person
)
from coco_to_mpii import convert_coco_to_mpii
from ultralytics import YOLO


DATASET_ROOT = os.path.abspath(os.path.join(TOOLS_DIR, ".."))
IMAGES_DIR = os.path.join(DATASET_ROOT, "images")
ANNOTATIONS_COCO_DIR = os.path.join(DATASET_ROOT, "annotations", "coco")
ANNOTATIONS_MPII_DIR = os.path.join(DATASET_ROOT, "annotations", "mpii")
LEDGER_FILE = os.path.join(DATASET_ROOT, "LICENSE_LEDGER.csv")


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


def is_allowed_license(lic_str: str) -> Tuple[bool, bool]:
    """
    Returns (is_allowed, commercial_use_ok)
    Allowed: CC0, CC-BY, CC-BY-SA, Public Domain, etc.
    Excluded: NC, ND, unknown.
    """
    l = lic_str.lower()
    if any(k in l for k in ["nc", "noncommercial", "non-commercial", "nd", "no-deriv"]):
        return False, False
    if "public domain" in l or "pd" in l or "cc0" in l:
        return True, True
    if "cc by-sa" in l:
        return True, True
    if "cc by" in l:
        return True, True
    if "free" in l or "gnu" in l or "gpl" in l:
        return True, True
    return False, False


def query_wikimedia_for_candidates(target_count: int = 150) -> List[Dict[str, Any]]:
    """Query Wikimedia Commons across multiple search terms to collect candidate images."""
    print(f"[*] Querying Wikimedia Commons API for candidate images...")
    candidates = []
    seen_titles = set()

    for query in SEARCH_QUERIES:
        if len(candidates) >= target_count * 2:
            break
        print(f"  -> Searching: '{query}'")
        try:
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srnamespace": 6,
                "srlimit": 40
            }
            r = requests.get("https://commons.wikimedia.org/w/api.php", params=params, headers=HEADERS, timeout=12)
            if r.status_code != 200:
                continue
            items = r.json().get("query", {}).get("search", [])
            titles = [it["title"] for it in items if it["title"] not in seen_titles and it["title"].lower().endswith(('.jpg', '.jpeg', '.png'))]
            for t in titles:
                seen_titles.add(t)

            if not titles:
                continue

            # Batch query imageinfo for up to 25 titles at a time
            for i in range(0, len(titles), 25):
                batch = titles[i:i+25]
                params2 = {
                    "action": "query",
                    "format": "json",
                    "prop": "imageinfo",
                    "iiprop": "url|extmetadata|size|mime",
                    "iiurlwidth": 960,
                    "titles": "|".join(batch)
                }
                r2 = requests.get("https://commons.wikimedia.org/w/api.php", params=params2, headers=HEADERS, timeout=12)
                if r2.status_code != 200:
                    continue
                pages = r2.json().get("query", {}).get("pages", {})
                for pid, pdata in pages.items():
                    info_list = pdata.get("imageinfo", [])
                    if not info_list:
                        continue
                    ii = info_list[0]
                    thumb_url = ii.get("thumburl") or ii.get("url")
                    orig_url = ii.get("url", "")
                    if not thumb_url:
                        continue
                    meta = ii.get("extmetadata", {})
                    lic_name = meta.get("LicenseShortName", {}).get("value", "Unknown")
                    allowed, comm_ok = is_allowed_license(lic_name)
                    if not allowed:
                        continue

                    artist = clean_html(meta.get("Artist", {}).get("value", ""))
                    if not artist:
                        artist = clean_html(meta.get("Credit", {}).get("value", "Wikimedia Commons Contributor"))
                    if not artist:
                        artist = "Wikimedia Commons Contributor"

                    candidates.append({
                        "title": pdata.get("title", ""),
                        "thumb_url": thumb_url,
                        "orig_url": orig_url,
                        "license": lic_name,
                        "author": artist,
                        "commercial_use_ok": "yes" if comm_ok else "no"
                    })
            time.sleep(0.3)
        except Exception as e:
            print(f"  Error querying '{query}': {e}")
            continue

    print(f"[*] Found {len(candidates)} candidate images with valid open licenses.")
    return candidates


def collect_source_a_images(yolo_model: YOLO, target_count: int = 150) -> List[Dict[str, Any]]:
    """Download candidates, run YOLOv8-pose, apply sanity checks, collect 150 valid images."""
    candidates = query_wikimedia_for_candidates(target_count)
    random.shuffle(candidates)

    source_a_data = []
    print(f"[*] Running YOLOv8-pose pre-labeling and validation on Source A candidates...")

    for cand in candidates:
        if len(source_a_data) >= target_count:
            break
        try:
            r = requests.get(cand["thumb_url"], headers=HEADERS, timeout=12)
            if r.status_code != 200 or len(r.content) < 5000:
                continue

            img = Image.open(BytesIO(r.content)).convert("RGB")
            # Resize image to reasonable size if very large (e.g. max dimension 1024)
            max_d = max(img.width, img.height)
            if max_d > 1024:
                scale = 1024.0 / max_d
                new_w, new_h = int(img.width * scale), int(img.height * scale)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            results = yolo_model(img, conf=0.35, verbose=False)
            if not results or results[0].keypoints is None:
                continue

            boxes = results[0].boxes
            kpts_data = results[0].keypoints

            if boxes is None or len(boxes) == 0:
                continue

            valid_persons = []
            for b_idx in range(len(boxes)):
                b = boxes[b_idx]
                if int(b.cls[0]) != 0: # person class
                    continue
                bbox_xywh = b.xywh[0].cpu().numpy().tolist()
                bx, by, bw, bh = bbox_xywh
                bbox = [round(bx - bw/2.0, 2), round(by - bh/2.0, 2), round(bw, 2), round(bh, 2)]

                # Extract keypoints
                kp_coords = kpts_data[b_idx].xy[0].cpu().numpy() # 17 x 2
                kp_conf = kpts_data[b_idx].conf[0].cpu().numpy() if kpts_data[b_idx].conf is not None else [1.0]*17

                flat_kpts = []
                for k_i in range(17):
                    kx, ky = float(kp_coords[k_i][0]), float(kp_coords[k_i][1])
                    kc = float(kp_conf[k_i])
                    # If kc > 0.4 and not 0,0, v = 2 (visible), else if kc > 0.2, v = 1 (occluded)
                    if kc >= 0.35 and (kx > 0 or ky > 0):
                        v = 2
                    elif kc >= 0.15 and (kx > 0 or ky > 0):
                        v = 1
                    else:
                        v = 0
                        kx, ky = 0.0, 0.0
                    flat_kpts.extend([round(kx, 2), round(ky, 2), v])

                if sanity_check_person(flat_kpts, bbox, img.width, img.height):
                    posture, camera_view, altitude_band, occlusion = classify_posture_and_attributes(
                        flat_kpts, bbox, img.width, img.height
                    )
                    valid_persons.append({
                        "posture": posture,
                        "camera_view": camera_view,
                        "altitude_band": altitude_band,
                        "occlusion": occlusion,
                        "bbox": bbox,
                        "keypoints": flat_kpts,
                        "label_source": "model_prelabel_unreviewed",
                        "review_status": "unreviewed"
                    })

            # Keep if 1 to 4 persons detected
            if 1 <= len(valid_persons) <= 4:
                source_a_data.append({
                    "image": img,
                    "width": img.width,
                    "height": img.height,
                    "persons": valid_persons,
                    "source_url": cand["orig_url"],
                    "author": cand["author"],
                    "license": cand["license"],
                    "commercial_use_ok": cand["commercial_use_ok"],
                    "notes": f"Pre-labeled via YOLOv8n-pose from Wikimedia Commons ({cand['title']})"
                })
                print(f"  [+] Accepted Source A #{len(source_a_data)}: {cand['title'][:45]} ({len(valid_persons)} persons)")

        except Exception as e:
            continue

    print(f"[*] Total Source A images collected: {len(source_a_data)}")
    return source_a_data


def generate_source_b_images(target_count: int = 150) -> List[Dict[str, Any]]:
    """Generate 150 synthetic images with articulated humanoid rigs."""
    print(f"[*] Generating {target_count} Source B synthetic images...")
    source_b_data = []

    # Distribution targets for postures
    posture_targets = ["lying"] * 45 + ["seated"] * 30 + ["crouching"] * 25 + ["upright"] * 50

    for i in range(target_count):
        target_posture = posture_targets[i]
        w, h = random.choice([(720, 720), (800, 600), (960, 720), (640, 640)])
        img, persons = generate_synthetic_scene(w, h, target_posture)

        source_b_data.append({
            "image": img,
            "width": w,
            "height": h,
            "persons": persons,
            "source_url": "https://github.com/RescueSwarm/RescueSwarm-PoseSet/synthetic",
            "author": "RescueSwarm Generative Rig",
            "license": "generated by us",
            "commercial_use_ok": "yes",
            "notes": f"Procedural articulated rig aerial casualty scene (target posture: {target_posture})"
        })

    print(f"[*] Total Source B images generated: {len(source_b_data)}")
    return source_b_data


def build_and_package_dataset():
    """Main build function."""
    print("==================================================")
    print("RescueSwarm Pose Dataset v0.1 Build Pipeline")
    print("==================================================")

    yolo_model = YOLO("yolov8n-pose.pt")

    # Step 1: Collect Source A & B images
    source_a = collect_source_a_images(yolo_model, target_count=150)
    
    # If Source A is slightly short due to network rate limits, top up safely or warn
    if len(source_a) < 150:
        print(f"[!] Warning: Source A collected {len(source_a)} images. Adjusting to match 50/50 balance.")
    
    count_a = len(source_a)
    count_b = count_a # Maintain exact 50% / 50% ratio
    source_b = generate_source_b_images(target_count=count_b)

    total_images_count = count_a + count_b
    print(f"[*] Total dataset size: {total_images_count} images ({count_a} Source A, {count_b} Source B)")

    # Step 2: Split into train (80%), val (10%), test (10%)
    # Maintain equal balance in each split
    train_a = int(round(count_a * 0.8))
    val_a = int(round(count_a * 0.1))
    test_a = count_a - train_a - val_a

    train_b = train_a
    val_b = val_a
    test_b = count_b - train_b - val_b

    splits_data = {
        "train": source_a[:train_a] + source_b[:train_b],
        "val": source_a[train_a:train_a+val_a] + source_b[train_b:train_b+val_b],
        "test": source_a[train_a+val_a:] + source_b[train_b+val_b:]
    }

    # Shuffle each split so Source A and B are interspersed
    for s_name in splits_data:
        random.shuffle(splits_data[s_name])

    # Step 3: Assign filenames rs_000001.jpg onward, save images, build annotations and ledger
    img_global_idx = 1
    ann_global_idx = 1
    ledger_rows = []

    coco_datasets = {
        "train": {"info": {}, "licenses": [], "images": [], "annotations": [], "categories": COCO_CATEGORIES},
        "val": {"info": {}, "licenses": [], "images": [], "annotations": [], "categories": COCO_CATEGORIES},
        "test": {"info": {}, "licenses": [], "images": [], "annotations": [], "categories": COCO_CATEGORIES}
    }

    info_block = {
        "description": "RescueSwarm Pose Dataset (COCO Keypoints format)",
        "version": "0.1",
        "year": 2026,
        "contributor": "RescueSwarm Team (NIDAR 2.0 Track 1)",
        "date_created": "2026-10-12"
    }
    license_block = [
        {"id": 1, "name": "Open Source / Multi-License (Refer to LICENSE_LEDGER.csv)", "url": ""}
    ]

    for s_name, ds in coco_datasets.items():
        ds["info"] = info_block
        ds["licenses"] = license_block

    for split_name, img_items in splits_data.items():
        split_img_dir = os.path.join(IMAGES_DIR, split_name)
        os.makedirs(split_img_dir, exist_ok=True)

        for item in img_items:
            img_filename = f"rs_{img_global_idx:06d}.jpg"
            img_path = os.path.join(split_img_dir, img_filename)

            # Save JPEG image (quality 85 for crisp aerial details & compact size)
            item["image"].save(img_path, format="JPEG", quality=85)

            # Register image in COCO
            source_type_str = "source_a_open_license" if "Wikimedia" in item["notes"] else "source_b_synthetic"
            coco_datasets[split_name]["images"].append({
                "id": img_global_idx,
                "file_name": img_filename,
                "width": item["width"],
                "height": item["height"],
                "license": 1,
                "source_url": item["source_url"],
                "source_type": source_type_str
            })

            # Process persons
            for p in item["persons"]:
                kpts = p["keypoints"]
                bbox = p["bbox"]
                num_kpts = sum(1 for i in range(17) if kpts[i*3+2] > 0)

                # Generate body outline polygon via build_outline
                seg, area, _ = build_body_outline(kpts, bbox, item["width"], item["height"])

                ann_entry = {
                    "id": ann_global_idx,
                    "image_id": img_global_idx,
                    "category_id": 1,
                    "keypoints": kpts,
                    "num_keypoints": num_kpts,
                    "bbox": bbox,
                    "segmentation": seg,
                    "area": area,
                    "iscrowd": 0,
                    "posture": p["posture"],
                    "camera_view": p["camera_view"],
                    "altitude_band": p["altitude_band"],
                    "occlusion": p["occlusion"],
                    "label_source": p["label_source"],
                    "review_status": p["review_status"]
                }
                coco_datasets[split_name]["annotations"].append(ann_entry)
                ann_global_idx += 1

            # Ledger row
            attr_text = f"Photo by {item['author']} ({item['source_url']}), licensed under {item['license']}." if source_type_str == "source_a_open_license" else "Created programmatically by RescueSwarm kinematic rig."
            ledger_rows.append({
                "image_file": img_filename,
                "source_type": source_type_str,
                "source_url": item["source_url"],
                "author": item["author"],
                "license": item["license"],
                "attribution_text": attr_text,
                "commercial_use_ok": item["commercial_use_ok"],
                "notes": item["notes"]
            })

            img_global_idx += 1

    # Step 4: Write COCO JSON files
    os.makedirs(ANNOTATIONS_COCO_DIR, exist_ok=True)
    for s_name in ["train", "val", "test"]:
        out_p = os.path.join(ANNOTATIONS_COCO_DIR, f"person_keypoints_{s_name}.json")
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(coco_datasets[s_name], f, indent=2)
        print(f"[+] Saved COCO annotations: {out_p} ({len(coco_datasets[s_name]['images'])} images, {len(coco_datasets[s_name]['annotations'])} annotations)")

    # Step 5: Convert and write MPII-style JSON files
    os.makedirs(ANNOTATIONS_MPII_DIR, exist_ok=True)
    for s_name in ["train", "val", "test"]:
        mpii_data = convert_coco_to_mpii(coco_datasets[s_name])
        out_p = os.path.join(ANNOTATIONS_MPII_DIR, f"mpii_style_{s_name}.json")
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(mpii_data, f, indent=2)
        print(f"[+] Saved MPII annotations: {out_p} ({len(mpii_data)} images)")

    # Step 6: Write LICENSE_LEDGER.csv
    fieldnames = ["image_file", "source_type", "source_url", "author", "license", "attribution_text", "commercial_use_ok", "notes"]
    with open(LEDGER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in ledger_rows:
            writer.writerow(r)
    print(f"[+] Saved License Ledger: {LEDGER_FILE} ({len(ledger_rows)} rows)")

    print("==================================================")
    print("Dataset Generation Complete!")
    print(f"Total Images: {len(ledger_rows)}")
    print(f"Train: {len(splits_data['train'])}, Val: {len(splits_data['val'])}, Test: {len(splits_data['test'])}")
    print(f"Total Annotations: {ann_global_idx - 1}")
    print("==================================================")


if __name__ == "__main__":
    build_and_package_dataset()
