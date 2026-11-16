import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger("evidencerag.quality")

def assess_image_quality(image_path: str) -> Dict[str, Any]:
    """
    Assess document image quality using OpenCV:
    - Laplacian variance for blur detection
    - Resolution check (width x height)
    - Aspect ratio & potential rotation check
    - Brightness / contrast analysis
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            # Try loading with PIL first then convert to numpy
            pil_img = Image.open(image_path)
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Blur detection using Laplacian variance
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Normal clean documents typically have variance > 120-150.
        # Blurry scans typically have variance < 90.
        is_blurry = bool(laplacian_var < 95.0)

        # 2. Resolution check
        # A good scanned doc should be at least 700x700 or ~150-300 DPI
        is_low_res = bool(w < 650 or h < 650)

        # 3. Brightness & contrast
        mean_brightness = float(np.mean(gray))
        contrast = float(np.std(gray))
        is_too_dark = bool(mean_brightness < 40)
        is_washed_out = bool(contrast < 20)

        # 4. Rotation / Orientation heuristic
        # If text lines are predominantly vertical or orientation flag
        is_rotated = False
        try:
            # Edge detection to check dominant angles
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
            if lines is not None and len(lines) > 10:
                vertical_count = 0
                horizontal_count = 0
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi)
                    if 75 <= angle <= 105:
                        vertical_count += 1
                    elif angle <= 15 or angle >= 165:
                        horizontal_count += 1
                if vertical_count > horizontal_count * 2.5 and vertical_count > 15:
                    is_rotated = True
        except Exception as e:
            logger.debug(f"Hough rotation check non-fatal error: {e}")

        # Compute overall quality score between 0.0 and 1.0
        score = 1.0
        if is_blurry:
            score -= 0.35
        if is_low_res:
            score -= 0.25
        if is_too_dark or is_washed_out:
            score -= 0.20
        if is_rotated:
            score -= 0.15
        
        quality_score = max(0.1, min(1.0, round(score, 2)))

        return {
            "width": w,
            "height": h,
            "laplacian_variance": round(float(laplacian_var), 2),
            "is_blurry": is_blurry,
            "is_low_res": is_low_res,
            "is_rotated": is_rotated,
            "mean_brightness": round(mean_brightness, 2),
            "contrast": round(contrast, 2),
            "quality_score": quality_score
        }
    except Exception as e:
        logger.error(f"Error assessing image quality for {image_path}: {e}")
        return {
            "width": 0,
            "height": 0,
            "laplacian_variance": 0.0,
            "is_blurry": False,
            "is_low_res": False,
            "is_rotated": False,
            "mean_brightness": 128.0,
            "contrast": 50.0,
            "quality_score": 0.8
        }
