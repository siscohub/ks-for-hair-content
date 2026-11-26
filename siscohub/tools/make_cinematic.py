"""(Emojis/… are stripped: the Arabic display font has no glyphs for them.)
Cinematic "mindset" reel for SiscoHub (dark, grainy, B&W film look, brush-stroke frame,
kinetic Arabic text word by word, a chart line drawing in the background, logo at the end).
Original visuals only (no film/TV footage).

Usage: python3 make_cinematic.py spec.json out.mp4
spec: {"lines": ["اسمعني منيح 👂", "السوق ما بيكافئ", "الأذكى…", "بيكافئ *الأصبر*."],
       "outro": "خطة · ستوب · صبر"}
Each line appears in turn (~1.6 s each), words pop in one by one; *word* = teal accent.
"""
import json, sys, math, pathlib, random, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FONT = str(ROOT / "tools/node_modules/@fontsource/cairo/files/cairo-arabic-900-normal.woff2")
FONT_L = str(ROOT / "tools/node_modules/@fontsource/cairo/files/cairo-latin-800-normal.woff2")
LOGO = ROOT / "tools/assets/sisco_logo.jpg"
MUSIC = sorted((ROOT / "tools/assets/music").glob("sisco*.m4a"))
W, H, FPS = 1080, 1920, 30
TEAL = (53, 198, 179)
rng = np.random.default_rng(7)


def brush_panel():
    """Rough dark brush-stroke panel mask (procedural)."""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    x0, x1, y0, y1 = 110, 970, 330, 1590
    for i in range(260):  # ragged horizontal strokes
        y = rng.integers(y0 - 60, y1 + 60)
        l = x0 + rng.normal(0, 25); r = x1 + rng.normal(0, 25)
        d.line([(l, y), (r, y + rng.normal(0, 3))], fill=255, width=int(rng.integers(6, 18)))
    for i in range(90):  # ragged vertical edges
        x = rng.choice([x0, x1]) + rng.normal(0, 22)
        ya = rng.integers(y0 - 40, y1); d.line([(x, ya), (x + rng.normal(0, 8), ya + rng.integers(80, 400))], fill=255, width=int(rng.integers(4, 14)))
    d.rectangle([x0 + 20, y0 + 20, x1 - 20, y1 - 20], fill=255)
    return m.filter(ImageFilter.GaussianBlur(1.2)).rotate(-2.5, resample=Image.BICUBIC)


def chart_points():
    pts, y = [], 0.0
    for i in range(60):
        y += rng.normal(0.35, 1.6)
        pts.append(y)
    pts = np.array(pts); pts = (pts - pts.min()) / (pts.max() - pts.min())
    xs = np.linspace(190, 890, len(pts)); ys = 1520 - pts * 300
    return list(zip(xs, ys))


def text_img(words, n_visible, size):
    """Render first n_visible words of a line (RTL, centered). *w* = accent."""
    f = ImageFont.truetype(FONT, size)
    shown = [w for w in words[:n_visible]]
    clean = " ".join(w.strip("*") for w in shown)
    img = Image.new("RGBA", (W, size * 2), (0, 0, 0, 0))
    if not shown:
        return img
    d = ImageDraw.Draw(img)
    tw = d.textlength(clean, font=f, direction="rtl", language="ar")
    x = (W + tw) / 2  # draw right-to-left word by word
    for w in shown:
        acc = w.startswith("*")
        t = w.strip("*")
        ww = d.textlength(t, font=f, direction="rtl", language="ar")
        sp = d.textlength(" ", font=f)
        x -= ww
        col = TEAL + (255,) if acc else (245, 245, 240, 255)
        d.text((x + 4, 6), t, font=f, fill=(0, 0, 0, 200), direction="rtl", language="ar")
        d.text((x, 0), t, font=f, fill=col, direction="rtl", language="ar")
        x -= sp
    return img


