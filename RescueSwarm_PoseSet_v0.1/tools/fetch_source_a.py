"""
fetch_source_a.py - Fetch and Pre-label Open-Licensed Real Aerial / SAR Images
RescueSwarm Pose Dataset (NIDAR 2.0 Track 1)

Queries Wikimedia Commons for openly licensed images (CC0, CC-BY, CC-BY-SA, Public Domain)
related to search-and-rescue, casualty simulations, aerial/elevated viewpoints, and outdoor poses.
Runs YOLOv8-pose, applies automated geometric sanity checks, and records full license metadata.
"""

import os
import re
import math
import json
import time
import requests
from io import BytesIO
from PIL import Image
from typing import Dict, List, Tuple, Any
from ultralytics import YOLO


SEARCH_QUERIES = [
    "search and rescue drill",
    "casualty simulation",
    "first aid exercise casualty",
    "disaster response training exercise",
    "flood rescue training",
    "earthquake rescue drill",
    "stretcher rescue exercise",
    "mountain rescue training",
    "paramedic training victim",
    "wilderness search and rescue",
    "aerial view people park",
    "drone photo people field",
    "overhead view people grass",
    "sunbathing aerial view lawn",
    "sports overhead view",
    "urban search and rescue USAR drill",
    "mass casualty incident drill",
    "triage drill simulation",
    "firefighter rescue drill victim",
    "evacuation drill people outdoor",
    "lifeguard rescue drill beach",
    "air ambulance exercise casualty"
]

HEADERS = {"User-Agent": "RescueSwarmDatasetBot/1.0 (academic research for NIDAR student drone challenge; contact: rescueswarm@nidar.in)"}


def clean_html(text: str) -> str:
    """Remove HTML tags from author/credit strings."""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip().replace('\n', ' ').replace('\r', '')


def classify_posture_and_attributes(keypoints_list: List[float], bbox: List[float], img_w: int, img_h: int) -> Tuple[str, str, str, str]:
    """
    Apply geometric heuristics to infer posture, camera view, altitude band, and occlusion.
    """
    pts = {}
    for i in range(17):
        pts[i] = (keypoints_list[i*3], keypoints_list[i*3+1], int(keypoints_list[i*3+2]))

    # Midpoints
    l_sh, r_sh = pts[5], pts[6]
    l_hip, r_hip = pts[11], pts[12]
    l_knee, r_knee = pts[13], pts[14]
    l_ank, r_ank = pts[15], pts[16]

    num_vis = sum(1 for i in range(17) if pts[i][2] > 0)

    # Occlusion
    if num_vis >= 14:
        occlusion = "none"
    elif num_vis >= 8:
        occlusion = "partial"
    else:
        occlusion = "heavy"

    # Altitude band
    bw, bh = bbox[2], bbox[3]
    diag = (bw**2 + bh**2)**0.5
    img_diag = (img_w**2 + img_h**2)**0.5
    ratio = diag / max(1.0, img_diag)

    if ratio < 0.14:
        altitude_band = "high"
    elif ratio < 0.35:
        altitude_band = "mid"
    else:
        altitude_band = "low"

    # Torso orientation
    sh_vis = (l_sh[2] > 0 or r_sh[2] > 0)
    hip_vis = (l_hip[2] > 0 or r_hip[2] > 0)

    posture = "unknown"
    camera_view = "oblique"

    if sh_vis and hip_vis:
        mid_sh_x = (l_sh[0] + r_sh[0])/2.0 if (l_sh[2] > 0 and r_sh[2] > 0) else (l_sh[0] if l_sh[2] > 0 else r_sh[0])
        mid_sh_y = (l_sh[1] + r_sh[1])/2.0 if (l_sh[2] > 0 and r_sh[2] > 0) else (l_sh[1] if l_sh[2] > 0 else r_sh[1])
        mid_hip_x = (l_hip[0] + r_hip[0])/2.0 if (l_hip[2] > 0 and r_hip[2] > 0) else (l_hip[0] if l_hip[2] > 0 else r_hip[0])
        mid_hip_y = (l_hip[1] + r_hip[1])/2.0 if (l_hip[2] > 0 and r_hip[2] > 0) else (l_hip[1] if l_hip[2] > 0 else r_hip[1])

        dx = mid_sh_x - mid_hip_x
        dy = mid_sh_y - mid_hip_y
        dist = (dx**2 + dy**2)**0.5

        if dist > 3.0:
            angle_from_vert = math.degrees(math.atan2(abs(dx), abs(dy)))
            if angle_from_vert > 55.0 or abs(dy) < abs(dx) * 0.7:
                posture = "lying"
            else:
                # Vertical torso: check legs
                has_knees = (l_knee[2] > 0 or r_knee[2] > 0)
                if has_knees:
                    knee_y = (l_knee[1] + r_knee[1])/2.0 if (l_knee[2] > 0 and r_knee[2] > 0) else (l_knee[1] if l_knee[1] > 0 else r_knee[1])
                    thigh_dy = abs(knee_y - mid_hip_y)
                    torso_dy = abs(dy)
                    if thigh_dy < torso_dy * 0.5:
                        posture = "seated" if bw > bh * 0.9 else "crouching"
                    else:
                        posture = "upright"
                else:
                    posture = "upright"
        else:
            posture = "crouching"
    else:
        # Fallback based on bbox aspect ratio
        if bw > bh * 1.3:
            posture = "lying"
        elif bh > bw * 1.5:
            posture = "upright"
        else:
            posture = "crouching"

    # Camera view heuristic
    if bw > bh * 1.1 and posture == "upright":
        camera_view = "top_down"
    elif ratio < 0.15:
        camera_view = "top_down" if abs(bw - bh) < 30 else "oblique"
    elif posture == "lying" and bh > bw * 0.8:
        camera_view = "top_down"
    else:
        camera_view = "oblique"

    return posture, camera_view, altitude_band, occlusion


def sanity_check_person(keypoints: List[float], bbox: List[float], img_w: int, img_h: int) -> bool:
    """Verify detected person is valid and keypoints are geometrically sane."""
    bx, by, bw, bh = bbox
    if bw < 15 or bh < 15:
        return False
    if bx < -10 or by < -10 or (bx + bw) > (img_w + 10) or (by + bh) > (img_h + 10):
        return False

    num_vis = sum(1 for i in range(17) if keypoints[i*3+2] > 0)
    if num_vis < 5:
        return False

    # Check keypoint bounds
    for i in range(17):
        if keypoints[i*3+2] > 0:
            kx = keypoints[i*3]
            ky = keypoints[i*3+1]
            if kx < 0 or kx > img_w or ky < 0 or ky > img_h:
                return False

    return True
