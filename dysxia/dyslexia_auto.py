import language_tool_python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import difflib
import re
import cv2
import os
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
from spellchecker import SpellChecker


# ---------- Setup device ----------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# -------------------------
# Load pretrained TrOCR model and move to device
# -------------------------
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
ocr_model = VisionEncoderDecoderModel.from_pretrained(
    "microsoft/trocr-base-handwritten").to(device)


# Spell checker
spell = SpellChecker(distance=2)  # tweaking distance for better correction


# -------------------------
# Recognize one row or whole image
# -------------------------


def extract_text_from_image(image_path):
    image = Image.open(image_path).convert("RGB")
    pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
    generated_ids = ocr_model.generate(pixel_values, max_length=512)
    text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return text


def correct_text(text):
    corrected = []
    for word in text.split():
        corrected.append(spell.correction(word) or word)
    return " ".join(corrected)


# -------------------------
# Adaptive row extraction
# -------------------------


def extract_rows_from_page(page_path, save_dir="rows"):
    os.makedirs(save_dir, exist_ok=True)
    img = cv2.imread(page_path, cv2.IMREAD_GRAYSCALE)

    # If image is very small (likely just 1 row) → skip segmentation
    if img.shape[0] < 200:
        raw = extract_text_from_image(page_path)
        return [(raw, correct_text(raw))]

    # Adaptive thresholding for robustness
    thresh = cv2.adaptiveThreshold(
        img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 35, 15
    )

    # Adaptive kernel based on image width
    kernel_width = max(30, img.shape[1] // 20)  # scale with width
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 5))
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    # Find contours (rows of text)
    contours, _ = cv2.findContours(
        dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    row_results = []
    for i, c in enumerate(sorted(contours, key=lambda ctr: cv2.boundingRect(ctr)[1])):
        x, y, w, h = cv2.boundingRect(c)
        if h < 20:  # ignore noise
            continue
        row_crop = img[y:y + h, x:x + w]
        row_path = os.path.join(save_dir, f"row_{i}.png")
        cv2.imwrite(row_path, row_crop)
        raw_text = extract_text_from_image(row_path)
        row_results.append((raw_text))

    # If only one row found → return whole image OCR instead
    if len(row_results) <= 1:
        raw = extract_text_from_image(page_path)
        return [raw]

    return row_results


# ---------- Global initializations (load once) ----------
tool = language_tool_python.LanguageTool("en-IN")

MODEL_NAME = "prithivida/grammar_error_correcter_v1"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
correction_model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)


# ---------- Helpers ----------


def print_diff(a: str, b: str):
    for line in difflib.ndiff(a.split(), b.split()):
        if line.startswith("- ") or line.startswith("+ "):
            print(line)


def preserve_case(orig: str, corr: str) -> str:
    if orig.isupper():
        return corr.upper()
    if orig[0].isupper():
        return corr.capitalize()
    return corr


# ---------- 1) Better spell correction (preserve punctuation & case) ----------
WORD_RE = re.compile(r"[A-Za-z']+")


def spell_correct(text: str) -> str:
    def repl(match):
        w = match.group(0)
        wl = w.lower()
        if wl in spell:
            return w
        suggestion = spell.correction(wl)
        if not suggestion:
            return w
        return preserve_case(w, suggestion)
    return WORD_RE.sub(repl, text)


# ---------- 2) Grammar correction (use full-text check for context) ----------


def grammar_correct(text: str) -> str:
    matches = tool.check(text)
    corrected = language_tool_python.utils.correct(text, matches)
    return corrected


# ---------- Sentence splitter (no NLTK needed) ----------


def split_sentences(text: str):
    # Split on ., ?, ! but keep punctuation attached
    return re.split(r'(?<=[.!?])\s+', text.strip())


# ---------- 3) Transformer-based refinement (with truncation safety) ----------


def model_correct(text: str, max_length: int = 512) -> str:
    sentences = split_sentences(text)
    corrected_sentences = []
    for sent in sentences:
        inputs = tokenizer(sent, return_tensors="pt",
                           truncation=True, max_length=1024).to(device)
        out = correction_model.generate(**inputs, max_length=max_length)
        corrected = tokenizer.decode(out[0], skip_special_tokens=True)
        corrected_sentences.append(corrected)
    return " ".join(corrected_sentences)


# ---------- Combined pipeline ----------


def stepwise_correct(text: str):
    print("=== ORIGINAL ===")
    print(text, "\n")

    print("=== AFTER SPELL CHECK ===")
    s1 = spell_correct(text)
    print(s1)

    print("=== AFTER LANGUAGE TOOL (Grammar) ===")
    s2 = grammar_correct(s1)
    print(s2)

    print("=== AFTER TRANSFORMER REFINEMENT ===")
    s3 = model_correct(s2)
    print(s3)

    return s1, s2, s3


# ---------- For frontend: One-call, all results ----------


def process_image_for_dyslexia(image_path):
    """
    Given an image path, runs the full dyslexia pipeline and returns all intermediate steps:
    - OCR (single line text from image)
    - Spell correction (s1)
    - Grammar correction (s2)
    - Transformer/model correction (s3)
    - Final result (same as s3, unless post-processing is added)
    """
    rows = extract_rows_from_page(image_path)
    # join rows (row is tuple or str):
    if isinstance(rows[0], tuple):
        ocr_text = ' '.join([r[0] for r in rows])
    else:
        ocr_text = ' '.join(rows)

    s1, s2, s3 = stepwise_correct(ocr_text)
    final = stepwise_correct(ocr_text)

    return {
        "ocr": ocr_text,
        "spell_corrected": s1,
        "grammar_corrected": s2,
        "transformer_refined": s3,
        "final": final
    }
