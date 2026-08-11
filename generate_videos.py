from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 15
DURATION = 30
TOTAL_FRAMES = FPS * DURATION
OUT = Path("output")
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

CARS = [
    ("BMW M4", "Pearl White", (242, 244, 246)),
    ("Porsche 911 GT3", "Jet Black", (18, 19, 22)),
    ("Lamborghini Huracán", "Racing Red", (196, 18, 48)),
    ("Ferrari 488 Pista", "Electric Blue", (0, 92, 255)),
    ("McLaren 720S", "Matte Grey", (100, 103, 108)),
    ("Audi R8", "Metallic Silver", (180, 188, 196)),
    ("Mercedes-AMG GT", "Deep Emerald Green", (0, 96, 62)),
    ("Nissan GT-R", "Sunset Orange", (232, 93, 4)),
    ("Chevrolet Corvette C8", "Titanium Gold", (181, 139, 56)),
    ("Ford Mustang Shelby GT500", "Midnight Purple", (58, 32, 88)),
]

SHOTS = [
    "1 · Front Grille Upgrade",
    "2 · Hood Enhancement",
    "3 · Side Skirts & Handles",
    "4 · Performance Wheels",
    "5 · Brake Calipers",
    "6 · Exhaust Installation",
    "7 · Rear Wing Installation",
    "8 · Light Startup",
    "9 · Interior Touch-Up",
    "10 · Final Reveal",
]


def font(size, bold=False):
    path = FONT_PATHS[0] if bold else FONT_PATHS[-1]
    return ImageFont.truetype(path, size=size)


F_TITLE = font(68, True)
F_SUB = font(36)
F_SMALL = font(28)


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    return t * t * (3 - 2 * t)


