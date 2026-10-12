# RescueSwarm Pose Dataset v0.1

**Project:** RescueSwarm (NIDAR 2.0, Track 1: Drone Innovation)  
**Organization:** Drone Federation India & MeitY (SwaYaan Initiative)  
**Team / Company:** RescueSwarm  
**Release Version:** v0.1  
**Primary Format:** COCO Keypoints 1.0 (17 keypoints)  
**Secondary Format:** MPII-Style (16 joints + activity labels)

---

## 1. Project Brief & Dataset Rationale

NIDAR 2.0 (2026-27) Track 1 focuses on autonomous swarm drones for disaster response and search-and-rescue (SAR). The RescueSwarm vision stack detects casualties from aerial drone video, predicts 17 body keypoints, builds a body outline polygon ("exo-skeleton" overlay), and classifies posture (`upright`, `seated`, `lying`, `crouching`) to triage medical priority for rescuers.

### Why This Dataset Exists
1. **Perspective Mismatch in Existing Benchmarks:** Standard benchmarks (COCO, MPII) predominantly feature ground-level, upright, large-in-frame subjects. Aerial drone cameras observe humans from top-down or steep oblique viewpoints, small in frame, often lying prone/supine or partially occluded by rubble and debris.
2. **Seed Set for Fine-Tuning & Outline Verification:** Serves as a benchmark seed set to fine-tune lightweight edge models (YOLOv8-Pose) for onboard drone compute, and to validate keypoint-to-outline polygonal conversion.
3. **Controlled Schema with Drone Attributes:** Matches official COCO Keypoints format for full compatibility with `pycocotools` and pretrained models, while embedding domain-specific metadata (`posture`, `camera_view`, `altitude_band`, `occlusion`, `label_source`, `review_status`).
4. **Strict License Ledger:** Every image is tracked in `LICENSE_LEDGER.csv` with source URLs, author attribution, and commercial permissions.

---

## 2. Dataset Structure

```
RescueSwarm_PoseSet_v0.1/
  README.md
  LICENSE_LEDGER.csv
  HOW_TO_REVIEW.md
  requirements.txt
  images/
    train/               # 240 images (rs_000001.jpg .. rs_000240.jpg)
    val/                 # 30 images (rs_000241.jpg .. rs_000270.jpg)
    test/                # 30 images (rs_000271.jpg .. rs_000300.jpg)
  annotations/
    coco/
      person_keypoints_train.json
      person_keypoints_val.json
      person_keypoints_test.json
    mpii/
      mpii_style_train.json
      mpii_style_val.json
      mpii_style_test.json
  tools/
    mpii_to_coco.py      # MPII-to-COCO converter
    coco_to_mpii.py      # COCO-to-MPII converter
    build_outline.py     # Deterministic exo-skeleton polygon builder
    validate_dataset.py  # Full QA validation suite
    visualize.py         # Visual overlay generator
  qa/
    overlays/            # 35 visual verification overlays
    validation_report.md # Automated test report
    class_balance.md     # Breakdown of postures, views, and altitudes
```

---

## 3. Dataset Statistics & Splits

- **Total Images:** 300
- **Total Person Annotations:** 519 (average 1.73 persons per image)
- **Split Distribution:**
  - `train`: 240 images (422 annotations, 80.0%)
  - `val`: 30 images (44 annotations, 10.0%)
  - `test`: 30 images (53 annotations, 10.0%)
- **Source Mix (50/50):**
  - **Source A (Open-License Real Aerial & SAR):** 150 images (331 annotations) from Wikimedia Commons.
  - **Source B (Synthetic Kinematic Rig):** 150 images (188 annotations) rendered onto aerial disaster rubble, asphalt, grass, and dirt backgrounds with drop shadows and occlusions.
- **Review Breakdown:**
  - `reviewed`: 188 annotations (36.2%) — synthetic kinematic rigs with exact geometric ground truth.
  - `unreviewed`: 331 annotations (63.8%) — Source A images pre-labeled via YOLOv8-pose with automated geometric sanity checks.
- **Posture Breakdown:**
  - `upright`: 274 persons (52.8%)
  - `crouching`: 117 persons (22.5%)
  - `lying`: 75 persons (14.5%)
  - `seated`: 53 persons (10.2%)