def main(spec_path, out):
    s = json.loads(pathlib.Path(spec_path).read_text(encoding="utf-8"))
    import re
    clean = lambda x: re.sub(r"[^\u0600-\u06FF\u0750-\u077F\sA-Za-z0-9*%-]", "", x.replace("…", "").replace("·", "،")).strip()
    lines = [clean(l).split() for l in s["lines"]]
    s["outro"] = clean(s.get("outro", ""))
    per_line, outro_t = 1.7, 2.2
    total = per_line * len(lines) + outro_t
    N = int(total * FPS)
    panel = np.array(brush_panel(), np.float32)[..., None] / 255
    pts = chart_points()
    sm = rng.normal(0, 1, (H // 64, W // 64)); sm = Image.fromarray(((sm - sm.min()) / (sm.max() - sm.min()) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(40))
    smoke = (np.array(sm, np.float32)[..., None] / 255) * 70 + 35
    panel_tex = (np.array(Image.fromarray(rng.integers(0, 255, (H // 8, W // 8), dtype=np.uint8)).resize((W, H), Image.BICUBIC), np.float32)[..., None] / 255)
    logo = Image.open(LOGO).convert("RGB").resize((220, 220))
    lmask = Image.new("L", (220, 220), 0); ImageDraw.Draw(lmask).rounded_rectangle([0, 0, 219, 219], 40, fill=255)
    tmp = pathlib.Path(tempfile.mkdtemp())
    scratches = [(rng.integers(0, W), rng.integers(0, 40)) for _ in range(6)]
    cache = {}
    for i in range(N):
        t = i / FPS
        # background: dark textured gradient
        base = smoke + 6 * math.sin(t * 1.3)
        img = base * (1 - panel) + (10 + 6 * panel_tex) * panel
        img = np.repeat(img, 3, 2)
        pil = Image.fromarray(img.clip(0, 255).astype(np.uint8))
        d = ImageDraw.Draw(pil)
        # chart line drawing in background
        k = int(min(1, t / (total * 0.8)) * (len(pts) - 1)) + 1
        if k > 1:
            d.line(pts[:k], fill=(55, 95, 92), width=5, joint="curve")
            x, y = pts[k - 1]; d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(110, 190, 180), width=4)
        # text
        li = int(t // per_line)
        if li < len(lines):
            lt = t - li * per_line
            words = lines[li]
            nv = min(len(words), 1 + int(lt / 0.28))
            size = 118 if len(" ".join(words)) < 16 else 96
            key = (li, nv)
            if key not in cache:
                cache[key] = text_img(words, nv, size)
            ti = cache[key]
            pop = 1 + 0.06 * max(0, 1 - (lt % 0.28) / 0.12) if nv < len(words) or lt < len(words) * 0.28 + 0.12 else 1
            if pop != 1:
                ti = ti.resize((int(W * pop), int(ti.height * pop)), Image.BICUBIC)
            pil.paste(ti, ((W - ti.width) // 2, 960 - ti.height // 2), ti)
        else:
            ot = t - per_line * len(lines)
            a = min(1, ot / 0.5)
            lg = Image.composite(logo, Image.new("RGB", logo.size), lmask)
            pil.paste(lg, ((W - 220) // 2, 640), Image.eval(lmask, lambda v: int(v * a)))
            f = ImageFont.truetype(FONT, 84)
            txt = s.get("outro", "")
            tw = d.textlength(txt, font=f, direction="rtl", language="ar")
            d.text(((W - tw) / 2, 900), txt, font=f, fill=tuple(int(c * a) for c in TEAL), direction="rtl", language="ar")
            f2 = ImageFont.truetype(FONT_L, 46); t2 = "SiscoHub"
            d.text(((W - d.textlength(t2, font=f2)) / 2, 1040), t2, font=f2, fill=(int(230 * a),) * 3)
        # disclaimer
        fd = ImageFont.truetype(FONT, 30); dt = "محتوى تعليمي فقط · ليس نصيحة مالية"
        d.text(((W - d.textlength(dt, font=fd, direction="rtl", language="ar")) / 2, 1790), dt, font=fd, fill=(120, 120, 118), direction="rtl", language="ar")
        arr = np.array(pil, np.float32)
        # film look: B&W with slight teal tint, grain, flicker, vignette, scratches
        g = arr.mean(2, keepdims=True)
        tint = np.array([0.92, 1.0, 1.0])
        txtmask = (np.abs(arr[..., 1:2] - arr[..., 0:1]) > 40).astype(np.float32)  # keep teal text colourful
        arr = arr * txtmask + (g * tint) * (1 - txtmask)
        arr *= 1 + 0.04 * math.sin(t * 23) + rng.normal(0, 0.015)
        arr += rng.normal(0, 14, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
        vy = np.linspace(-1, 1, H)[:, None]; vx = np.linspace(-1, 1, W)[None, :]
        arr *= (1 - 0.45 * (vx ** 2 + vy ** 2) / 2)[..., None]
        for sx, sd in scratches:
            if (i + sd) % 37 < 3:
                xx = int((sx + i * 3) % W); arr[:, xx:xx + 2] += 60
        Image.fromarray(arr.clip(0, 255).astype(np.uint8)).save(tmp / f"f{i:04d}.jpg", quality=90)
    music = random.choice(MUSIC) if MUSIC else None
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%04d.jpg")]
    if music:
        cmd += ["-i", str(music), "-filter_complex", f"[1:a]atrim=0:{total},lowpass=f=2500,volume=0.9,afade=t=out:st={total-1}:d=1[a]", "-map", "0:v", "-map", "[a]"]
    cmd += ["-t", f"{total}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
