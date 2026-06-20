"""
Aeolian Cartography — Plate I.
A boy who holds the wind, rendered as a field study.
Refined second pass.
"""
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

random.seed(11)
np.random.seed(11)

# ---------------------------------------------------------------- canvas
W, H = 1800, 2400
img = Image.new("RGB", (W, H), (8, 12, 24))

# ---------------------------------------------------------------- palette
INDIGO_DEEP = (8, 12, 24)
INDIGO_MID  = (14, 22, 42)
CYAN_PALE   = (176, 212, 234)
CYAN_MIST   = (120, 168, 205)
CYAN_DEEP   = (70, 110, 150)
BONE        = (236, 236, 228)
AMBER       = (226, 170, 92)
AMBER_GLOW  = (246, 204, 124)
AMBER_DEEP  = (180, 120, 56)

# ---------------------------------------------------------------- background
bg = np.zeros((H, W, 3), dtype=np.float32)
top = np.array(INDIGO_DEEP, dtype=np.float32)
mid = np.array(INDIGO_MID, dtype=np.float32)
bot = np.array((5, 8, 16), dtype=np.float32)
for y in range(H):
    t = y / (H - 1)
    if t < 0.5:
        k = t / 0.5
        c = top * (1 - k) + mid * k
    else:
        k = (t - 0.5) / 0.5
        c = mid * (1 - k) + bot * k
    bg[y, :] = c
cy, cx = H * 0.50, W * 0.5
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
rmax = math.hypot(W * 0.5, H * 0.5)
glow = np.clip(1.0 - (r / rmax) ** 1.6, 0, 1) * 16
bg[:, :, 0] += glow
bg[:, :, 1] += glow * 1.1
bg[:, :, 2] += glow * 1.3
bg = np.clip(bg, 0, 255).astype(np.uint8)
img = Image.fromarray(bg, "RGB")
draw = ImageDraw.Draw(img, "RGBA")

# ---------------------------------------------------------------- wind field
fx, fy = W * 0.5, H * 0.505
R = 215.0

def field(x, y):
    u0, v0 = 1.0, -0.10
    dx, dy = x - fx, y - fy
    r2 = dx * dx + dy * dy + 1e-3
    r4 = r2 * r2
    du = -R * R * (dx * dx - dy * dy) / r4
    dv = -R * R * (2.0 * dx * dy) / r4
    sx, sy = fx + 380, fy - 30
    sdx, sdy = x - sx, y - sy
    sr2 = sdx * sdx + sdy * sdy + 220.0
    strength = 2800.0
    su = -strength * sdx / sr2
    sv = -strength * sdy / sr2
    return u0 + du + su * 0.32, v0 + dv + sv * 0.32

def in_body(x, y, pad=0.0):
    dx, dy = x - fx, y - fy
    ex = (dx) / (R * 0.60 + pad)
    ey = (dy + 24) / (R * 1.16 + pad)
    return ex * ex + ey * ey < 1.0

def trace(x0, y0, steps=640, ds=5.0):
    pts = [(x0, y0)]
    x, y = x0, y0
    for _ in range(steps):
        u, v = field(x, y)
        sp = math.hypot(u, v)
        if sp < 1e-4:
            break
        x += ds * u / sp
        y += ds * v / sp
        if not (0 <= x < W and 0 <= y < H):
            break
        if in_body(x, y, pad=-8.0):
            break
        pts.append((x, y))
    return pts

# ---------------------------------------------------------------- streamline passes
# Pass A — deep background, faint, dense
seedsA = []
for y in range(110, H - 110, 9):
    seedsA.append((70.0, float(y)))
for (sx, sy) in seedsA:
    pts = trace(sx, sy)
    if len(pts) < 6:
        continue
    draw.line(pts, fill=(*CYAN_DEEP, 26), width=1, joint="curve")

# Pass B — mid layer, primary streamlines
seedsB = []
for y in range(120, H - 120, 16):
    seedsB.append((85.0, float(y)))
# extra seeds that will visibly part around the body (near body height)
for k in range(-9, 10):
    seedsB.append((90.0, fy + k * 18))
for (sx, sy) in seedsB:
    pts = trace(sx, sy)
    if len(pts) < 6:
        continue
    t = (sy - 120) / (H - 240)
    alpha = int(40 + 80 * (0.45 + 0.55 * (1 - abs(t - 0.5) * 1.5)))
    alpha = max(24, min(135, alpha))
    width = 1 if random.random() < 0.82 else 2
    col = CYAN_PALE if random.random() < 0.72 else CYAN_MIST
    draw.line(pts, fill=(*col, alpha), width=width, joint="curve")