def rounded_rect(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_hand(draw, cx, cy, scale=1.0, angle=0.0):
    # Stylized gloved hand pointing down-left, enough to read as "hands working" in motion.
    skin = (238, 195, 154)
    cuff = (235, 238, 242)
    w, h = int(120 * scale), int(150 * scale)
    # wrist/cuff
    rounded_rect(draw, [cx - w//2, cy - h//2 + 80, cx + w//2, cy + h//2 + 20], 24, cuff)
    # palm
    rounded_rect(draw, [cx - w//2 + 10, cy - h//2, cx + w//2 - 10, cy + h//2 - 20], 34, skin)
    # fingers
    for i in range(4):
        x = cx - w//2 + 20 + i * int(28 * scale)
        rounded_rect(draw, [x, cy - h//2 - int(36*scale), x + int(22*scale), cy - h//2 + int(46*scale)], 12, skin)
    # thumb
    rounded_rect(draw, [cx + w//2 - int(20*scale), cy - int(8*scale), cx + w//2 + int(52*scale), cy + int(44*scale)], 12, skin)


def draw_screwdriver(draw, x, y, t):
    draw.line([x - 180, y - 140, x, y], fill=(30, 32, 36), width=26)
    draw.line([x - 230, y - 180, x - 180, y - 140], fill=(198, 55, 60), width=34)
    rounded_rect(draw, [x - 18, y - 18, x + 18, y + 18], 8, (170, 176, 184))
    # small motion marks
    for i in range(3):
        off = int(t * 40 + i * 22) % 66
        draw.line([x + 30 + off, y - 34 + off//3, x + 52 + off, y - 22 + off//3], fill=(120, 126, 136), width=5)


def draw_wheel(draw, cx, cy, r, spin=0.0, lit=False):
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(10, 11, 13), outline=(190, 196, 204), width=8)
    draw.ellipse([cx-int(r*0.62), cy-int(r*0.62), cx+int(r*0.62), cy+int(r*0.62)], fill=(34, 36, 40))
    for i in range(10):
        a = spin + i * 3.14159 / 5
        x2 = cx + int(r * 0.58 * __import__("math").cos(a))
        y2 = cy + int(r * 0.58 * __import__("math").sin(a))
        draw.line([cx, cy, x2, y2], fill=(185, 191, 200), width=10)
    draw.ellipse([cx-30, cy-30, cx+30, cy+30], fill=(210, 215, 222))
    for i in range(5):
        a = spin * 0.5 + i * 1.256
        x2 = cx + int(r * 0.82 * __import__("math").cos(a))
        y2 = cy + int(r * 0.82 * __import__("math").sin(a))
        color = (64, 180, 255) if lit else (100, 104, 112)
        draw.ellipse([x2-12, y2-12, x2+12, y2+12], fill=color)


def draw_car_base(draw, color_rgb, highlight=0.0, show_wing=False, show_interior=False, x_offset=0, scale=1.0):
    cx, cy = W // 2 + x_offset, 940
    car_w, car_h = int(820 * scale), int(270 * scale)
    dark = tuple(max(10, int(c * 0.20)) for c in color_rgb)
    stripe_col = tuple(min(255, int(c * 0.75 + 60)) for c in color_rgb)
    outline_col = (24, 25, 29) if sum(color_rgb) > 330 else (210, 214, 220)
    # shadow
    draw.ellipse([cx - int(460*scale), cy + int(130*scale), cx + int(460*scale), cy + int(270*scale)], fill=(218, 222, 228))
    # cabin
    rounded_rect(draw, [cx - int(250*scale), cy - int(225*scale), cx + int(250*scale), cy - int(25*scale)], int(90*scale), dark)
    # main body
    body = [cx - car_w//2, cy - int(85*scale), cx + car_w//2, cy + int(120*scale)]
    rounded_rect(draw, body, int(115*scale), color_rgb, outline=outline_col, width=4)
    # hood definition lines
    draw.line([cx - int(300*scale), cy - int(45*scale), cx + int(300*scale), cy - int(45*scale)], fill=dark, width=4)
    draw.line([cx - int(340*scale), cy + int(25*scale), cx + int(340*scale), cy + int(25*scale)], fill=dark, width=3)
    # windshield/cabin glass
    rounded_rect(draw, [cx - int(205*scale), cy - int(205*scale), cx + int(205*scale), cy - int(45*scale)], int(70*scale), (42, 64, 84))
    draw.line([cx - int(180*scale), cy - int(180*scale), cx + int(180*scale), cy - int(180*scale)], fill=(175, 205, 230), width=5)
    # front & rear light bars
    rounded_rect(draw, [cx - int(405*scale), cy - int(5*scale), cx - int(325*scale), cy + int(45*scale)], int(20*scale), (250, 250, 250))
    rounded_rect(draw, [cx + int(325*scale), cy - int(5*scale), cx + int(405*scale), cy + int(45*scale)], int(20*scale), (255, 80, 70))
    # highlight stripe
    rounded_rect(draw, [cx - int(320*scale), cy - int(72*scale), cx + int(330*scale), cy - int(34*scale)], int(28*scale), stripe_col)
    # lower intake/diffuser
    rounded_rect(draw, [cx - int(120*scale), cy + int(52*scale), cx + int(150*scale), cy + int(98*scale)], int(20*scale), (14, 16, 20))
    # side skirt
    rounded_rect(draw, [cx - int(350*scale), cy + int(102*scale), cx + int(350*scale), cy + int(132*scale)], int(14*scale), (12, 14, 17))
    # door handles
    for dx in (-150, 150):
        rounded_rect(draw, [cx + int(dx*scale), cy - int(2*scale), cx + int((dx+82)*scale), cy + int(20*scale)], int(9*scale), (212, 218, 226))
    # wing
    if show_wing:
        draw.line([cx - int(255*scale), cy - int(275*scale), cx - int(255*scale), cy - int(200*scale)], fill=(24, 26, 30), width=int(18*scale))
        draw.line([cx + int(255*scale), cy - int(275*scale), cx + int(255*scale), cy - int(200*scale)], fill=(24, 26, 30), width=int(18*scale))
        rounded_rect(draw, [cx - int(340*scale), cy - int(330*scale), cx + int(340*scale), cy - int(272*scale)], int(30*scale), (12, 14, 17))
    # interior glimpses
    if show_interior:
        rounded_rect(draw, [cx - int(180*scale), cy - int(190*scale), cx + int(180*scale), cy - int(55*scale)], int(50*scale), (74, 44, 28))
        draw.ellipse([cx - int(90*scale), cy - int(165*scale), cx - int(5*scale), cy - int(80*scale)], outline=(210, 214, 220), width=int(10*scale))
        rounded_rect(draw, [cx + int(45*scale), cy - int(160*scale), cx + int(150*scale), cy - int(55*scale)], int(20*scale), (120, 64, 40))
    # wheels
    draw_wheel(draw, cx - int(270*scale), cy + int(115*scale), int(98*scale), lit=highlight > 0.45)
    draw_wheel(draw, cx + int(270*scale), cy + int(115*scale), int(98*scale), lit=highlight > 0.65)


def draw_shot_icons(draw, idx, color_rgb, t):
    cx, cy = W//2, 620
    # shot-specific component vignette over the car
    if idx == 0:  # grille
        rounded_rect(draw, [cx-210, cy+40, cx+210, cy+180], 35, (12, 13, 15))
        for x in range(cx-185, cx+190, 28):
            draw.line([x, cy+52, x, cy+168], fill=(58, 61, 68), width=5)
        glow = int(120 + 120*t)
        draw.ellipse([cx-42, cy+78, cx+42, cy+162], outline=(190, 200, 214), width=10)
        draw.ellipse([cx-20, cy+100, cx+20, cy+140], outline=(glow, glow, glow), width=6)
        draw_hand(draw, cx + 250 - int(30*t), cy + 40 - int(18*t), 0.82)
    elif idx == 1:  # hood vents
        for i in range(3):
            x = cx - 160 + i*160
            rounded_rect(draw, [x-55, cy+30, x+55, cy+150], 18, (10, 12, 14))
            for yy in range(cy+52, cy+145, 20):
                draw.line([x-40, yy, x+40, yy], fill=(80, 84, 92), width=4)
        draw_hand(draw, cx - 260 + int(80*t), cy + 70, 0.8)
    elif idx == 2:  # skirts & handles
        rounded_rect(draw, [cx-330, cy+135, cx+330, cy+175], 16, (10, 12, 14))
        for dx in (-120, 140):
            rounded_rect(draw, [cx+dx, cy-8, cx+dx+80, cy+20], 10, (225, 230, 238))
        draw_hand(draw, cx + 280, cy - 20 + int(26*t), 0.78)
    elif idx == 3:  # wheels
        draw_wheel(draw, cx - 160, cy + 80, 120, spin=t*8, lit=t > 0.5)
        draw_wheel(draw, cx + 170, cy + 80, 120, spin=-t*7, lit=t > 0.2)
        # polish cloth arc
        draw.arc([cx-245, cy-40, cx-75, cy+190], start=200, end=310, fill=(235, 238, 242), width=26)
        draw_hand(draw, cx - 260, cy - 40, 0.72)
    elif idx == 4:  # calipers
        draw_wheel(draw, cx - 150, cy + 80, 118, spin=t*2, lit=True)
        rounded_rect(draw, [cx - 230, cy + 25, cx - 90, cy + 135], 28, tuple(min(255, int(c*0.85+25)) for c in color_rgb))
        draw_screwdriver(draw, cx + 170, cy + 75, t)
        draw_hand(draw, cx + 310, cy - 10, 0.7)
    elif idx == 5:  # exhaust
        rounded_rect(draw, [cx-300, cy+120, cx+300, cy+185], 24, (12, 13, 15))
        for i in range(4):
            x = cx - 165 + i*110
            rounded_rect(draw, [x-38, cy+140, x+38, cy+168], 14, (150, 158, 170))
            rounded_rect(draw, [x+8, cy+144, x+38, cy+164], 10, (60, 140, 255))
        draw_hand(draw, cx + 250, cy + 30, 0.72)
    elif idx == 6:  # wing
        draw.line([cx-230, cy+20, cx-230, cy+120], fill=(20, 22, 26), width=18)
        draw.line([cx+230, cy+20, cx+230, cy+120], fill=(20, 22, 26), width=18)
        rounded_rect(draw, [cx-330, cy-40, cx+330, cy+18], 28, (12, 14, 17))
        draw_hand(draw, cx + 250, cy - 90, 0.74)
    elif idx == 7:  # lights
        # two light clusters + taillight strip
        rounded_rect(draw, [cx-330, cy+20, cx-120, cy+95], 32, (235, 245, 255))
        rounded_rect(draw, [cx+120, cy+20, cx+330, cy+95], 32, (255, 70, 62))
        for i in range(5):
            alpha = min(255, int((t*1.4 - i*0.15) * 255))
            if alpha > 0:
                x = cx - 300 + i * 38
                draw.ellipse([x-10, cy+45-10, x+10, cy+45+10], fill=(255, 255, 255))
        draw.line([cx+150, cy+58, cx+300, cy+58], fill=(255, 220, 220), width=8)
        draw_hand(draw, cx - 20, cy - 90 + int(45*t), 0.68)
    elif idx == 8:  # interior
        rounded_rect(draw, [cx-220, cy-40, cx+220, cy+170], 36, (72, 42, 26))
        draw.ellipse([cx-110, cy-5, cx-20, cy+85], outline=(225, 229, 236), width=10)
        rounded_rect(draw, [cx+35, cy+0, cx+155, cy+120], 22, (126, 68, 42))
        # leather wrap motion lines
        for i in range(4):
            draw.arc([cx-118+i*8, cy-10+i*6, cx-12-i*8, cy+92-i*6], 20, 220, fill=(214, 180, 142), width=5)
        draw_hand(draw, cx + 250, cy + 30, 0.72)
    elif idx == 9:  # reveal motion streaks
        for i in range(7):
            y = 1040 + i*34
            draw.line([70, y, 330 + i*28, y], fill=(222, 226, 232), width=6)
        rounded_rect(draw, [cx-290, 1240, cx+290, 1292], 25, (22, 24, 28))
        txt = "FULLY CUSTOMIZED"
        tw = draw.textlength(txt, font=F_SMALL)
        draw.text((cx - tw/2, 1250), txt, font=F_SMALL, fill=(235, 238, 242))


def draw_header(draw, title, subtitle, idx, t):
    # soft white studio panel
    rounded_rect(draw, [50, 60, W-50, 290], 42, (255, 255, 255))
    draw.text((90, 92), title, font=F_TITLE, fill=(16, 18, 22))
    draw.text((90, 178), subtitle, font=F_SUB, fill=(82, 88, 98))
    # progress pills
    x = 90
    for i in range(10):
        w = 72 if i == idx else 46
        fill = (24, 26, 30) if i == idx else (205, 210, 217)
        rounded_rect(draw, [x, 246, x + w, 264], 9, fill)
        x += w + 12


def make_frame(car, color_name, rgb, frame_idx, video_index):
    t = frame_idx / TOTAL_FRAMES
    shot = min(9, frame_idx // (FPS * 3))
    local = (frame_idx % (FPS * 3)) / (FPS * 3)
    p = smooth(local)
    img = Image.new("RGB", (W, H), (248, 249, 251))
    d = ImageDraw.Draw(img)
    for y in range(H):
        g = int(248 - 16 * (y / H))
        d.line([(0, y), (W, y)], fill=(g, g + 1, g + 4))
    # soft studio glow
    for r in range(680, 0, -34):
        shade = 250 - (r // 34)
        d.ellipse([W//2 - r, 680 - r//2, W//2 + r, 680 + r//2], outline=(shade, shade, min(255, shade + 2)))

    title = f"{car}"
    subtitle = f"{color_name} · Shot {shot+1}/10"
    draw_header(d, title, subtitle, shot, t)

    show_wing = shot >= 6
    show_interior = shot == 8
    highlight = 1.0 if shot in (3, 4, 5, 7, 9) else local
    x_offset = 0
    scale = 1.0
    if shot == 9:
        x_offset = int(lerp(-280, 120, p))
        scale = 1.0 + 0.08 * p
    draw_car_base(d, rgb, highlight=highlight, show_wing=show_wing, show_interior=show_interior, x_offset=x_offset, scale=scale)
    draw_shot_icons(d, shot, rgb, p)

    rounded_rect(d, [70, 1480, W-70, 1740], 36, (255, 255, 255))
    d.text((110, 1512), SHOTS[shot], font=F_SUB, fill=(18, 20, 24))
    desc = [
        "Chrome emblem snaps into black mesh grille.",
        "Carbon vents and scoops press flush into the hood.",
        "Side skirts clip on; chrome handles snap into place.",
        "Matte wheels polished; blue lug LEDs ignite.",
        "Color-matched calipers bolt in behind each wheel.",
        "Blue-tip titanium exhaust locks into carbon diffuser.",
        "GT wing tested, adjusted, and seated with a click.",
        "LED startup sweeps across headlights and taillights.",
        "Leather wrap and tailored covers go in fast.",
        "The finished build rolls across the white studio.",
    ][shot]
    d.text((110, 1570), desc, font=F_SMALL, fill=(88, 94, 104))

    cues = ["CLICK", "PRESS-CLICK", "SNAP", "SHHHK", "TURN-TURN", "CLACK", "THUNK", "CHIME", "FWIP", "HUM"]
    cue = cues[shot]
    tw = d.textlength(cue, font=F_SMALL)
    rounded_rect(d, [W-140-tw, 1660, W-100, 1712], 22, (24, 26, 30))
    d.text((W-120-tw, 1670), cue, font=F_SMALL, fill=(240, 243, 247))

    footer = f"VIRAL CAR ASSEMBLY · {video_index+1}/10 · 30 SEC"
    fw = d.textlength(footer, font=F_SMALL)
    d.text(((W-fw)/2, 1818), footer, font=F_SMALL, fill=(120, 126, 136))
    return img


def render_video(car, color_name, rgb, video_index):
    raw = OUT / f"{video_index+1:02d}_{car.replace(' ', '_').replace('-', '_')}_raw.mp4"
    final = OUT / f"{video_index+1:02d}_{car.replace(' ', '_').replace('-', '_')}_youtube_short.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "veryfast",
        str(raw)
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(TOTAL_FRAMES):
        frame = make_frame(car, color_name, rgb, i, video_index)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed for {car}")
    # Add a soft engine-hum-like tone bed and short tactile tick pulses.
    subprocess.run([
        "ffmpeg", "-y", "-i", str(raw),
        "-f", "lavfi", "-i", "sine=frequency=72:duration=30",
        "-f", "lavfi", "-i", "sine=frequency=1100:duration=0.06",
        "-filter_complex", "[1:a]volume=0.045[hum];[2:a]volume=0.0[tick];[hum][tick]amix=inputs=2[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", str(final)
    ], check=True)
    raw.unlink(missing_ok=True)
    return final


def main():
    OUT.mkdir(exist_ok=True)
    made = []
    for i, (car, color_name, rgb) in enumerate(CARS):
        print(f"Rendering {i+1}/10: {car} ({color_name})")
        made.append(render_video(car, color_name, rgb, i))
    print("Done:")
    for p in made:
        print(p)

if __name__ == "__main__":
    main()
