# backend/services/ocr_service.py

import pytesseract
from PIL import Image
import fitz
import io

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    ext = filename.lower().split(".")[-1]
    if ext == "pdf":
        return _extract_from_pdf(file_bytes)
    elif ext in ["png", "jpg", "jpeg", "tiff", "bmp", "webp"]:
        return _extract_from_image(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")

def _extract_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    if len(text.strip()) < 50:
        text = ""
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text += pytesseract.image_to_string(img, lang="eng")
    doc.close()
    return text.strip()

def _extract_from_image(file_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(file_bytes))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    return pytesseract.image_to_string(img, lang="eng").strip()