# Pass C — bright foreground accents (fewer, brighter)
for _ in range(70):
    sy = random.uniform(180, H - 180)
    pts = trace(80.0, sy)
    if len(pts) < 8:
        continue
    draw.line(pts, fill=(*BONE, random.randint(90, 150)), width=1, joint="curve")

# ---------------------------------------------------------------- isobar rings (scientific layer)
for k, (rr, a) in enumerate([(R * 1.35, 40), (R * 1.75, 30), (R * 2.25, 22), (R * 2.85, 16)]):
    bbox = [fx - rr, fy - rr * 1.16 - 24, fx + rr, fy + rr * 1.16 - 24]
    draw.ellipse(bbox, outline=(*CYAN_MIST, a), width=1)

# ---------------------------------------------------------------- particles
for _ in range(620):
    x = random.uniform(70, W - 70)
    y = random.uniform(110, H - 110)
    if in_body(x, y, pad=18):
        continue
    u, v = field(x, y)
    sp = math.hypot(u, v) + 1e-3
    ln = random.uniform(2, 8)
    ex = x + ln * u / sp
    ey = y + ln * v / sp
    a = random.randint(35, 105)
    col = BONE if random.random() < 0.28 else CYAN_PALE
    draw.line([(x, y), (ex, ey)], fill=(*col, a), width=1)

# bright compression dust near figure
for _ in range(300):
    ang = random.uniform(0, 2 * math.pi)
    rr = random.uniform(R * 0.72, R * 1.55)
    x = fx + math.cos(ang) * rr
    y = fy + math.sin(ang) * rr * 1.12
    if in_body(x, y):
        continue
    if not (60 < x < W - 60 and 60 < y < H - 60):
        continue
    s = random.choice([1, 1, 1, 2])
    draw.ellipse([x - s, y - s, x + s, y + s],
                 fill=(*BONE, random.randint(70, 150)))

# ---------------------------------------------------------------- warm halo (held breath)
halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
hd = ImageDraw.Draw(halo)
for rr, a in [(300, 8), (240, 14), (180, 22), (130, 34), (90, 52), (60, 70)]:
    hd.ellipse([fx - rr, fy - rr * 1.12, fx + rr, fy + rr * 1.12],
               fill=(246, 204, 124, a))
halo = halo.filter(ImageFilter.GaussianBlur(34))
img = Image.alpha_composite(img.convert("RGBA"), halo).convert("RGB")
draw = ImageDraw.Draw(img, "RGBA")

# ---------------------------------------------------------------- the boy
def F(dx, dy):
    return (fx + dx, fy + dy)

head_r = 30
hx, hy = 0, -165  # head center

# soft inner glow on figure lines: draw a blurred wider amber underlay
fig_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
fg = ImageDraw.Draw(fig_glow)

def fg_line(pts, w=3, a=70):
    fg.line(pts, fill=(246, 204, 124, a), width=w, joint="curve")

# head glow
fg.ellipse([F(hx - head_r, hy - head_r)[0], F(hx - head_r, hy - head_r)[1],
            F(hx + head_r, hy + head_r)[0], F(hx + head_r, hy + head_r)[1]],
           outline=(246, 204, 124, 90), width=4)

# torso sides
def torso_side(side):
    pts = []
    top_y = hy + head_r + 14
    for i in range(26):
        t = i / 25
        y = top_y + t * 128
        w = 20 * (1 - 0.4 * math.sin(t * math.pi)) + 3
        x = side * w
        pts.append(F(x, y))
    return pts

left = torso_side(-1)
right = torso_side(1)
fg_line(left); fg_line(right)
fg_line([left[0], right[0]])
fg_line([left[-1], right[-1]])

# arms
def arm(raised):
    pts = []
    sx, sy = 0, hy + head_r + 20
    if raised:
        ex, ey = -82, -228
        cx, cy = -70, -130
    else:
        ex, ey = 92, 26
        cx, cy = 62, -14
    for i in range(22):
        t = i / 21
        x = (1 - t) ** 2 * sx + 2 * (1 - t) * t * cx + t * t * ex
        y = (1 - t) ** 2 * sy + 2 * (1 - t) * t * cy + t * t * ey
        pts.append(F(x, y))
    return pts

raised_arm = arm(True)
lower_arm = arm(False)
fg_line(raised_arm); fg_line(lower_arm)

