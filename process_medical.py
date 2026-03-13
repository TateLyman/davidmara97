"""
Process medical textbook images into degraded 1997 scans for the ARG.
Makes them look like they were photocopied from old textbooks, then scanned
on a terrible library scanner and saved as low-quality JPEGs.
"""
import random
import math
import io
import os
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops, ImageOps

INPUT_DIR = "/Users/tatelyman/the arg/images"
OUTPUT_DIR = "/Users/tatelyman/the arg/images"

random.seed(1943)

def resize_to_90s(img, max_width=400, max_height=350):
    img.thumbnail((max_width, max_height), Image.LANCZOS)
    return img

def to_bw_with_sepia(img):
    gray = img.convert('L')
    result = Image.new('RGB', gray.size)
    for x in range(gray.size[0]):
        for y in range(gray.size[1]):
            v = gray.getpixel((x, y))
            r = min(255, int(v * 1.08 + 12))
            g = min(255, int(v * 0.95 + 5))
            b = max(0, int(v * 0.75 - 8))
            result.putpixel((x, y), (r, g, b))
    return result

def darken_significantly(img, factor=0.3):
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(factor)

def increase_contrast(img, factor=1.5):
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(factor)

def add_film_grain(img, intensity=25):
    w, h = img.size
    grain = Image.new(img.mode, (w, h))
    pixels = grain.load()
    for x in range(w):
        for y in range(h):
            noise = int(random.gauss(128, intensity))
            noise = max(0, min(255, noise))
            if img.mode == 'RGB':
                pixels[x, y] = (noise, noise, noise)
            else:
                pixels[x, y] = noise
    grain = grain.filter(ImageFilter.GaussianBlur(radius=0.4))
    return ImageChops.add(img, grain, scale=2, offset=-5)

def add_vignette(img, strength=0.5):
    w, h = img.size
    vig = Image.new('L', (w, h), 255)
    cx, cy = w // 2, h // 2
    max_r = math.sqrt(cx**2 + cy**2)
    for y in range(h):
        for x in range(w):
            dist = math.sqrt((x - cx)**2 + (y - cy)**2)
            factor = 1.0 - (dist / max_r) * strength
            factor = max(0.05, min(1.0, factor))
            vig.putpixel((x, y), int(255 * factor))
    vig = vig.filter(ImageFilter.GaussianBlur(radius=max_r // 6))
    if img.mode == 'RGB':
        vig_rgb = Image.merge('RGB', (vig, vig, vig))
        return ImageChops.multiply(img, vig_rgb)
    return ImageChops.multiply(img, vig)

def add_scanner_edge(img):
    w, h = img.size
    for x in range(min(12, w)):
        darkness = int((12 - x) * 5)
        for y in range(h):
            if img.mode == 'RGB':
                r, g, b = img.getpixel((x, y))
                img.putpixel((x, y), (max(0, r - darkness), max(0, g - darkness), max(0, b - darkness)))
            else:
                v = img.getpixel((x, y))
                img.putpixel((x, y), max(0, v - darkness))
    return img

def add_age_stains(img, count=2):
    w, h = img.size
    for _ in range(count):
        stain = Image.new('L', (w, h), 0)
        sdraw = ImageDraw.Draw(stain)
        cx = random.randint(w // 4, 3 * w // 4)
        cy = random.randint(h // 4, 3 * h // 4)
        for _ in range(4):
            ox = cx + random.randint(-30, 30)
            oy = cy + random.randint(-30, 30)
            sx = random.randint(20, 50)
            sy = random.randint(20, 50)
            sdraw.ellipse([ox - sx, oy - sy, ox + sx, oy + sy], fill=random.randint(8, 20))
        stain = stain.filter(ImageFilter.GaussianBlur(radius=15))
        if img.mode == 'RGB':
            stain_rgb = Image.merge('RGB', (stain, stain, stain))
            img = ImageChops.subtract(img, stain_rgb)
        else:
            img = ImageChops.subtract(img, stain)
    return img

def add_scratches(img, count=10):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for _ in range(count):
        x1 = random.randint(0, w)
        y1 = random.randint(0, h)
        angle = random.uniform(-0.3, 0.3)
        length = random.randint(20, 120)
        x2 = int(x1 + length * math.cos(angle))
        y2 = int(y1 + length * math.sin(angle))
        brightness = random.randint(160, 220)
        color = (brightness, brightness - 10, brightness - 20) if img.mode == 'RGB' else brightness
        draw.line([(x1, y1), (x2, y2)], fill=color, width=1)
    return img

def add_scan_bands(img, count=5):
    w, h = img.size
    for _ in range(count):
        y = random.randint(0, h - 1)
        band_h = random.randint(1, 4)
        brightness = random.randint(-12, 12)
        for dy in range(band_h):
            py = y + dy
            if py >= h:
                break
            for x in range(w):
                if img.mode == 'RGB':
                    r, g, b = img.getpixel((x, py))
                    img.putpixel((x, py), (
                        max(0, min(255, r + brightness)),
                        max(0, min(255, g + brightness)),
                        max(0, min(255, b + brightness))
                    ))
                else:
                    v = img.getpixel((x, py))
                    img.putpixel((x, py), max(0, min(255, v + brightness)))
    return img

def add_photocopy_effect(img):
    """Make it look like a photocopy of a photocopy - high contrast, lost detail"""
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = ImageEnhance.Sharpness(img).enhance(0.3)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    img = ImageEnhance.Contrast(img).enhance(1.5)
    return img

def jpeg_crush(img, quality=20):
    if img.mode == 'L':
        img = img.convert('RGB')
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=quality, subsampling=2)
    buf.seek(0)
    return Image.open(buf).copy()


# ============================================================
# Process each medical image
# ============================================================

def process_hand_xray():
    """Polydactyly X-ray - extra fingers, perfect for the creature's hands"""
    img = Image.open(os.path.join(INPUT_DIR, "medical_hand.jpg"))
    img = resize_to_90s(img, 300, 350)
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.5)
    img = increase_contrast(img, 1.8)
    img = add_film_grain(img, 20)
    img = add_vignette(img, 0.4)
    img = add_age_stains(img, 2)
    img = add_scanner_edge(img)
    img = add_scan_bands(img, 3)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    img = jpeg_crush(img, 22)
    img.save(os.path.join(OUTPUT_DIR, "evidence_hand.jpg"), "JPEG", quality=25)
    print(f"Processed evidence_hand.jpg ({img.size[0]}x{img.size[1]})")

def process_teeth():
    """Supernumerary teeth - too many teeth in a human jaw"""
    img = Image.open(os.path.join(INPUT_DIR, "medical_teeth.jpg"))
    img = resize_to_90s(img, 350, 400)
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.55)
    img = increase_contrast(img, 1.6)
    img = add_photocopy_effect(img)
    img = add_film_grain(img, 22)
    img = add_vignette(img, 0.5)
    img = add_age_stains(img, 3)
    img = add_scratches(img, 8)
    img = add_scanner_edge(img)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.4))
    img = jpeg_crush(img, 20)
    img.save(os.path.join(OUTPUT_DIR, "evidence_teeth.jpg"), "JPEG", quality=22)
    print(f"Processed evidence_teeth.jpg ({img.size[0]}x{img.size[1]})")

