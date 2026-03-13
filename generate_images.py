"""
Generate highly realistic degraded photographs for the ARG.
Uses layered noise, realistic film grain, proper scanner artifacts,
and authentic period-appropriate degradation.
"""
import random
import os
import math
import io

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops

OUTPUT_DIR = "/Users/tatelyman/the arg/images"

def film_grain(img, intensity=25, monochrome=True):
    """Realistic film grain using Gaussian-distributed noise"""
    w, h = img.size
    grain = Image.new('L', (w, h))
    pixels = grain.load()
    for x in range(w):
        for y in range(h):
            # Use gaussian-like distribution for more realistic grain
            val = int(128 + random.gauss(0, intensity))
            pixels[x, y] = max(0, min(255, val))
    grain = grain.filter(ImageFilter.GaussianBlur(radius=0.3))

    if img.mode == 'L':
        # Blend grain with image
        result = ImageChops.add(img, grain, scale=2, offset=-10)
        return result
    else:
        grain_rgb = Image.merge('RGB', (grain, grain, grain))
        result = ImageChops.add(img, grain_rgb, scale=2, offset=-10)
        return result

def scanner_artifacts(img):
    """Simulate a 1997 flatbed scanner - bands, slight skew, edge darkening"""
    w, h = img.size
    draw = ImageDraw.Draw(img)

    # Scan bands (horizontal brightness variation)
    for y in range(h):
        if random.random() < 0.02:
            band_brightness = random.randint(-8, 8)
            for x in range(w):
                if img.mode == 'L':
                    v = img.getpixel((x, y))
                    img.putpixel((x, y), max(0, min(255, v + band_brightness)))
                else:
                    r, g, b = img.getpixel((x, y))[:3]
                    img.putpixel((x, y), (
                        max(0, min(255, r + band_brightness)),
                        max(0, min(255, g + band_brightness)),
                        max(0, min(255, b + band_brightness))
                    ))

    # Edge shadow (scanner lid not fully closed on thick material)
    for y in range(h):
        for x in range(min(15, w)):
            if img.mode == 'L':
                v = img.getpixel((x, y))
                darkness = int((15 - x) * 2.5)
                img.putpixel((x, y), max(0, v - darkness))
            else:
                r, g, b = img.getpixel((x, y))[:3]
                darkness = int((15 - x) * 2.5)
                img.putpixel((x, y), (max(0, r - darkness), max(0, g - darkness), max(0, b - darkness)))

    return img

