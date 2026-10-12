# How to Review and Correct Annotations in CVAT

This guide explains how to import the **RescueSwarm Pose Dataset** into [CVAT (Computer Vision Annotation Tool)](https://www.cvat.ai/) using the standard **COCO Keypoints 1.0** format, verify or correct pre-labeled annotations, and export them back.

---

## 1. Creating the Task in CVAT

1. **Log in** to your CVAT instance (cloud or self-hosted).
2. Click **Create a new task**.
3. **Name:** e.g., `RescueSwarm_PoseSet_v0.1_train`.
4. **Labels:**
   - Add label `person` with the **17 COCO Keypoints** skeleton:
     - Keypoints: `nose`, `left_eye`, `right_eye`, `left_ear`, `right_ear`, `left_shoulder`, `right_shoulder`, `left_elbow`, `right_elbow`, `left_wrist`, `right_wrist`, `left_hip`, `right_hip`, `left_knee`, `right_knee`, `left_ankle`, `right_ankle`.
     - Skeleton connections matching COCO standard (or choose the standard COCO Keypoints 1.0 preset).
   - Add extra text/select attributes for each person:
     - `posture`: `[upright, seated, lying, crouching, unknown]`
     - `camera_view`: `[top_down, oblique, ground_level]`
     - `altitude_band`: `[low, mid, high, na]`
     - `occlusion`: `[none, partial, heavy]`
     - `review_status`: `[unreviewed, reviewed]`
5. **Attach Files:**
   - Select all images from `images/train/` (or `val/`, `test/`).
   - Click **Submit & Open**.

---

## 2. Importing Existing Pre-Labels

1. Open the created task.
2. Under **Actions** (three dots menu), select **Upload annotations**.
3. Choose format: **COCO Keypoints 1.0**.
4. Select the corresponding annotation file:
   - `annotations/coco/person_keypoints_train.json` (or `val`, `test`).
5. Wait for CVAT to load the existing bounding boxes, keypoints, and segmentation polygons.

---

## 3. Human Review Workflow

For each image:
1. **Keypoint Alignment:**
   - Check if joints match body landmarks (especially shoulders, elbows, wrists, hips, knees, ankles).
   - If a limb is occluded by debris or vegetation, drag the point to its estimated location and set attribute `occlusion` to `partial` or `heavy`.
2. **Posture & Camera Attributes:**
   - Verify `posture` matches the visual state (`lying` for grounded casualties, `seated`, `crouching`, `upright`).
   - Verify `camera_view` (`top_down` vs `oblique`).
3. **Status Update:**
   - Switch `review_status` from `unreviewed` to `reviewed`.
   - Set `label_source` to `model_prelabel_reviewed` (or `manual` if drawn from scratch).

---

## 4. Exporting Back to Dataset

1. In CVAT, click **Actions** -> **Export task dataset**.
2. Select format: **COCO Keypoints 1.0**.
3. Download the exported zip archive.
4. Replace the corresponding `person_keypoints_<split>.json` in `annotations/coco/`.
5. Run the dataset toolchain:
   ```bash
   # Re-generate MPII export
   python tools/coco_to_mpii.py --coco_input annotations/coco/person_keypoints_train.json --mpii_output annotations/mpii/mpii_style_train.json

   # Validate dataset integrity
   python tools/validate_dataset.py

   # Re-generate visual overlays
   python tools/visualize.py --num 35
   ```