def process_ecorche():
    """Ecorche figure - flayed anatomy, looks like something mid-transformation"""
    img = Image.open(os.path.join(INPUT_DIR, "medical_ecorche.jpg"))
    img = resize_to_90s(img, 280, 400)
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.35)
    img = increase_contrast(img, 1.9)
    img = add_film_grain(img, 28)
    img = add_vignette(img, 0.65)
    img = add_age_stains(img, 2)
    img = add_scratches(img, 6)
    img = add_scanner_edge(img)
    img = add_scan_bands(img, 4)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.7))
    img = jpeg_crush(img, 18)
    img.save(os.path.join(OUTPUT_DIR, "evidence_body.jpg"), "JPEG", quality=20)
    print(f"Processed evidence_body.jpg ({img.size[0]}x{img.size[1]})")

def process_specimen():
    """Ruysch anatomical tableau - grotesque arrangement of specimens"""
    img = Image.open(os.path.join(INPUT_DIR, "medical_specimen.jpg"))
    img = resize_to_90s(img, 400, 350)
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.4)
    img = increase_contrast(img, 1.7)
    img = add_film_grain(img, 25)
    img = add_vignette(img, 0.6)
    img = add_age_stains(img, 3)
    img = add_scratches(img, 10)
    img = add_scanner_edge(img)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    img = jpeg_crush(img, 20)
    img.save(os.path.join(OUTPUT_DIR, "evidence_specimen.jpg"), "JPEG", quality=22)
    print(f"Processed evidence_specimen.jpg ({img.size[0]}x{img.size[1]})")

def process_skeleton():
    """Vesalius flayed figure - exposed anatomy standing upright"""
    img = Image.open(os.path.join(INPUT_DIR, "medical_skeleton.jpg"))
    img = resize_to_90s(img, 250, 400)
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.45)
    img = increase_contrast(img, 1.6)
    img = add_photocopy_effect(img)
    img = add_film_grain(img, 20)
    img = add_vignette(img, 0.5)
    img = add_age_stains(img, 2)
    img = add_scratches(img, 12)
    img = add_scanner_edge(img)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    img = jpeg_crush(img, 22)
    img.save(os.path.join(OUTPUT_DIR, "evidence_anatomy.jpg"), "JPEG", quality=25)
    print(f"Processed evidence_anatomy.jpg ({img.size[0]}x{img.size[1]})")

def process_monster():
    """Gould & Pyle cranial deformity - deeply unsettling medical illustration"""
    img = Image.open(os.path.join(INPUT_DIR, "medical_monster.jpg"))
    img = resize_to_90s(img, 280, 380)
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.5)
    img = increase_contrast(img, 1.7)
    img = add_photocopy_effect(img)
    img = add_film_grain(img, 24)
    img = add_vignette(img, 0.55)
    img = add_age_stains(img, 3)
    img = add_scratches(img, 8)
    img = add_scanner_edge(img)
    img = add_scan_bands(img, 3)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    img = jpeg_crush(img, 20)
    img.save(os.path.join(OUTPUT_DIR, "evidence_cranial.jpg"), "JPEG", quality=22)
    print(f"Processed evidence_cranial.jpg ({img.size[0]}x{img.size[1]})")

def process_pathology():
    """Extra digits clinical photo"""
    img = Image.open(os.path.join(INPUT_DIR, "medical_pathology.jpg"))
    img = resize_to_90s(img, 350, 250)
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.45)
    img = increase_contrast(img, 1.8)
    img = add_film_grain(img, 26)
    img = add_vignette(img, 0.55)
    img = add_age_stains(img, 2)
    img = add_scanner_edge(img)
    img = add_scan_bands(img, 4)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    img = jpeg_crush(img, 18)
    img.save(os.path.join(OUTPUT_DIR, "evidence_digits.jpg"), "JPEG", quality=20)
    print(f"Processed evidence_digits.jpg ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    print("Processing medical textbook images...\n")

    process_hand_xray()
    process_teeth()
    process_ecorche()
    process_specimen()
    process_skeleton()
    process_monster()
    process_pathology()

    print("\nAll medical images processed.")