def age_damage(img, stains=3, foxing=20):
    """Water stains, foxing spots, and age discoloration"""
    w, h = img.size
    draw = ImageDraw.Draw(img)

    # Water/moisture stains (large soft dark areas)
    for _ in range(stains):
        cx = random.randint(w//4, 3*w//4)
        cy = random.randint(h//4, 3*h//4)
        size = random.randint(30, 80)

        stain = Image.new('L', (w, h), 0)
        stain_draw = ImageDraw.Draw(stain)
        # Organic shape using overlapping ellipses
        for _ in range(5):
            ox = cx + random.randint(-size//3, size//3)
            oy = cy + random.randint(-size//3, size//3)
            sx = random.randint(size//2, size)
            sy = random.randint(size//2, size)
            stain_draw.ellipse([ox-sx, oy-sy, ox+sx, oy+sy], fill=random.randint(10, 25))

        stain = stain.filter(ImageFilter.GaussianBlur(radius=size//3))

        if img.mode == 'L':
            img = ImageChops.subtract(img, stain)
        else:
            stain_rgb = Image.merge('RGB', (stain, stain, stain))
            img = ImageChops.subtract(img, stain_rgb)

    # Foxing (small brown spots from age)
    for _ in range(foxing):
        x = random.randint(0, w-1)
        y = random.randint(0, h-1)
        r = random.randint(1, 4)
        if img.mode == 'L':
            draw = ImageDraw.Draw(img)
            draw.ellipse([x-r, y-r, x+r, y+r], fill=random.randint(100, 150))
        else:
            draw = ImageDraw.Draw(img)
            brownish = (random.randint(110, 160), random.randint(90, 130), random.randint(60, 90))
            draw.ellipse([x-r, y-r, x+r, y+r], fill=brownish)

    return img

def vignette(img, strength=0.6):
    """Realistic lens vignette"""
    w, h = img.size
    vig = Image.new('L', (w, h), 255)
    draw = ImageDraw.Draw(vig)
    cx, cy = w // 2, h // 2
    max_r = math.sqrt(cx**2 + cy**2)

    for y in range(h):
        for x in range(w):
            dist = math.sqrt((x - cx)**2 + (y - cy)**2)
            factor = 1.0 - (dist / max_r) * strength
            factor = max(0.1, min(1.0, factor))
            vig.putpixel((x, y), int(255 * factor))

    vig = vig.filter(ImageFilter.GaussianBlur(radius=max_r // 8))

    if img.mode == 'L':
        return ImageChops.multiply(img, vig)
    else:
        vig_rgb = Image.merge('RGB', (vig, vig, vig))
        return ImageChops.multiply(img, vig_rgb)

def sepia_tone(img):
    """Convert to sepia for period-appropriate look"""
    if img.mode == 'L':
        img = img.convert('RGB')
    r, g, b = img.split()
    # Manual sepia
    result = Image.new('RGB', img.size)
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            rr, gg, bb = img.getpixel((x, y))[:3]
            tr = int(0.393 * rr + 0.769 * gg + 0.189 * bb)
            tg = int(0.349 * rr + 0.686 * gg + 0.168 * bb)
            tb = int(0.272 * rr + 0.534 * gg + 0.131 * bb)
            result.putpixel((x, y), (min(255, tr), min(255, tg), min(255, tb)))
    return result

def jpeg_degrade(img, quality=25):
    """Simulate 1997 JPEG compression artifacts"""
    if img.mode == 'L':
        img = img.convert('RGB')
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=quality, subsampling=2)
    buf.seek(0)
    return Image.open(buf).copy()

# ============================================================
# Create realistic dark architectural photograph
# ============================================================
def make_dark_photo(width, height, scene_type="corridor"):
    """
    Create a realistic-looking photograph by building up layers
    of light and shadow, simulating actual photographic conditions.
    """
    img = Image.new('L', (width, height), 20)
    draw = ImageDraw.Draw(img)

    if scene_type == "exterior":
        # Sky gradient (overcast, period-appropriate)
        for y in range(height * 2 // 5):
            val = 180 - int(y * 0.3) + random.randint(-3, 3)
            draw.line([(0, y), (width-1, y)], fill=max(100, min(220, val)))

        # Treeline silhouette
        tree_y = height * 2 // 5
        for x in range(width):
            offset = int(15 * math.sin(x * 0.03) + 10 * math.sin(x * 0.07) + 5 * math.sin(x * 0.15))
            for dy in range(-20 - offset, 10):
                py = tree_y + dy
                if 0 <= py < height:
                    if dy < -offset:
                        img.putpixel((x, py), random.randint(40, 70))

        # Building mass (dark, imposing)
        bldg_left = width // 6
        bldg_right = width * 5 // 6
        bldg_top = height // 5
        bldg_bottom = height * 3 // 4

        for y in range(bldg_top, bldg_bottom):
            for x in range(bldg_left, bldg_right):
                val = 80 + random.randint(-5, 5)
                # Slight variation for texture
                if (x - bldg_left) % 12 < 1 or (y - bldg_top) % 8 < 1:
                    val -= 10  # mortar lines
                img.putpixel((x, y), max(30, min(130, val)))

        # Windows (dark rectangles in building)
        win_rows = 4
        win_cols = 10
        for row in range(win_rows):
            for col in range(win_cols):
                wx = bldg_left + 15 + col * (bldg_right - bldg_left - 30) // win_cols
                wy = bldg_top + 15 + row * (bldg_bottom - bldg_top - 30) // win_rows
                ww, wh = 12, 20
                draw.rectangle([wx, wy, wx+ww, wy+wh], fill=random.randint(35, 55))

        # Central entrance (gothic arch suggestion)
        ent_x = width // 2
        ent_w = 30
        draw.rectangle([ent_x - ent_w, bldg_bottom - 60, ent_x + ent_w, bldg_bottom], fill=40)
        draw.arc([ent_x - ent_w, bldg_bottom - 90, ent_x + ent_w, bldg_bottom - 40], 180, 360, fill=75, width=2)

        # Tower element
        tower_w = 25
        draw.rectangle([ent_x - tower_w, bldg_top - 30, ent_x + tower_w, bldg_top], fill=75)
        # Crenellations
        for i in range(5):
            cx = ent_x - tower_w + i * (tower_w * 2 // 5)
            draw.rectangle([cx, bldg_top - 40, cx + 6, bldg_top - 30], fill=70)

        # Ground/lawn
        for y in range(bldg_bottom, height):
            for x in range(width):
                val = 60 + int((y - bldg_bottom) * 0.5) + random.randint(-8, 8)
                img.putpixel((x, y), max(30, min(120, val)))

        # Pathway
        path_cx = width // 2
        for y in range(bldg_bottom, height):
            pw = 15 + (y - bldg_bottom) // 2
            for x in range(path_cx - pw, path_cx + pw):
                if 0 <= x < width:
                    img.putpixel((x, y), random.randint(90, 115))

    elif scene_type == "corridor":
        # Dark corridor with perspective convergence
        vanishing_x = width // 2
        vanishing_y = height * 2 // 5

        for y in range(height):
            for x in range(width):
                # Distance from vanishing point determines brightness
                dy = abs(y - vanishing_y)
                dx = abs(x - vanishing_x)

                # Perspective lines
                if dy > 10:
                    expected_x = vanishing_x + (x - vanishing_x) * (vanishing_y) / max(1, y)
                    wall_dist = abs(x - expected_x)

                    if y > vanishing_y:
                        # Floor
                        floor_val = 20 + int(dy * 0.15) + random.randint(-3, 3)
                        # Wall areas
                        perspective_width = int((y - vanishing_y) * 0.8)
                        if abs(x - vanishing_x) > perspective_width:
                            val = 30 + random.randint(-3, 3)  # wall
                        else:
                            val = floor_val
                    else:
                        val = 15 + random.randint(-2, 2)  # ceiling

                    img.putpixel((x, y), max(3, min(80, val)))

        # Door at vanishing point
        door_w = 20
        door_h = 40
        draw.rectangle([vanishing_x - door_w, vanishing_y - door_h//2,
                        vanishing_x + door_w, vanishing_y + door_h//2],
                       fill=8, outline=35)
        # Door slightly ajar (thin bright line)
        draw.line([(vanishing_x - 5, vanishing_y - door_h//2 + 3),
                   (vanishing_x - 5, vanishing_y + door_h//2 - 3)], fill=3, width=2)

        # Weak light source (single bulb effect)
        for radius in range(80):
            brightness = max(0, int(35 * math.exp(-radius / 30.0)))
            for angle in range(0, 360, 3):
                rad = math.radians(angle)
                px = int(vanishing_x + radius * math.cos(rad))
                py = int(vanishing_y + 60 + radius * math.sin(rad) * 0.6)
                if 0 <= px < width and 0 <= py < height:
                    current = img.getpixel((px, py))
                    img.putpixel((px, py), min(90, current + brightness))

        # Drag marks on walls
        for i in range(8):
            mark_y = random.randint(vanishing_y + 20, height - 40)
            mark_x_start = random.randint(10, width // 4) if random.random() > 0.5 else random.randint(3 * width // 4, width - 10)
            length = random.randint(40, 120)
            direction = 1 if mark_x_start < width // 2 else -1
            for j in range(length):
                mx = mark_x_start + j * direction
                my = mark_y + random.randint(-1, 1)
                if 0 <= mx < width and 0 <= my < height:
                    current = img.getpixel((mx, my))
                    img.putpixel((mx, my), min(60, current + 8))

    elif scene_type == "underground_room":
        # Very dark underground room - almost nothing visible
        # Faint concrete walls at edges
        for y in range(height):
            for x in range(width):
                # Base: nearly black
                val = 5 + random.randint(-2, 2)
                # Slight wall visibility at edges
                if x < 25:
                    val = 12 + random.randint(-3, 3)
                elif x > width - 25:
                    val = 11 + random.randint(-3, 3)
                if y < 15:
                    val = 10 + random.randint(-2, 2)
                img.putpixel((x, y), max(0, min(30, val)))

        # Floor slightly more visible (flash reflection)
        for y in range(height * 2 // 3, height):
            for x in range(25, width - 25):
                val = 8 + int((y - height * 2 // 3) * 0.1) + random.randint(-2, 2)
                img.putpixel((x, y), max(3, min(20, val)))

        # Circular marks on floor
        cx, cy = width // 2, height * 3 // 4
        for r in range(30, 90, 3):
            for angle in range(0, 360, 1):
                rad = math.radians(angle)
                px = int(cx + r * math.cos(rad))
                py = int(cy + int(r * 0.4 * math.sin(rad)))
                if 0 <= px < width and 0 <= py < height:
                    current = img.getpixel((px, py))
                    img.putpixel((px, py), min(15, current + 3))

        # Kneeling figures (barely visible silhouettes)
        figure_positions = [
            (width//2 - 60, height//2 + 10),
            (width//2 - 30, height//2 - 20),
            (width//2 + 30, height//2 - 20),
            (width//2 + 60, height//2 + 10),
            (width//2, height//2 - 40),
        ]
        for fx, fy in figure_positions:
            # Head
            draw.ellipse([fx-5, fy-12, fx+5, fy], fill=16)
            # Body
            draw.rectangle([fx-6, fy, fx+6, fy+20], fill=14)
            # Arms extended forward
            draw.line([(fx+6, fy+5), (fx+18, fy+12)], fill=13, width=2)
            draw.line([(fx-6, fy+5), (fx-18, fy+12)], fill=13, width=2)

        # Dark mass in center
        draw.ellipse([cx-25, cy-15, cx+25, cy+15], fill=2)

        # Camera flash hotspot
        for radius in range(40):
            brightness = max(0, int(12 * math.exp(-radius / 15.0)))
            for angle in range(0, 360, 5):
                rad = math.radians(angle)
                px = int(width // 3 + radius * math.cos(rad))
                py = int(30 + radius * math.sin(rad))
                if 0 <= px < width and 0 <= py < height:
                    current = img.getpixel((px, py))
                    img.putpixel((px, py), min(60, current + brightness))

    elif scene_type == "stairwell":
        # Stairwell with fresh concrete filling
        for y in range(height):
            for x in range(width):
                val = 40 + random.randint(-5, 5)
                img.putpixel((x, y), val)

        # Walls (darker sides)
        wall_w = width // 5
        for y in range(height):
            for x in range(wall_w):
                val = 50 + random.randint(-5, 5)
                img.putpixel((x, y), val)
            for x in range(width - wall_w, width):
                val = 48 + random.randint(-5, 5)
                img.putpixel((x, y), val)

        # Concrete fill (lighter, smooth, in center)
        concrete_left = wall_w + 10
        concrete_right = width - wall_w - 10
        concrete_top = height // 4
        for y in range(concrete_top, height):
            for x in range(concrete_left, concrete_right):
                val = 130 + random.randint(-8, 8)
                # Subtle texture variation
                if random.random() < 0.05:
                    val += random.randint(-20, 20)
                img.putpixel((x, y), max(80, min(180, val)))

        # Steps visible above concrete (darker lines)
        for i in range(6):
            step_y = concrete_top - 10 + i * 8
            if 0 <= step_y < height:
                draw.line([(concrete_left, step_y), (concrete_right, step_y)], fill=35, width=2)
                for x in range(concrete_left, concrete_right):
                    if 0 <= step_y + 1 < height:
                        img.putpixel((x, step_y + 1), random.randint(30, 45))

        # Dark stairwell above (where stairs go up)
        for y in range(concrete_top - 40):
            for x in range(concrete_left, concrete_right):
                val = 25 + random.randint(-5, 5)
                img.putpixel((x, y), val)

        # Two figures
        # Figure 1 (left, facing away)
        f1x = wall_w // 2 + 20
        f1y = height // 2
        draw.ellipse([f1x-8, f1y-20, f1x+8, f1y-4], fill=70)
        draw.rectangle([f1x-10, f1y-4, f1x+10, f1y+35], fill=65)
        draw.rectangle([f1x-10, f1y+35, f1x+10, f1y+55], fill=60)

        # Figure 2 (right, facing camera)
        f2x = width - wall_w // 2 - 20
        f2y = height // 2 - 10
        draw.ellipse([f2x-9, f2y-22, f2x+9, f2y-4], fill=80)
        draw.rectangle([f2x-11, f2y-4, f2x+11, f2y+35], fill=75)
        draw.rectangle([f2x-11, f2y+35, f2x+11, f2y+55], fill=70)
        # Eyes (small bright dots staring at camera)
        draw.point([(f2x-3, f2y-14), (f2x+3, f2y-14)], fill=110)
        # Mouth line (tight, grim)
        draw.line([(f2x-3, f2y-9), (f2x+3, f2y-9)], fill=55, width=1)

        # Flash reflection on wet concrete
        flash_cx = (concrete_left + concrete_right) // 2
        flash_cy = height * 2 // 3
        for radius in range(60):
            brightness = max(0, int(50 * math.exp(-radius / 25.0)))
            for angle in range(0, 360, 3):
                rad = math.radians(angle)
                px = int(flash_cx + radius * math.cos(rad))
                py = int(flash_cy + radius * math.sin(rad) * 0.5)
                if concrete_left <= px < concrete_right and concrete_top <= py < height:
                    current = img.getpixel((px, py))
                    img.putpixel((px, py), min(220, current + brightness))

    elif scene_type == "crack":
        # Camcorder nightshot of cracked concrete
        # Green-tinted, interlaced, very grainy

        # Concrete surface from above
        for y in range(height):
            for x in range(width):
                val = 30 + random.randint(-8, 8)
                img.putpixel((x, y), max(10, min(60, val)))

        # Flashlight cone from top center
        cone_cx = width // 2
        for y in range(height):
            cone_width = 30 + y * width // (height * 3)
            for x in range(width):
                dx = abs(x - cone_cx)
                if dx < cone_width:
                    brightness = int(30 * (1 - dx / cone_width) * (1 - y / height * 0.3))
                    current = img.getpixel((x, y))
                    img.putpixel((x, y), min(80, current + brightness))

        # THE CRACK - jagged, dark, going down the center
        crack_x = width // 2
        crack_points = []
        for y in range(15, height - 15):
            crack_x += random.randint(-2, 2)
            crack_x = max(width // 3, min(2 * width // 3, crack_x))
            crack_points.append((crack_x, y))

            # Main crack width varies
            w_var = random.randint(2, 6)
            for dx in range(-w_var, w_var + 1):
                px = crack_x + dx
                if 0 <= px < width:
                    # Darker toward center of crack
                    darkness = max(0, 3 - abs(dx))
                    img.putpixel((px, y), darkness)

        # Branch cracks
        for _ in range(6):
            start_idx = random.randint(0, len(crack_points) - 1)
            sx, sy = crack_points[start_idx]
            angle = random.uniform(-1.2, 1.2)
            length = random.randint(15, 50)
            for i in range(length):
                bx = int(sx + i * math.cos(angle))
                by = int(sy + i * math.sin(angle))
                if 0 <= bx < width and 0 <= by < height:
                    w_var = max(1, 3 - i // 15)
                    for dx in range(-w_var, w_var + 1):
                        px = bx + dx
                        if 0 <= px < width:
                            img.putpixel((px, by), random.randint(1, 5))

        # Two faint points of reflected light deep in crack (eyes?)
        eye_y = height // 2 + 10
        eye_x = width // 2
        img.putpixel((eye_x - 2, eye_y), 50)
        img.putpixel((eye_x + 3, eye_y + 1), 47)
        # Slight glow around them
        for ey_offset in [(-2, eye_y), (3, eye_y + 1)]:
            for r in range(1, 4):
                for a in range(0, 360, 30):
                    rad = math.radians(a)
                    epx = int(eye_x + ey_offset[0] + r * math.cos(rad))
                    epy = int(ey_offset[1] + r * math.sin(rad))
                    if 0 <= epx < width and 0 <= epy < height:
                        current = img.getpixel((epx, epy))
                        img.putpixel((epx, epy), min(30, current + 5))

    elif scene_type == "boiler":
        # Boiler room with flash, two men, dark doorway

        # Base room illuminated by flash
        for y in range(height):
            for x in range(width):
                val = 35 + random.randint(-5, 5)
                img.putpixel((x, y), val)

        # Flash radial falloff from camera position (bottom center)
        flash_x, flash_y = width // 2, height
        for y in range(height):
            for x in range(width):
                dist = math.sqrt((x - flash_x)**2 + (y - flash_y)**2)
                brightness = max(0, int(60 * math.exp(-dist / (height * 0.6))))
                current = img.getpixel((x, y))
                img.putpixel((x, y), min(140, current + brightness))

        # Boiler (large cylinder, left side)
        boiler_cx = width // 4
        boiler_top = height // 4
        boiler_bottom = height * 3 // 4
        boiler_w = width // 5
        draw.ellipse([boiler_cx - boiler_w, boiler_top,
                      boiler_cx + boiler_w, boiler_bottom], fill=75, outline=55)

        # Pipes from boiler going right
        for py_offset in range(-30, 30, 15):
            py = (boiler_top + boiler_bottom) // 2 + py_offset
            draw.line([(boiler_cx + boiler_w, py), (width - 50, py - 10)], fill=80, width=4)

        # Figure 1 - Earl Whitmore (center-left, facing camera, smiling)
        f1x = width * 2 // 5
        f1y = height // 2
        draw.ellipse([f1x-10, f1y-22, f1x+10, f1y-2], fill=100)
        draw.rectangle([f1x-12, f1y-2, f1x+12, f1y+40], fill=90)
        draw.rectangle([f1x-12, f1y+40, f1x+12, f1y+65], fill=85)
        # Face features
        draw.point([(f1x-4, f1y-14), (f1x+4, f1y-14)], fill=50)
        draw.arc([f1x-4, f1y-10, f1x+4, f1y-6], 0, 180, fill=60, width=1)

        # Figure 2 - unidentified (right, near doorway)
        f2x = width * 3 // 4
        f2y = height // 2 - 5
        draw.ellipse([f2x-9, f2y-20, f2x+9, f2y-2], fill=80)
        draw.rectangle([f2x-10, f2y-2, f2x+10, f2y+35], fill=75)
        draw.rectangle([f2x-10, f2y+35, f2x+10, f2y+55], fill=70)

        # Dark doorway behind figure 2
        door_left = width - width // 5
        door_top = height // 5
        door_bottom = height * 3 // 4
        draw.rectangle([door_left, door_top, width - 10, door_bottom], fill=8)

        # THIRD FIGURE in doorway - barely visible
        f3x = door_left + (width - 10 - door_left) // 2
        f3y = (door_top + door_bottom) // 2
        # Just slightly lighter than the pure black doorway
        draw.ellipse([f3x-6, f3y-15, f3x+6, f3y], fill=12)
        draw.rectangle([f3x-7, f3y, f3x+7, f3y+30], fill=11)

    elif scene_type == "document":
        # Scanned handwritten document on aged paper
        # Lighter base - aged paper
        for y in range(height):
            for x in range(width):
                val = 195 + random.randint(-6, 6)
                # Natural paper color variation
                val += int(10 * math.sin(x * 0.02) * math.cos(y * 0.015))
                img.putpixel((x, y), max(160, min(225, val)))

        # Handwriting simulation - wavy lines of varying darkness
        lines_data = [
            (40, 60, "February 7, 1943", True),
            (40, 100, "They sealed the sub-level entrance", False),
            (40, 120, "today. Poured concrete over the", False),
            (40, 140, "stairwell. The men from the city", False),
            (40, 160, "supervised. They brought a new door", False),
            (40, 180, "for the B2 corridor - steel, with a", False),
            (40, 200, "lock I do not have a key for.", False),
            (40, 240, "When I asked why, the foreman told", False),
            (40, 260, "me it was for 'structural reasons.'", False),
            (40, 280, "Structural reasons do not require", False),
            (40, 300, "armed men standing watch while you", False),
            (40, 320, "pour concrete.", False),
            (40, 360, "I am putting in my resignation on", False),
            (40, 380, "Monday. I have been head janitor at", False),
            (40, 400, "this school for eleven years and I", False),
            (40, 420, "have never once been afraid to walk", False),
            (40, 440, "the halls at night until now.", False),
            (40, 480, "Whatever they found under this", False),
            (40, 500, "building, they should have left it", False),
            (40, 520, "alone. Some things are in the ground", False),
            (40, 540, "for a reason.", False),
            (300, 590, "- E. Whitmore", True),
        ]

        for lx, ly, text, bold in lines_data:
            char_width = 6 if not bold else 7
            for i, char in enumerate(text):
                if char == ' ':
                    continue
                cx = lx + i * char_width
                cy = ly + int(2 * math.sin(cx * 0.05 + ly * 0.03))  # Wavy baseline

                if cx >= width - 30:
                    break

                # Each "character" is a small cluster of dark pixels
                ink_val = random.randint(25, 50) if not bold else random.randint(15, 35)
                char_h = random.randint(6, 10)
                char_w = random.randint(3, 5)

                for dy in range(char_h):
                    for dx in range(char_w):
                        if random.random() > 0.25:  # Imperfect ink coverage
                            px = cx + dx
                            py = cy + dy
                            if 0 <= px < width and 0 <= py < height:
                                img.putpixel((px, py), ink_val + random.randint(-5, 10))

                # Descenders/ascenders for some chars
                if char in 'gjpqy':
                    for dy in range(char_h, char_h + 4):
                        px = cx + char_w // 2
                        py = cy + dy
                        if 0 <= py < height:
                            img.putpixel((px, py), ink_val + 5)
                elif char in 'bdfhklt':
                    for dy in range(-3, 0):
                        px = cx + char_w // 2
                        py = cy + dy
                        if 0 <= py < height:
                            img.putpixel((px, py), ink_val + 5)

    elif scene_type == "p7_disturbing":
        # The horrifying photograph - dark room, flash, the thing on the floor

        # Very dark room
        for y in range(height):
            for x in range(width):
                val = 5 + random.randint(-2, 2)
                img.putpixel((x, y), val)

        # Flash reflection on walls (brief, harsh)
        for y in range(height):
            for x in range(20):
                img.putpixel((x, y), random.randint(15, 25))
            for x in range(width - 20, width):
                img.putpixel((x, y), random.randint(14, 24))
        for x in range(width):
            for y in range(15):
                img.putpixel((x, y), random.randint(12, 22))

        # Wet floor reflecting flash
        for y in range(height * 2 // 3, height):
            for x in range(20, width - 20):
                val = 8 + int((y - height * 2 // 3) * 0.08) + random.randint(-2, 2)
                img.putpixel((x, y), max(5, min(20, val)))

        # THE FIGURE on the floor
        # Curled/fetal position, center of frame
        body_cx = width // 2
        body_cy = height // 2 + 20

        # Torso (elongated, too long, curving)
        for i in range(100):
            t = i / 100.0
            bx = int(body_cx - 40 + 80 * t)
            by = int(body_cy + 15 * math.sin(t * math.pi * 0.8))
            for dy in range(-12, 12):
                for dx in range(-4, 4):
                    px = bx + dx
                    py = by + dy
                    if 0 <= px < width and 0 <= py < height:
                        dist = math.sqrt(dx**2 + dy**2)
                        brightness = max(0, int(30 * math.exp(-dist / 8.0)))
                        current = img.getpixel((px, py))
                        img.putpixel((px, py), max(current, brightness))

        # Head (with hair - lighter streaks)
        head_x = body_cx - 50
        head_y = body_cy - 5
        draw.ellipse([head_x - 12, head_y - 14, head_x + 12, head_y + 10], fill=28)
        # Hair (lighter streaks)
        for i in range(12):
            hx = head_x + random.randint(-14, 14)
            hy = head_y - 14
            for j in range(random.randint(8, 18)):
                px = hx + random.randint(-1, 1)
                py = hy - j
                if 0 <= px < width and 0 <= py < height:
                    img.putpixel((px, py), random.randint(40, 55))

        # Face (partially visible - eyes, too-wide mouth)
        # Eyes - two bright pinpoints
        draw.point([(head_x - 4, head_y - 3)], fill=65)
        draw.point([(head_x + 4, head_y - 2)], fill=60)
        # Glint in eyes
        for eye_pos in [(head_x - 4, head_y - 3), (head_x + 4, head_y - 2)]:
            for r in range(1, 3):
                for a in range(0, 360, 45):
                    rad = math.radians(a)
                    epx = int(eye_pos[0] + r * math.cos(rad))
                    epy = int(eye_pos[1] + r * math.sin(rad))
                    if 0 <= epx < width and 0 <= epy < height:
                        img.putpixel((epx, epy), random.randint(25, 35))

        # Mouth - too wide, teeth visible
        mouth_y = head_y + 5
        for mx in range(head_x - 10, head_x + 10):
            if 0 <= mx < width and 0 <= mouth_y < height:
                img.putpixel((mx, mouth_y), 10)
                # Teeth (tiny bright spots in mouth)
                if random.random() > 0.4:
                    img.putpixel((mx, mouth_y + 1), random.randint(35, 50))

        # Arms with too many joints
        arm_points = [
            (body_cx + 40, body_cy - 5),
            (body_cx + 55, body_cy - 18),
            (body_cx + 50, body_cy - 30),
            (body_cx + 62, body_cy - 38),
            (body_cx + 58, body_cy - 48),
            (body_cx + 68, body_cy - 52),
        ]
        for i in range(len(arm_points) - 1):
            x1, y1 = arm_points[i]
            x2, y2 = arm_points[i + 1]
            draw.line([(x1, y1), (x2, y2)], fill=25, width=3)
            # Joint bump
            draw.ellipse([x2-3, y2-3, x2+3, y2+3], fill=28)

        # Fingers (too many, at end of arm)
        last_x, last_y = arm_points[-1]
        for f in range(7):
            angle = math.radians(-100 + f * 25)
            fx = int(last_x + 12 * math.cos(angle))
            fy = int(last_y + 12 * math.sin(angle))
            draw.line([(last_x, last_y), (fx, fy)], fill=22, width=2)

        # Legs folded backward
        draw.line([(body_cx - 20, body_cy + 10), (body_cx - 30, body_cy + 30),
                   (body_cx - 20, body_cy + 45), (body_cx - 35, body_cy + 55)], fill=24, width=3)

        # Skin splits/seams on torso (thin bright lines)
        for _ in range(4):
            sx = random.randint(body_cx - 30, body_cx + 30)
            sy = random.randint(body_cy - 10, body_cy + 10)
            length = random.randint(8, 20)
            angle = random.uniform(-0.3, 0.3)
            for i in range(length):
                px = int(sx + i * math.cos(angle))
                py = int(sy + i * math.sin(angle))
                if 0 <= px < width and 0 <= py < height:
                    img.putpixel((px, py), random.randint(35, 50))

        # Flash hotspot
        for radius in range(50):
            brightness = max(0, int(20 * math.exp(-radius / 20.0)))
            for angle in range(0, 360, 5):
                rad = math.radians(angle)
                px = int(body_cx + radius * math.cos(rad))
                py = int(body_cy + radius * math.sin(rad))
                if 0 <= px < width and 0 <= py < height:
                    current = img.getpixel((px, py))
                    img.putpixel((px, py), min(55, current + brightness))

        # Data corruption (horizontal line shifts)
        for _ in range(12):
            y = random.randint(0, height - 1)
            shift = random.randint(-15, 15)
            row = [img.getpixel((x, y)) for x in range(width)]
            for x in range(width):
                src_x = (x + shift) % width
                img.putpixel((x, y), row[src_x])

        # Corruption blocks
        for _ in range(4):
            bx = random.randint(0, width - 40)
            by = random.randint(0, height - 6)
            bw = random.randint(20, 40)
            bh = random.randint(2, 5)
            val = random.randint(0, 15)
            draw.rectangle([bx, by, bx + bw, by + bh], fill=val)

    return img


# ============================================================
# Generate all images with realistic processing
# ============================================================
def process_and_save(img, filename, mode="photo", jpeg_quality=25):
    """Apply final processing pipeline and save"""

    if mode == "photo":
        img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
        img = film_grain(img, 20)
        img = vignette(img, 0.5)
        img = age_damage(img, stains=2, foxing=10)
        img_rgb = sepia_tone(img)
        img_rgb = scanner_artifacts(img_rgb)
        img_rgb = jpeg_degrade(img_rgb, jpeg_quality)

    elif mode == "dark_photo":
        img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
        img = film_grain(img, 30)
        img = vignette(img, 0.7)
        img = age_damage(img, stains=1, foxing=5)
        img_rgb = sepia_tone(img)
        img_rgb = scanner_artifacts(img_rgb)
        img_rgb = jpeg_degrade(img_rgb, max(10, jpeg_quality - 5))

    elif mode == "very_dark":
        img = img.filter(ImageFilter.GaussianBlur(radius=1.0))
        img = film_grain(img, 35)
        img = vignette(img, 0.85)
        img_rgb = sepia_tone(img)
        img_rgb = jpeg_degrade(img_rgb, max(8, jpeg_quality - 10))

    elif mode == "document":
        img = img.filter(ImageFilter.GaussianBlur(radius=0.3))
        img = film_grain(img, 8)
        img = age_damage(img, stains=3, foxing=15)
        img_rgb = sepia_tone(img)
        img_rgb = scanner_artifacts(img_rgb)
        img_rgb = jpeg_degrade(img_rgb, 35)

    elif mode == "camcorder":
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        img = film_grain(img, 45)
        # Green nightshot tint
        img_rgb = img.convert('RGB')
        r, g, b = img_rgb.split()
        from PIL import ImageEnhance
        # Darken red and blue, boost green
        result = Image.new('RGB', img.size)
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                rv, gv, bv = img_rgb.getpixel((x, y))
                result.putpixel((x, y), (max(0, rv - 15), min(255, gv + 10), max(0, bv - 20)))
        img_rgb = result
        # Interlacing
        for y in range(0, img.size[1], 2):
            for x in range(img.size[0] - 1, 0, -1):
                img_rgb.putpixel((x, y), img_rgb.getpixel((max(0, x - 1), y)))

        # REC indicator and timestamp overlay
        draw_rgb = ImageDraw.Draw(img_rgb)
        draw_rgb.rectangle([5, img.size[1] - 18, 95, img.size[1] - 5], fill=(20, 20, 20))
        draw_rgb.rectangle([img.size[0] - 50, 5, img.size[0] - 5, 18], fill=(40, 8, 8))

        img_rgb = jpeg_degrade(img_rgb, 15)

    elif mode == "corrupted":
        img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
        img = film_grain(img, 40)
        img = vignette(img, 0.9)
        # Sickly color cast
        img_rgb = img.convert('RGB')
        result = Image.new('RGB', img.size)
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                rv, gv, bv = img_rgb.getpixel((x, y))
                result.putpixel((x, y), (min(255, rv + 5), max(0, gv - 3), max(0, bv - 5)))
        img_rgb = result
        img_rgb = jpeg_degrade(img_rgb, 8)

    img_rgb.save(os.path.join(OUTPUT_DIR, filename), "JPEG", quality=jpeg_quality)
    print(f"Generated {filename} ({img_rgb.size[0]}x{img_rgb.size[1]})")


if __name__ == "__main__":
    random.seed(19971114)

    print("Generating realistic degraded photographs...\n")

    # Photo 1: School exterior
    img = make_dark_photo(468, 350, "exterior")
    process_and_save(img, "central_1915.jpg", "photo", 30)

    # Photo 2: Basement construction
    img = make_dark_photo(400, 300, "underground_room")
    # Make it slightly brighter for construction scene
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.5)
    process_and_save(img, "basement_1912.jpg", "dark_photo", 25)

    # Photo 3: Boiler room
    img = make_dark_photo(400, 300, "boiler")
    process_and_save(img, "boiler_1935.jpg", "photo", 28)

    # Photo 4: B2 Corridor
    img = make_dark_photo(400, 300, "corridor")
    process_and_save(img, "b2_corridor_1941.jpg", "dark_photo", 22)

    # Photo 5: Site C ritual room
    img = make_dark_photo(400, 300, "underground_room")
    process_and_save(img, "site_c_1942.jpg", "very_dark", 15)

    # Photo 6: Sealed stairwell
    img = make_dark_photo(400, 300, "stairwell")
    process_and_save(img, "sealed_stairwell_1943.jpg", "photo", 25)

    # Photo 7: THE disturbing one
    img = make_dark_photo(400, 300, "p7_disturbing")
    process_and_save(img, "p7.jpg", "corrupted", 10)

    # Document scan: Whitmore's log
    img = make_dark_photo(500, 650, "document")
    process_and_save(img, "whitmore_log.jpg", "document", 35)

    # Camcorder still: the crack
    img = make_dark_photo(320, 240, "crack")
    process_and_save(img, "crack.jpg", "camcorder", 18)

    print("\nAll images generated successfully.")