- **Camera Views:** `oblique` (77.5%), `top_down` (14.1%), `ground_level` (8.5%)
- **Altitude Bands:** `low` (<10m: 44.1%), `mid` (10-30m: 41.0%), `high` (>30m: 14.8%)

---

## 4. Annotation Schemas

### 4.1 Primary: COCO Keypoints Format
- Follows standard COCO Keypoints JSON: `info`, `licenses`, `images`, `annotations`, `categories`.
- 17 Keypoints: `nose`, `left_eye`, `right_eye`, `left_ear`, `right_ear`, `left_shoulder`, `right_shoulder`, `left_elbow`, `right_elbow`, `left_wrist`, `right_wrist`, `left_hip`, `right_hip`, `left_knee`, `right_knee`, `left_ankle`, `right_ankle`.
- Visibility `v`: `0` = unlabelled/absent (x=0, y=0), `1` = occluded, `2` = visible.
- Extra RescueSwarm fields in each annotation:
  - `posture`: `upright`, `seated`, `lying`, `crouching`, `unknown`
  - `camera_view`: `top_down`, `oblique`, `ground_level`
  - `altitude_band`: `low` (<10m), `mid` (10-30m), `high` (>30m), `na`
  - `occlusion`: `none`, `partial`, `heavy`
  - `label_source`: `synthetic`, `model_prelabel_unreviewed`, `manual`
  - `review_status`: `reviewed`, `unreviewed`

### 4.2 Secondary: MPII-Style Format
- JSON structure per image with `annorect` list.
- 16 Joints: 0 r_ankle, 1 r_knee, 2 r_hip, 3 l_hip, 4 l_knee, 5 l_ankle, 6 pelvis (derived midpoint of hips), 7 thorax (derived midpoint of shoulders), 8 upper_neck, 9 head_top, 10 r_wrist, 11 r_elbow, 12 r_shoulder, 13 l_shoulder, 14 l_elbow, 15 l_wrist.
- `annopoints`: list of `{"id", "x", "y", "is_visible"}` with `"derived": true` on pelvis and thorax.
- Includes `objpos`, `scale`, and `activity` (`{"category": posture, "activity": description}`).

---

## 5. Converters & Body Outline Tool

- `tools/build_outline.py`: Generates the exoskeleton `segmentation` polygon from keypoints using dilated limb capsules, torso polygons, and Shapely geometry union. Deterministic, robust to missing points, handles lying/crouching postures, and includes fallback bounding boxes if visible points < 4.
- `tools/coco_to_mpii.py` & `tools/mpii_to_coco.py`: Bidirectional converters between COCO and MPII. The 12 shared joints are preserved with 100.0% exact numerical match across all 519 annotations in round-trip validation.

---

## 6. License Ledger Summary

All 300 images are catalogued in `LICENSE_LEDGER.csv`. No unlicensed or unclear images are included:
- **generated by us** (Source B Synthetic): 150 images — Commercial use: **YES**
- **Public domain** (Source A Wikimedia): 123 images — Commercial use: **YES**
- **CC BY 4.0** (Source A Wikimedia): 15 images — Commercial use: **YES** (Attribution required)
- **CC BY 2.0** (Source A Wikimedia): 5 images — Commercial use: **YES** (Attribution required)
- **CC BY-SA 2.0** (Source A Wikimedia): 7 images — Commercial use: **YES** (Share-Alike required)

*Summary:* 100% of the dataset is permissible for academic, competition, and open research use. 293 images (97.7%) permit direct commercial deployment, while 7 images carry a Share-Alike (CC BY-SA 2.0) provision.

---

## 7. Known Limitations

1. **Model Pre-labeling:** 63.8% of annotations are pre-labeled by YOLOv8-pose with automated sanity checks. Minor keypoint offsets may exist in complex terrain; users can follow `HOW_TO_REVIEW.md` in CVAT to manually refine annotations.
2. **Facial Points in High-Altitude Aerials:** Keypoints for eyes, nose, and ears have low visibility (`v=0` or `v=1`) on small-scale subjects taken from >30m altitude.
3. **Synthetic Texture Simplicity:** While synthetic rigs realistically model articulation, shadows, and occlusion, synthetic backgrounds are procedurally generated and may have slight domain gaps relative to live drone thermal/multispectral streams.
