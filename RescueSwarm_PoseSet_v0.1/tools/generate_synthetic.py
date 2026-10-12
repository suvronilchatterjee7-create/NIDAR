"""
generate_synthetic.py - Articulated Humanoid Rig & Aerial Background Generator
RescueSwarm Pose Dataset (NIDAR 2.0 Track 1)

Renders articulated human casualties and rescuers onto procedural aerial backgrounds
(disaster rubble, earthquake debris, grass, asphalt, dirt/gravel) from top-down
and oblique perspectives with exact ground-truth keypoint projections and drop shadows.
"""

import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import Dict, List, Tuple, Any


# 17 COCO Keypoints:
# 0: nose, 1: l_eye, 2: r_eye, 3: l_ear, 4: r_ear
# 5: l_shoulder, 6: r_shoulder, 7: l_elbow, 8: r_elbow, 9: l_wrist, 10: r_wrist
# 11: l_hip, 12: r_hip, 13: l_knee, 14: r_knee, 15: l_ankle, 16: r_ankle

def create_aerial_background(width: int, height: int, env_type: str) -> Image.Image:
    """Generate textured aerial background (rubble, asphalt, grass, dirt)."""
    base = np.zeros((height, width, 3), dtype=np.uint8)
    
    if env_type == "rubble":
        # Greyish-tan concrete/rubble base
        base_color = np.array([140, 135, 125], dtype=np.float32)
        noise = np.random.normal(0, 25, (height, width, 3))
        img_arr = np.clip(base_color + noise, 40, 220).astype(np.uint8)
        img = Image.fromarray(img_arr)
        draw = ImageDraw.Draw(img)
        # Add random concrete chunks and debris cracks
        for _ in range(random.randint(40, 80)):
            cx = random.randint(0, width)
            cy = random.randint(0, height)
            rx = random.randint(10, 60)
            ry = random.randint(10, 60)
            c_val = random.randint(80, 200)
            draw.polygon([
                (cx - rx, cy - ry//2),
                (cx - rx//2, cy - ry),
                (cx + rx, cy - ry//3),
                (cx + rx//2, cy + ry),
                (cx - rx//3, cy + ry)
            ], fill=(c_val, c_val - 5, c_val - 12))
        # Cracks
        for _ in range(random.randint(15, 30)):
            x0, y0 = random.randint(0, width), random.randint(0, height)
            pts = [(x0, y0)]
            for _ in range(random.randint(3, 8)):
                x0 += random.randint(-40, 40)
                y0 += random.randint(-40, 40)
                pts.append((x0, y0))
            draw.line(pts, fill=(50, 45, 40), width=random.randint(1, 3))

    elif env_type == "grass":
        # Greenish field with variations
        base_color = np.array([65, 115, 45], dtype=np.float32)
        noise = np.random.normal(0, 18, (height, width, 3))
        img_arr = np.clip(base_color + noise, 20, 190).astype(np.uint8)
        img = Image.fromarray(img_arr)
        draw = ImageDraw.Draw(img)
        # Patches of dried grass / mud
        for _ in range(random.randint(10, 25)):
            x = random.randint(0, width)
            y = random.randint(0, height)
            r = random.randint(30, 90)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=(95, 110, 45, 60))

    elif env_type == "asphalt":
        # Dark road / tarmac
        base_color = np.array([60, 62, 65], dtype=np.float32)
        noise = np.random.normal(0, 12, (height, width, 3))
        img_arr = np.clip(base_color + noise, 30, 140).astype(np.uint8)
        img = Image.fromarray(img_arr)
        draw = ImageDraw.Draw(img)
        # Road markings or cracks
        if random.random() < 0.6:
            draw.line([(0, height//2), (width, height//2)], fill=(200, 190, 60), width=random.randint(4, 8))
        for _ in range(random.randint(5, 15)):
            x = random.randint(0, width)
            y = random.randint(0, height)
            draw.line([(x, y), (x + random.randint(-30, 30), y + random.randint(-30, 30))], fill=(30, 30, 30), width=2)

    else: # dirt / sand
        base_color = np.array([160, 140, 105], dtype=np.float32)
        noise = np.random.normal(0, 20, (height, width, 3))
        img_arr = np.clip(base_color + noise, 50, 220).astype(np.uint8)
        img = Image.fromarray(img_arr)
        draw = ImageDraw.Draw(img)
        for _ in range(random.randint(20, 50)):
            x = random.randint(0, width)
            y = random.randint(0, height)
            r = random.randint(3, 12)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=(110, 95, 75))

    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    return img


def generate_rig_keypoints(posture: str, camera_view: str, scale: float, rotation: float, center: Tuple[float, float]) -> Dict[int, Tuple[float, float, int]]:
    """
    Compute 2D coordinates for the 17 keypoints of an articulated humanoid rig.
    Returns dict: joint_id -> (x, y, visibility)
    """
    cx, cy = center
    rad = math.radians(rotation)
    cos_r, sin_r = math.cos(rad), math.sin(rad)

    def rot(dx: float, dy: float) -> Tuple[float, float]:
        rx = dx * cos_r - dy * sin_r
        ry = dx * sin_r + dy * cos_r
        return cx + rx * scale, cy + ry * scale

    # Foreshortening factor based on camera view
    # In top_down view, vertical standing bodies are highly foreshortened (head close to feet).
    # In lying posture, body is spread out in both top_down and oblique views.
    fs_z = 0.35 if camera_view == "top_down" else 0.85

    kpts = {}

    if posture == "upright":
        # Standing / walking
        # dx is lateral, dy is body axis
        kpts[0] = rot(0, -50 * fs_z)         # nose
        kpts[1] = rot(-4, -53 * fs_z)        # l_eye
        kpts[2] = rot(4, -53 * fs_z)         # r_eye
        kpts[3] = rot(-9, -51 * fs_z)        # l_ear
        kpts[4] = rot(9, -51 * fs_z)         # r_ear
        
        kpts[5] = rot(-16, -36 * fs_z)       # l_shoulder
        kpts[6] = rot(16, -36 * fs_z)        # r_shoulder
        
        # Arm swinging slightly
        arm_sw = random.uniform(-6, 6)
        kpts[7] = rot(-22 + arm_sw, -15 * fs_z)     # l_elbow
        kpts[8] = rot(22 - arm_sw, -15 * fs_z)      # r_elbow
        kpts[9] = rot(-25 + arm_sw*1.5, 6 * fs_z)   # l_wrist
        kpts[10] = rot(25 - arm_sw*1.5, 6 * fs_z)  # r_wrist
        
        kpts[11] = rot(-11, 4 * fs_z)        # l_hip
        kpts[12] = rot(11, 4 * fs_z)         # r_hip
        
        # Leg walking stance
        leg_step = random.uniform(-8, 8)
        kpts[13] = rot(-12, (28 + leg_step) * fs_z)  # l_knee
        kpts[14] = rot(12, (28 - leg_step) * fs_z)   # r_knee
        kpts[15] = rot(-13, (52 + leg_step*1.3) * fs_z) # l_ankle
        kpts[16] = rot(13, (52 - leg_step*1.3) * fs_z)  # r_ankle

    elif posture == "lying":
        # Supine or prone on ground
        # Full length visible from top
        var_arm = random.uniform(-10, 10)
        var_leg = random.uniform(-10, 10)
        
        kpts[0] = rot(0, -54)          # nose
        kpts[1] = rot(-5, -57)         # l_eye
        kpts[2] = rot(5, -57)          # r_eye
        kpts[3] = rot(-10, -55)        # l_ear
        kpts[4] = rot(10, -55)         # r_ear
        
        kpts[5] = rot(-18, -38)        # l_shoulder
        kpts[6] = rot(18, -38)         # r_shoulder
        
        # Arms spread out or by side
        kpts[7] = rot(-28 + var_arm, -18)    # l_elbow
        kpts[8] = rot(28 - var_arm, -18)     # r_elbow
        kpts[9] = rot(-36 + var_arm*1.2, 0)  # l_wrist
        kpts[10] = rot(36 - var_arm*1.2, 0) # r_wrist
        
        kpts[11] = rot(-12, 6)         # l_hip
        kpts[12] = rot(12, 6)          # r_hip
        
        kpts[13] = rot(-14 + var_leg, 34)    # l_knee
        kpts[14] = rot(14 - var_leg, 34)     # r_knee
        kpts[15] = rot(-16 + var_leg*1.2, 62) # l_ankle
        kpts[16] = rot(16 - var_leg*1.2, 62)  # r_ankle

    elif posture == "seated":
        # Seated, legs extended or folded forward
        kpts[0] = rot(0, -42 * fs_z)   # nose
        kpts[1] = rot(-4, -45 * fs_z)  # l_eye
        kpts[2] = rot(4, -45 * fs_z)   # r_eye
        kpts[3] = rot(-9, -43 * fs_z)  # l_ear
        kpts[4] = rot(9, -43 * fs_z)   # r_ear
        
        kpts[5] = rot(-16, -28 * fs_z) # l_shoulder
        kpts[6] = rot(16, -28 * fs_z)  # r_shoulder
        
        kpts[7] = rot(-22, -10 * fs_z) # l_elbow
        kpts[8] = rot(22, -10 * fs_z)  # r_elbow
        kpts[9] = rot(-20, 8 * fs_z)   # l_wrist
        kpts[10] = rot(20, 8 * fs_z)   # r_wrist
        
        kpts[11] = rot(-11, 2)         # l_hip
        kpts[12] = rot(11, 2)          # r_hip
        
        # Knees bent forward
        kpts[13] = rot(-16, 20)        # l_knee
        kpts[14] = rot(16, 20)         # r_knee
        kpts[15] = rot(-14, 38)        # l_ankle
        kpts[16] = rot(14, 38)         # r_ankle

    else: # crouching
        kpts[0] = rot(0, -32 * fs_z)   # nose
        kpts[1] = rot(-4, -35 * fs_z)  # l_eye
        kpts[2] = rot(4, -35 * fs_z)   # r_eye
        kpts[3] = rot(-8, -33 * fs_z)  # l_ear
        kpts[4] = rot(8, -33 * fs_z)   # r_ear
        
        kpts[5] = rot(-15, -20 * fs_z) # l_shoulder
        kpts[6] = rot(15, -20 * fs_z)  # r_shoulder
        
        kpts[7] = rot(-22, -4 * fs_z)  # l_elbow
        kpts[8] = rot(22, -4 * fs_z)   # r_elbow
        kpts[9] = rot(-18, 12 * fs_z)  # l_wrist
        kpts[10] = rot(18, 12 * fs_z)  # r_wrist
        
        kpts[11] = rot(-10, 0)         # l_hip
        kpts[12] = rot(10, 0)          # r_hip
        
        # Crouched compact legs
        kpts[13] = rot(-18, 16)        # l_knee
        kpts[14] = rot(18, 16)         # r_knee
        kpts[15] = rot(-12, 26)        # l_ankle
        kpts[16] = rot(12, 26)         # r_ankle

    # Convert to (x, y, visibility)
    res = {}
    for i in range(17):
        x, y = kpts[i]
        res[i] = (round(x, 2), round(y, 2), 2)

    return res


def render_human_figure(img: Image.Image, kpts: Dict[int, Tuple[float, float, int]], scale: float, occlusion: str) -> Tuple[Image.Image, List[float], Dict[int, Tuple[float, float, int]]]:
    """
    Renders realistic humanoid figure with clothes, limbs, drop shadow onto image.
    Applies occlusion if requested, updating keypoint visibility accordingly.
    """
    draw = ImageDraw.Draw(img, "RGBA")
    
    # Random outfit colors
    is_rescuer = random.random() < 0.35
    if is_rescuer:
        torso_color = (255, random.randint(110, 140), 10, 255) # High-vis orange
        pants_color = (40, 50, 70, 255) # Dark blue cargo
    else:
        torso_color = (random.randint(60, 210), random.randint(60, 200), random.randint(60, 210), 255)
        pants_color = (random.randint(40, 90), random.randint(50, 90), random.randint(60, 110), 255)
    
    skin_color = (random.randint(190, 240), random.randint(150, 195), random.randint(120, 165), 255)
    shadow_color = (20, 20, 25, 90)

    limb_w = max(4, int(7 * scale))
    torso_w = max(8, int(14 * scale))
    head_r = max(5, int(9 * scale))

    # 1. Drop shadow offset
    sh_dx, sh_dy = int(6 * scale), int(8 * scale)

    def draw_capsule(p1, p2, width, color, offset=(0, 0)):
        x1, y1 = p1[0] + offset[0], p1[1] + offset[1]
        x2, y2 = p2[0] + offset[0], p2[1] + offset[1]
        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
        r = width // 2
        draw.ellipse([x1 - r, y1 - r, x1 + r, y1 + r], fill=color)
        draw.ellipse([x2 - r, y2 - r, x2 + r, y2 + r], fill=color)

    # Draw Shadows
    for (idx1, idx2) in [(11, 13), (13, 15), (12, 14), (14, 16), (5, 7), (7, 9), (6, 8), (8, 10)]:
        draw_capsule(kpts[idx1], kpts[idx2], limb_w, shadow_color, offset=(sh_dx, sh_dy))
    # Torso shadow
    mid_sh = ((kpts[5][0] + kpts[6][0])/2, (kpts[5][1] + kpts[6][1])/2)
    mid_hip = ((kpts[11][0] + kpts[12][0])/2, (kpts[11][1] + kpts[12][1])/2)
    draw_capsule(mid_sh, mid_hip, torso_w + 4, shadow_color, offset=(sh_dx, sh_dy))
    # Head shadow
    hx, hy = kpts[0][0] + sh_dx, kpts[0][1] + sh_dy
    draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=shadow_color)

    # 2. Draw Legs
    draw_capsule(kpts[11], kpts[13], limb_w, pants_color)
    draw_capsule(kpts[13], kpts[15], limb_w, pants_color)
    draw_capsule(kpts[12], kpts[14], limb_w, pants_color)
    draw_capsule(kpts[14], kpts[16], limb_w, pants_color)
    # Shoes
    for a_idx in [15, 16]:
        ax, ay = kpts[a_idx][0], kpts[a_idx][1]
        draw.ellipse([ax - limb_w//2, ay - limb_w//2, ax + limb_w//2, ay + limb_w//2], fill=(30, 30, 30, 255))

    # 3. Draw Torso
    draw_capsule(mid_sh, mid_hip, torso_w, torso_color)
    draw.polygon([
        (kpts[5][0], kpts[5][1]), (kpts[6][0], kpts[6][1]),
        (kpts[12][0], kpts[12][1]), (kpts[11][0], kpts[11][1])
    ], fill=torso_color)

    # 4. Draw Arms
    draw_capsule(kpts[5], kpts[7], limb_w, torso_color)
    draw_capsule(kpts[7], kpts[9], limb_w, skin_color)
    draw_capsule(kpts[6], kpts[8], limb_w, torso_color)
    draw_capsule(kpts[8], kpts[10], limb_w, skin_color)

    # 5. Draw Head & Face
    hx, hy = kpts[0][0], kpts[0][1]
    draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=skin_color)
    # Hair / Helmet
    hair_color = (255, 230, 40, 255) if is_rescuer else (random.randint(30, 70), random.randint(25, 55), random.randint(20, 40), 255)
    draw.arc([hx - head_r, hy - head_r, hx + head_r, hy + head_r], start=180, end=360, fill=hair_color, width=max(2, head_r//2))

    # 6. Occlusion Debris
    updated_kpts = dict(kpts)
    if occlusion in ("partial", "heavy"):
        # Draw a slab or rock covering a portion (e.g. legs or arm)
        occ_target = random.choice(["legs", "arm"])
        if occ_target == "legs":
            target_pt = kpts[14] # knee/ankle
            occ_indices = [13, 14, 15, 16] if occlusion == "heavy" else [14, 16]
        else:
            target_pt = kpts[8] # elbow/wrist
            occ_indices = [6, 8, 10] if occlusion == "heavy" else [8, 10]
        
        ox, oy = target_pt[0], target_pt[1]
        sz = int(random.randint(18, 38) * scale)
        c_val = random.randint(85, 140)
        draw.polygon([
            (ox - sz, oy - sz//2),
            (ox + sz, oy - sz//3),
            (ox + sz//2, oy + sz),
            (ox - sz//2, oy + sz)
        ], fill=(c_val, c_val - 5, c_val - 10, 255))

        # Mark occluded keypoints visibility v=1
        for idx in occ_indices:
            kx, ky, _ = updated_kpts[idx]
            updated_kpts[idx] = (kx, ky, 1)

    # Calculate tight bounding box
    all_x = [pt[0] for pt in updated_kpts.values()]
    all_y = [pt[1] for pt in updated_kpts.values()]
    pad = int(10 * scale)
    min_x = max(0.0, min(all_x) - pad)
    min_y = max(0.0, min(all_y) - pad)
    max_x = min(float(img.width), max(all_x) + pad)
    max_y = min(float(img.height), max(all_y) + pad)
    bbox = [round(min_x, 2), round(min_y, 2), round(max_x - min_x, 2), round(max_y - min_y, 2)]

    return img, bbox, updated_kpts


def generate_synthetic_scene(img_w: int, img_h: int, target_posture: str = None) -> Tuple[Image.Image, List[Dict[str, Any]]]:
    """Generate a full synthetic scene with 1 to 3 people."""
    env_types = ["rubble", "grass", "asphalt", "dirt"]
    env = random.choice(env_types)
    img = create_aerial_background(img_w, img_h, env)

    camera_views = ["top_down", "oblique", "oblique", "ground_level"]
    camera_view = random.choice(camera_views)

    altitude_bands = ["low", "mid", "mid", "high"]
    altitude_band = random.choice(altitude_bands)

    # Scale based on altitude band
    if altitude_band == "low":
        base_scale = random.uniform(1.6, 2.4)
    elif altitude_band == "mid":
        base_scale = random.uniform(1.0, 1.6)
    else: # high
        base_scale = random.uniform(0.65, 1.0)

    # Number of persons (mostly 1, occasionally 2 or 3)
    num_persons = 1 if random.random() < 0.82 else random.randint(2, 3)
    
    posture_options = ["upright", "seated", "lying", "crouching"]
    persons_data = []

    for p_idx in range(num_persons):
        if p_idx == 0 and target_posture is not None:
            posture = target_posture
        else:
            posture = random.choices(posture_options, weights=[0.35, 0.20, 0.30, 0.15])[0]

        occlusion = random.choices(["none", "partial", "heavy"], weights=[0.55, 0.35, 0.10])[0]

        # Margin
        margin = int(80 * base_scale)
        cx = random.uniform(margin, max(margin + 50, img_w - margin))
        cy = random.uniform(margin, max(margin + 50, img_h - margin))
        rotation = random.uniform(0, 360)

        kpts = generate_rig_keypoints(posture, camera_view, base_scale, rotation, (cx, cy))
        img, bbox, final_kpts = render_human_figure(img, kpts, base_scale, occlusion)

        # Flatten keypoints to 51 floats
        flat_kpts = []
        for i in range(17):
            kx, ky, kv = final_kpts[i]
            flat_kpts.extend([kx, ky, kv])

        persons_data.append({
            "posture": posture,
            "camera_view": camera_view,
            "altitude_band": altitude_band,
            "occlusion": occlusion,
            "bbox": bbox,
            "keypoints": flat_kpts,
            "label_source": "synthetic",
            "review_status": "reviewed"
        })

    return img, persons_data


if __name__ == "__main__":
    test_img, test_persons = generate_synthetic_scene(640, 640, "lying")
    os.makedirs("test_synth", exist_ok=True)
    test_img.save("test_synth/sample_synth.jpg")
    print(f"Synthetic scene generated with {len(test_persons)} person(s). Saved to test_synth/sample_synth.jpg")
