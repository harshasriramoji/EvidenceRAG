import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pymupdf
from PIL import Image
import pytesseract
import cv2
import numpy as np

from backend.app.core.config import settings
from backend.app.services.ocr.quality import assess_image_quality

logger = logging.getLogger("evidencerag.ocr")

# Configure tesseract executable if available in PATH or custom path
TESSERACT_AVAILABLE = False
AVAILABLE_LANGS: List[str] = ["eng"]

try:
    if shutil.which("tesseract"):
        pytesseract.pytesseract.tesseract_cmd = "tesseract"
        TESSERACT_AVAILABLE = True
    elif os.path.exists(settings.TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        TESSERACT_AVAILABLE = True
    elif os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        TESSERACT_AVAILABLE = True

    if TESSERACT_AVAILABLE:
        try:
            AVAILABLE_LANGS = pytesseract.get_languages()
        except Exception:
            AVAILABLE_LANGS = ["eng"]
except Exception:
    TESSERACT_AVAILABLE = False


def preprocess_image_with_opencv(image_path: str) -> np.ndarray:
    """
    OpenCV document enhancement pipeline:
    - Grayscale conversion
    - Noise removal (median blur)
    - Contrast enhancement (CLAHE)
    - Deskewing & rotation angle correction
    - Adaptive thresholding
    """
    img = cv2.imread(image_path)
    if img is None:
        pil_img = Image.open(image_path)
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # 1. Grayscale conversion
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Noise removal
    denoised = cv2.medianBlur(gray, 3)

    # 3. Image enhancement (CLAHE for contrast equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # 4. Deskewing
    coords = np.column_stack(np.where(enhanced > 0))
    if len(coords) > 50:
        rect = cv2.minAreaRect(coords)
        angle = rect[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        if abs(angle) > 0.5 and abs(angle) < 45.0:
            (h, w) = enhanced.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            enhanced = cv2.warpAffine(enhanced, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # 5. Adaptive thresholding for crisp OCR binarization
    thresh = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return thresh


def process_document_ocr(file_path: str, mime_type: str, lang: str = "eng") -> Dict[str, Any]:
    """
    Process document via multi-engine OCR:
    - Extracts text per page and block-level bounding boxes
    - Supports English and Telugu OCR when language packs are installed
    - Evaluates image quality (blur, resolution, rotation)
    - Returns structured extraction dictionary
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    pages_text: List[Dict[str, Any]] = []
    text_blocks: List[Dict[str, Any]] = []
    full_text = ""
    quality_info = {
        "width": 800,
        "height": 1100,
        "laplacian_variance": 150.0,
        "is_blurry": False,
        "is_low_res": False,
        "is_rotated": False,
        "quality_score": 1.0
    }
    page_count = 1
    tess_lang = "eng"
    telugu_installed = "tel" in AVAILABLE_LANGS
    ocr_notice = None

    if lang in ("tel", "tel+eng", "eng+tel"):
        if telugu_installed:
            tess_lang = "tel+eng"
        else:
            ocr_notice = "Telugu OCR language data ('tel.traineddata') is not installed in Tesseract; fell back to English OCR."
            tess_lang = "eng"

    if mime_type == "application/pdf" or path.suffix.lower() == ".pdf":
        try:
            doc = pymupdf.open(file_path)
            page_count = len(doc)

            for page_idx in range(page_count):
                page = doc[page_idx]
                p_text = page.get_text() or ""
                p_width = page.rect.width or 612.0
                p_height = page.rect.height or 792.0

                # Extract layout blocks with bounding boxes
                raw_blocks = page.get_text("blocks") or []
                for b in raw_blocks:
                    if len(b) >= 5 and b[4].strip():
                        text_blocks.append({
                            "page_number": page_idx + 1,
                            "text": b[4].strip(),
                            "bbox": [
                                round(b[0] / p_width, 4),
                                round(b[1] / p_height, 4),
                                round((b[2] - b[0]) / p_width, 4),
                                round((b[3] - b[1]) / p_height, 4)
                            ]
                        })

                # Render first page as pixmap to assess visual quality
                if page_idx == 0:
                    pix = page.get_pixmap(dpi=150)
                    temp_img_path = path.parent / f"_temp_preview_{path.stem}.png"
                    pix.save(str(temp_img_path))
                    quality_info = assess_image_quality(str(temp_img_path))
                    try:
                        if temp_img_path.exists():
                            temp_img_path.unlink()
                    except Exception:
                        pass

                # If PDF text is empty or very sparse, attempt OCR on page pixmap if tesseract is available
                if len(p_text.strip()) < 15 and TESSERACT_AVAILABLE:
                    pix = page.get_pixmap(dpi=200)
                    temp_page_img = path.parent / f"_temp_ocr_{path.stem}_{page_idx}.png"
                    pix.save(str(temp_page_img))
                    try:
                        ocr_text = pytesseract.image_to_string(Image.open(str(temp_page_img)), lang=tess_lang)
                        if len(ocr_text.strip()) > len(p_text.strip()):
                            p_text = ocr_text
                    except Exception as e:
                        logger.warning(f"Tesseract OCR fallback failed for page {page_idx}: {e}")
                    finally:
                        if temp_page_img.exists():
                            try:
                                temp_page_img.unlink()
                            except Exception:
                                pass

                pages_text.append({
                    "page_number": page_idx + 1,
                    "text": p_text.strip()
                })
                full_text += p_text + "\n"

            doc.close()
        except Exception as e:
            logger.error(f"Error parsing PDF with PyMuPDF: {e}")
            raise e

    else:
        # Image file (JPG, PNG)
        quality_info = assess_image_quality(file_path)
        img_text = ""

        if TESSERACT_AVAILABLE:
            try:
                preprocessed = preprocess_image_with_opencv(file_path)
                img_text = pytesseract.image_to_string(Image.fromarray(preprocessed), lang=tess_lang)
                if not img_text.strip():
                    img_text = pytesseract.image_to_string(Image.open(file_path), lang=tess_lang)
            except Exception as e:
                logger.warning(f"Tesseract failed on image {file_path}: {e}")

        # If tesseract is not available or extracted nothing, return clear descriptive indicator
        if not img_text.strip():
            img_text = f"[Image Document: {path.name}]\nImage dimensions: {quality_info['width']}x{quality_info['height']}"

        # Estimate block coordinates
        text_blocks.append({
            "page_number": 1,
            "text": img_text.strip(),
            "bbox": [0.1, 0.1, 0.8, 0.8]
        })

        pages_text.append({
            "page_number": 1,
            "text": img_text.strip()
        })
        full_text = img_text

    return {
        "page_count": page_count,
        "full_text": full_text.strip(),
        "pages": pages_text,
        "blocks": text_blocks,
        "language_used": tess_lang,
        "telugu_ocr_installed": telugu_installed,
        "ocr_notice": ocr_notice,
        "quality": quality_info,
        "is_blurry": quality_info.get("is_blurry", False),
        "is_low_res": quality_info.get("is_low_res", False),
        "is_rotated": quality_info.get("is_rotated", False),
        "quality_score": quality_info.get("quality_score", 1.0)
    }
