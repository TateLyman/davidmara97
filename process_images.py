"""
Process real photographs into degraded 1997 scanner output.
Transform real photos to look like they were scanned on a Microtek ScanMaker E3
at 150 DPI in 1997 and saved as low-quality JPEGs on a GeoCities page.
"""
import random
import math
import io
import os
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops, ImageOps

INPUT_DIR = "/Users/tatelyman/the arg/images"
OUTPUT_DIR = "/Users/tatelyman/the arg/images"

random.seed(1997)

def resize_to_90s(img, max_width=468, max_height=350):
    """Resize to period-appropriate web dimensions"""
    img.thumbnail((max_width, max_height), Image.LANCZOS)
    return img

def to_grayscale(img):
    """Convert to grayscale"""
    return img.convert('L')

def to_bw_with_sepia(img):
    """Convert to black and white with sepia tone"""
    gray = img.convert('L')
    result = Image.new('RGB', gray.size)
    for x in range(gray.size[0]):
        for y in range(gray.size[1]):
            v = gray.getpixel((x, y))
            # Warm sepia tone
            r = min(255, int(v * 1.08 + 12))
            g = min(255, int(v * 0.95 + 5))
            b = max(0, int(v * 0.75 - 8))
            result.putpixel((x, y), (r, g, b))
    return result

def darken_significantly(img, factor=0.3):
    """Make image much darker"""
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(factor)

def increase_contrast(img, factor=1.5):
    """Increase contrast"""
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(factor)

def add_film_grain(img, intensity=25):
    """Add realistic film grain"""
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
    """Add dark vignette around edges"""
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
    """Dark edge from scanner lid shadow"""
    w, h = img.size
    draw = ImageDraw.Draw(img)
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
    """Add water/age stains"""
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
    """Add film scratches"""
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

def jpeg_crush(img, quality=20):
    """Simulate terrible 1997 JPEG compression"""
    if img.mode == 'L':
        img = img.convert('RGB')
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=quality, subsampling=2)
    buf.seek(0)
    return Image.open(buf).copy()

def add_scan_bands(img, count=5):
    """Add horizontal brightness bands from bad scanner"""
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

# ============================================================
# Process each real image
# ============================================================

def process_school_exterior():
    """Central High School - make it look like a 1915 archival photo"""
    img = Image.open(os.path.join(INPUT_DIR, "central_real.jpg"))
    img = resize_to_90s(img, 468, 350)
    img = to_bw_with_sepia(img)
    img = increase_contrast(img, 1.3)
    # Darken slightly for age
    img = darken_significantly(img, 0.7)
    img = add_film_grain(img, 18)
    img = add_vignette(img, 0.4)
    img = add_age_stains(img, 2)
    img = add_scratches(img, 12)
    img = add_scanner_edge(img)
    img = add_scan_bands(img, 4)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    img = jpeg_crush(img, 30)
    img.save(os.path.join(OUTPUT_DIR, "central_1915.jpg"), "JPEG", quality=35)
    print(f"Processed central_1915.jpg ({img.size[0]}x{img.size[1]})")

def process_corridor():
    """Dark hallway - make it look like a dark 1941 basement corridor"""
    img = Image.open(os.path.join(INPUT_DIR, "corridor_real.jpg"))
    img = resize_to_90s(img, 400, 300)
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.25)  # Very dark
    img = increase_contrast(img, 1.8)
    img = add_film_grain(img, 30)
    img = add_vignette(img, 0.7)
    img = add_age_stains(img, 1)
    img = add_scratches(img, 6)
    img = add_scanner_edge(img)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.7))
    img = jpeg_crush(img, 22)
    img.save(os.path.join(OUTPUT_DIR, "b2_corridor_1941.jpg"), "JPEG", quality=25)
    print(f"Processed b2_corridor_1941.jpg ({img.size[0]}x{img.size[1]})")

def process_catacomb():
    """Catacomb corridor - use as boiler room / underground passage"""
    img = Image.open(os.path.join(INPUT_DIR, "catacomb_real.jpg"))
    img = resize_to_90s(img, 400, 300)
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.4)
    img = increase_contrast(img, 1.5)
    img = add_film_grain(img, 22)
    img = add_vignette(img, 0.55)
    img = add_age_stains(img, 2)
    img = add_scratches(img, 8)
    img = add_scanner_edge(img)
    img = add_scan_bands(img, 3)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    img = jpeg_crush(img, 25)
    img.save(os.path.join(OUTPUT_DIR, "boiler_1935.jpg"), "JPEG", quality=28)
    print(f"Processed boiler_1935.jpg ({img.size[0]}x{img.size[1]})")

def process_caves():
    """Wabasha Street Caves - use as the sub-level / underground room"""
    img = Image.open(os.path.join(INPUT_DIR, "caves_real.jpg"))
    img = resize_to_90s(img, 400, 300)
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.15)  # Extremely dark
    img = increase_contrast(img, 2.0)
    img = add_film_grain(img, 35)
    img = add_vignette(img, 0.85)
    img = add_age_stains(img, 1)
    img = add_scanner_edge(img)
    img = img.filter(ImageFilter.GaussianBlur(radius=1.0))
    img = jpeg_crush(img, 15)
    img.save(os.path.join(OUTPUT_DIR, "site_c_1942.jpg"), "JPEG", quality=18)
    print(f"Processed site_c_1942.jpg ({img.size[0]}x{img.size[1]})")