# legs
def leg(side, stride=0):
    pts = []
    top_y = hy + head_r + 14 + 128
    for i in range(24):
        t = i / 23
        y = top_y + t * 158
        w = 10 * (1 - 0.28 * t)
        x = side * (w + stride * t)
        pts.append(F(x, y))
    return pts

fg_line(leg(-1, stride=-9))
fg_line(leg(1, stride=9))

# scarf flowing into wind
scarf_pts = []
sx, sy = 12, hy + head_r + 22
for i in range(70):
    t = i / 69
    x = sx + t * 560 + 34 * math.sin(t * 6)
    y = sy + t * 36 + 64 * math.sin(t * 5 + 1.2)
    scarf_pts.append(F(x, y))
fg_line(scarf_pts, w=3, a=80)
scarf_pts2 = []
for i in range(70):
    t = i / 69
    x = sx + t * 580 + 26 * math.sin(t * 6 + 0.6)
    y = sy + 12 + t * 26 + 52 * math.sin(t * 5 + 1.8)
    scarf_pts2.append(F(x, y))
fg_line(scarf_pts2, w=2, a=50)

# hair strands
for k in range(6):
    pts = []
    sx0 = -12 + k * 5
    sy0 = hy - head_r + 8
    for i in range(30):
        t = i / 29
        x = sx0 + t * (96 + k * 14) + 10 * math.sin(t * 5 + k)
        y = sy0 + t * (32 + k * 4) + 8 * math.sin(t * 4 + k * 0.7)
        pts.append(F(x, y))
    fg_line(pts, w=2, a=60)

fig_glow = fig_glow.filter(ImageFilter.GaussianBlur(6))
img = Image.alpha_composite(img.convert("RGBA"), fig_glow).convert("RGB")
draw = ImageDraw.Draw(img, "RGBA")

# crisp figure lines on top
def fig_line(pts, w=2, a=235, col=AMBER_GLOW):
    draw.line(pts, fill=(*col, a), width=w, joint="curve")

draw.ellipse([F(hx - head_r, hy - head_r)[0], F(hx - head_r, hy - head_r)[1],
              F(hx + head_r, hy + head_r)[0], F(hx + head_r, hy + head_r)[1]],
             outline=(*AMBER_GLOW, 235), width=2)
draw.line([F(0, hy + head_r), F(0, hy + head_r + 14)], fill=(*AMBER_GLOW, 225), width=2)
fig_line(left); fig_line(right)
fig_line([left[0], right[0]]); fig_line([left[-1], right[-1]])
fig_line(raised_arm); fig_line(lower_arm)
# hands
for (hxh, hyh) in [raised_arm[-1], lower_arm[-1]]:
    draw.ellipse([hxh - 6, hyh - 6, hxh + 6, hyh + 6],
                 outline=(*AMBER_GLOW, 235), width=2)
fig_line(leg(-1, stride=-9)); fig_line(leg(1, stride=9))
# feet
for (lx, ly) in [leg(-1, stride=-9)[-1], leg(1, stride=9)[-1]]:
    draw.line([(lx - 8, ly), (lx + 8, ly + 2)], fill=(*AMBER_GLOW, 230), width=2)

# scarf crisp
fig_line(scarf_pts, w=2, a=160, col=AMBER)
draw.line(scarf_pts2, fill=(*AMBER, 90), width=1, joint="curve")
# hair crisp
for k in range(6):
    pts = []
    sx0 = -12 + k * 5
    sy0 = hy - head_r + 8
    for i in range(30):
        t = i / 29
        x = sx0 + t * (96 + k * 14) + 10 * math.sin(t * 5 + k)
        y = sy0 + t * (32 + k * 4) + 8 * math.sin(t * 4 + k * 0.7)
        pts.append(F(x, y))
    draw.line(pts, fill=(*AMBER_GLOW, 130 - k * 12), width=1, joint="curve")

# a bright point at the raised hand — the locus of command
rh = raised_arm[-1]
for rr, a in [(22, 40), (14, 80), (8, 140)]:
    draw.ellipse([rh[0] - rr, rh[1] - rr, rh[0] + rr, rh[1] + rr],
                 fill=(*AMBER_GLOW, a))

# ---------------------------------------------------------------- frame & typography
M = 90
draw.rectangle([M, M, W - M, H - M], outline=(*CYAN_MIST, 70), width=1)
tick = 26
for (cx0, cy0, dx, dy) in [
    (M, M, 1, 1), (W - M, M, -1, 1), (M, H - M, 1, -1), (W - M, H - M, -1, -1)
]:
    draw.line([(cx0, cy0), (cx0 + dx * tick, cy0)], fill=(*BONE, 170), width=2)
    draw.line([(cx0, cy0), (cx0, cy0 + dy * tick)], fill=(*BONE, 170), width=2)

