# RescueSwarm Pose Dataset QA Validation Report

**Status:** PASS
**Total Images:** 300
**Total Annotations:** 519

## Validation Checks

| Check | Status | Details |
|---|---|---|
| LICENSE_LEDGER exists and readable | PASS | 300 rows |
| pycocotools load (train) | PASS | Successfully parsed 240 images, 422 annotations |
| pycocotools load (val) | PASS | Successfully parsed 30 images, 44 annotations |
| pycocotools load (test) | PASS | Successfully parsed 30 images, 53 annotations |
| Split isolation (zero overlap) | PASS | Zero image overlap across train/val/test |
| Converter round-trip test (COCO -> MPII -> COCO) | PASS | 100% exact numerical match on 12 shared joints across 519 persons |

## Round-Trip Converter Fidelity Analysis

The converter between COCO Keypoints (17 points) and MPII-style format (16 joints) was evaluated on all annotations in the dataset.
- **12 Shared Joints:** Shoulders, elbows, wrists, hips, knees, ankles.
- **Evaluated Persons:** 519
- **Coordinate / Visibility Discrepancies:** 0
- **Preservation Rate:** 100.0%
