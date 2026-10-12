# NIDAR 2.0 - RescueSwarm Pose Dataset (v0.1)

[![Dataset Status](https://img.shields.io/badge/dataset-verified_v0.1-green.svg)](RescueSwarm_PoseSet_v0.1/qa/validation_report.md)
[![License](https://img.shields.io/badge/license-CC_BY_/_Public_Domain-blue.svg)](RescueSwarm_PoseSet_v0.1/LICENSE_LEDGER.csv)
[![COCO Keypoints](https://img.shields.io/badge/schema-COCO_Keypoints_17-orange.svg)](RescueSwarm_PoseSet_v0.1/annotations/coco/)
[![MPII Style](https://img.shields.io/badge/schema-MPII_Style_16-purple.svg)](RescueSwarm_PoseSet_v0.1/annotations/mpii/)

This repository contains the official dataset package and vision toolchain for **RescueSwarm**, participating in **NIDAR 2.0 (2026-27)**.

---

## 1. Project Background

### 1.1 What is NIDAR?
**NIDAR** (National Innovation Challenge for Drone Application and Research) is a national drone innovation initiative organized by the **Drone Federation India (DFI)** in partnership with the **Ministry of Electronics and Information Technology (MeitY)** under the SwaYaan program.

- **Track 1 (Drone Innovation):** Swarm drones for disaster response and GPS-denied indoor navigation.
- **Track 2 (Component Innovation):** Flight controllers designed around India's indigenous **VEGA** processor (C-DAC, RISC-V).

### 1.2 RescueSwarm Vision Mission
RescueSwarm deploys an autonomous collaborative drone swarm across disaster zones (earthquake rubble, flood zones, collapsed structures). The onboard vision stack:
1. Detects human subjects from aerial (top-down / oblique) viewpoints.
2. Predicts **17 body keypoints** (COCO standard).
3. Builds an exoskeleton **body outline polygon** from keypoints using deterministic geometry.
4. Classifies casualty posture: `lying` (casualty requiring priority triage), `seated`, `crouching`, or `upright`.

---

## 2. Repository Contents

```
NIDAR/
├── RescueSwarm_PoseSet_v0.1/          # Extracted dataset directory
│   ├── README.md                      # Detailed dataset documentation
│   ├── LICENSE_LEDGER.csv             # Full provenance and licensing ledger
│   ├── HOW_TO_REVIEW.md               # CVAT import/export review instructions
│   ├── requirements.txt               # Pinned Python dependencies
│   ├── images/                        # 300 images split into train/val/test
│   │   ├── train/                     # 240 images
│   │   ├── val/                       # 30 images
│   │   └── test/                      # 30 images
│   ├── annotations/
│   │   ├── coco/                      # COCO Keypoints JSON annotations
│   │   └── mpii/                      # MPII-style JSON annotations
│   ├── tools/
│   │   ├── build_outline.py           # Deterministic exoskeleton polygon generator
│   │   ├── coco_to_mpii.py            # COCO-to-MPII format converter
│   │   ├── mpii_to_coco.py            # MPII-to-COCO format converter
│   │   ├── validate_dataset.py        # Automated QA verification suite
│   │   └── visualize.py               # Visual overlay renderer
│   └── qa/
│       ├── overlays/                  # 35 visual verification overlays
│       ├── validation_report.md       # Full validation test report
│       └── class_balance.md           # Breakdown of postures, views, and altitudes
├── RescueSwarm_PoseSet_v0.1.zip       # Complete pre-packaged dataset ZIP (40.7 MB)
├── yolov8n-pose.pt                    # Pretrained YOLOv8-pose edge model
└── README.md                          # Repository overview (this file)
```

---

## 3. Dataset Summary

- **Total Images:** 300 (`rs_000001.jpg` to `rs_000300.jpg`)
- **Total Annotations:** 519 persons (avg 1.73 persons/image)
- **Split Ratio:** 80% train (240), 10% val (30), 10% test (30)
- **Data Source Composition:**
  - **Source A (50%):** 150 open-licensed real aerial and disaster-exercise photos from Wikimedia Commons.
  - **Source B (50%):** 150 synthetic renders with articulated kinematic rigs on disaster rubble, asphalt, grass, and dirt.
- **Posture Breakdown:**
  - `upright`: 52.8%
  - `crouching`: 22.5%
  - `lying` (casualty): 14.5%
  - `seated`: 10.2%

---

## 4. Quickstart & Tool Usage

### Installation
```bash
pip install -r RescueSwarm_PoseSet_v0.1/requirements.txt
```

### Validate Dataset Integrity
```bash
python RescueSwarm_PoseSet_v0.1/tools/validate_dataset.py
```

### Convert Annotations Between Schemas
```bash
# COCO to MPII
python RescueSwarm_PoseSet_v0.1/tools/coco_to_mpii.py \
  --coco_input RescueSwarm_PoseSet_v0.1/annotations/coco/person_keypoints_train.json \
  --mpii_output RescueSwarm_PoseSet_v0.1/annotations/mpii/mpii_style_train.json

# MPII to COCO
python RescueSwarm_PoseSet_v0.1/tools/mpii_to_coco.py \
  --mpii_input RescueSwarm_PoseSet_v0.1/annotations/mpii/mpii_style_train.json \
  --coco_output RescueSwarm_PoseSet_v0.1/annotations/coco/person_keypoints_train.json
```

### Generate Visual Inspection Overlays
```bash
python RescueSwarm_PoseSet_v0.1/tools/visualize.py --num 35
```

---

## 5. Licensing & Attribution

All 300 images are cataloged in [`RescueSwarm_PoseSet_v0.1/LICENSE_LEDGER.csv`](RescueSwarm_PoseSet_v0.1/LICENSE_LEDGER.csv):
- **150 images:** Generated by us (RescueSwarm generative rig, CC0/Permissive).
- **123 images:** Public Domain (US Gov / Wikimedia Commons).
- **20 images:** Creative Commons Attribution (CC BY 4.0 / CC BY 2.0).
- **7 images:** Creative Commons Share-Alike (CC BY-SA 2.0).