def process_doorway():
    """Bricked up doorway - use as the sealed entrance"""
    img = Image.open(os.path.join(INPUT_DIR, "doorway_real.jpg"))
    img = resize_to_90s(img, 400, 300)
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.35)
    img = increase_contrast(img, 1.6)
    img = add_film_grain(img, 28)
    img = add_vignette(img, 0.65)
    img = add_age_stains(img, 2)
    img = add_scratches(img, 10)
    img = add_scanner_edge(img)
    img = add_scan_bands(img, 3)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    img = jpeg_crush(img, 22)
    img.save(os.path.join(OUTPUT_DIR, "sealed_stairwell_1943.jpg"), "JPEG", quality=25)
    print(f"Processed sealed_stairwell_1943.jpg ({img.size[0]}x{img.size[1]})")

def process_doorway_1904():
    """1904 walled-up doorway - use as construction / basement photo"""
    img = Image.open(os.path.join(INPUT_DIR, "doorway_1904.jpg"))
    img = resize_to_90s(img, 400, 300)
    if img.mode == 'L':
        img = img.convert('RGB')
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.5)
    img = increase_contrast(img, 1.4)
    img = add_film_grain(img, 20)
    img = add_vignette(img, 0.5)
    img = add_age_stains(img, 3)
    img = add_scratches(img, 15)
    img = add_scanner_edge(img)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    img = jpeg_crush(img, 25)
    img.save(os.path.join(OUTPUT_DIR, "basement_1912.jpg"), "JPEG", quality=28)
    print(f"Processed basement_1912.jpg ({img.size[0]}x{img.size[1]})")

def process_ledger():
    """Old ledger - use as the Whitmore log scan"""
    img = Image.open(os.path.join(INPUT_DIR, "ledger_real.jpg"))
    img = resize_to_90s(img, 500, 650)
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.8)
    img = increase_contrast(img, 1.2)
    img = add_film_grain(img, 10)
    img = add_age_stains(img, 3)
    img = add_scanner_edge(img)
    img = add_scan_bands(img, 2)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.3))
    img = jpeg_crush(img, 35)
    img.save(os.path.join(OUTPUT_DIR, "whitmore_log.jpg"), "JPEG", quality=38)
    print(f"Processed whitmore_log.jpg ({img.size[0]}x{img.size[1]})")

def process_caves_for_p7():
    """Create the p7 disturbing image - heavily corrupted cave photo"""
    img = Image.open(os.path.join(INPUT_DIR, "caves_real.jpg"))
    img = resize_to_90s(img, 400, 300)
    img = to_bw_with_sepia(img)
    img = darken_significantly(img, 0.1)  # Almost black
    img = increase_contrast(img, 2.5)
    img = add_film_grain(img, 45)
    img = add_vignette(img, 0.95)

    # Add corruption artifacts
    w, h = img.size
    draw = ImageDraw.Draw(img)

    # Horizontal glitch lines
    for _ in range(15):
        y = random.randint(0, h - 1)
        shift = random.randint(-20, 20)
        row = [img.getpixel((x, y)) for x in range(w)]
        for x in range(w):
            src_x = (x + shift) % w
            img.putpixel((x, y), row[src_x])

    # Corruption blocks
    for _ in range(6):
        bx = random.randint(0, w - 40)
        by = random.randint(0, h - 8)
        bw = random.randint(20, 50)
        bh = random.randint(2, 6)
        val = random.randint(5, 20)
        color = (val, max(0, val - 3), max(0, val - 5))
        draw.rectangle([bx, by, bx + bw, by + bh], fill=color)

    img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    img = jpeg_crush(img, 8)  # Extreme compression
    img.save(os.path.join(OUTPUT_DIR, "p7.jpg"), "JPEG", quality=10)
    print(f"Processed p7.jpg ({img.size[0]}x{img.size[1]})")

def process_corridor_for_crack():
    """Create the camcorder still of the crack"""
    img = Image.open(os.path.join(INPUT_DIR, "corridor_real.jpg"))
    img = resize_to_90s(img, 320, 240)
    # Convert to green-tinted nightshot look
    gray = img.convert('L')
    img = Image.new('RGB', gray.size)
    for x in range(gray.size[0]):
        for y in range(gray.size[1]):
            v = gray.getpixel((x, y))
            v = int(v * 0.2)  # Very dark
            img.putpixel((x, y), (max(0, v - 10), min(255, v + 8), max(0, v - 15)))

    img = add_film_grain(img, 40)

    # Add interlacing
    w, h = img.size
    for y in range(0, h, 2):
        for x in range(w - 1, 0, -1):
            img.putpixel((x, y), img.getpixel((max(0, x - 1), y)))

    # Camcorder overlay elements
    draw = ImageDraw.Draw(img)
    # Dark bar at bottom (timestamp area)
    draw.rectangle([0, h - 20, 100, h], fill=(8, 12, 8))
    # REC indicator
    draw.rectangle([w - 45, 5, w - 5, 17], fill=(25, 5, 5))

    img = jpeg_crush(img, 15)
    img.save(os.path.join(OUTPUT_DIR, "crack.jpg"), "JPEG", quality=18)
    print(f"Processed crack.jpg ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    print("Processing real photographs into degraded 1997 scans...\n")

    process_school_exterior()
    process_corridor()
    process_catacomb()
    process_caves()
    process_doorway()
    process_doorway_1904()
    process_ledger()
    process_caves_for_p7()
    process_corridor_for_crack()

    print("\nAll images processed successfully.")