FONT_DIR = "/data/user/skills/canvas-design/canvas-fonts"
def font(name, size):
    return ImageFont.truetype(f"{FONT_DIR}/{name}", size)

f_title = font("InstrumentSerif-Regular.ttf", 54)
f_sub   = font("InstrumentSerif-Italic.ttf", 30)
f_mono  = font("DMMono-Regular.ttf", 20)
f_mono_s= font("DMMono-Regular.ttf", 16)
f_label = font("InstrumentSerif-Regular.ttf", 22)

title = "Aeolian Cartography"
sub   = "Plate I  —  The Boy Who Holds the Wind"
draw.text((M + 8, M + 38), title, font=f_title, fill=(*BONE, 238))
tw = draw.textlength(title, font=f_title)
draw.line([(M + 8, M + 104), (M + 8 + tw, M + 104)], fill=(*AMBER, 190), width=1)
draw.text((M + 8, M + 116), sub, font=f_sub, fill=(*CYAN_PALE, 205))

spec = "Spec. № 047  ·  Field Study"
draw.text((W - M - 8 - draw.textlength(spec, font=f_mono), M + 44), spec,
          font=f_mono, fill=(*CYAN_PALE, 185))

# right-side coordinate block
coord_lines = [
    "47°34′N   12°08′E",
    "bearing   087°",
    "force     6.4 m·s⁻¹",
    "subject   juvenile, ~12 yr",
    "observed  dusk, clear",
]
for i, line in enumerate(coord_lines):
    draw.text((fx + R * 0.82, fy - 70 + i * 30), line,
              font=f_mono_s, fill=(*CYAN_PALE, 175))

# left annotation with leader
lx = fx - R * 1.55
draw.line([(fx - R * 0.92, fy - 6), (lx, fy - 6)],
          fill=(*CYAN_MIST, 150), width=1)
draw.ellipse([fx - R * 0.92 - 3, fy - 9, fx - R * 0.92 + 3, fy - 3],
             fill=(*AMBER, 230))
draw.text((lx - 12, fy - 34), "calm center",
          font=f_label, fill=(*BONE, 215))
draw.text((lx - 12, fy - 12), "v ≈ 0.0 m·s⁻¹",
          font=f_mono_s, fill=(*CYAN_PALE, 165))

# right annotation pointing to raised hand
rhx, rhy = raised_arm[-1]
draw.line([(rhx - 16, rhy - 16), (rhx - 120, rhy - 70)],
          fill=(*CYAN_MIST, 150), width=1)
draw.ellipse([rhx - 19, rhy - 19, rhx - 13, rhy - 13], fill=(*AMBER, 230))
draw.text((rhx - 250, rhy - 96), "locus of command",
          font=f_label, fill=(*BONE, 215))
draw.text((rhx - 250, rhy - 74), "divergence origin",
          font=f_mono_s, fill=(*CYAN_PALE, 165))

# bottom legend
draw.line([(M + 8, H - M - 100), (W - M - 8, H - M - 100)],
          fill=(*CYAN_MIST, 95), width=1)
legend = "streamlines denote instantaneous air trajectories about a stationary body"
draw.text((M + 8, H - M - 84), legend, font=f_mono_s, fill=(*CYAN_PALE, 175))
legend2 = "warm field marks the region of held breath — the figure's sphere of influence"
draw.text((M + 8, H - M - 60), legend2, font=f_mono_s, fill=(*CYAN_PALE, 155))

sig = "observed & rendered  —  A.C."
draw.text((W - M - 8 - draw.textlength(sig, font=f_sub), H - M - 46),
          sig, font=f_sub, fill=(*AMBER, 205))

# scale bar
sbx, sby = M + 8, H - M - 40
draw.line([(sbx, sby), (sbx + 120, sby)], fill=(*BONE, 205), width=1)
for k in range(5):
    xx = sbx + k * 30
    draw.line([(xx, sby), (xx, sby + 6)], fill=(*BONE, 205), width=1)
draw.text((sbx, sby + 10), "0    1    2    3    4  m", font=f_mono_s,
          fill=(*CYAN_PALE, 155))

# ---------------------------------------------------------------- grain
arr = np.asarray(img).astype(np.float32)
noise = (np.random.randn(H, W, 3) * 2.6)
arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
img = Image.fromarray(arr, "RGB")

img.save("/workspace/aeolian_cartography.png", "PNG", optimize=True)
print("saved", img.size)
