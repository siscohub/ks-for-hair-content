"""Render SiscoHub (Arabic, RTL) Instagram post 1080x1350 and/or story 1080x1920 from JSON.
Usage: python3 render_sisco.py spec.json outdir
JSON: {"post": {"kicker","title","body","footer"}  (optional),
       "story": {"kicker","title","body","cta"}    (optional)}
In "title", wrap accent words in *asterisks* (rendered gold).
Outputs post.png / story.png.
"""
import json, sys, pathlib, html
from playwright.sync_api import sync_playwright

F = pathlib.Path(__file__).resolve().parent / "node_modules/@fontsource/cairo/files"
FONTS = "".join(
    f"@font-face{{font-family:C;font-weight:{w};src:url(file://{F}/cairo-arabic-{w}-normal.woff2)}}"
    f"@font-face{{font-family:C;font-weight:{w};src:url(file://{F}/cairo-latin-{w}-normal.woff2)}}"
    for w in (400, 600, 800))

CSS = FONTS + """
*{margin:0;box-sizing:border-box}
body{width:var(--w);height:var(--h);background:#0B0F14;color:#F3F1EA;font-family:C;direction:ltr;overflow:hidden;position:relative}
.glow{position:absolute;width:1000px;height:1000px;border-radius:50%;background:radial-gradient(circle,rgba(53,198,179,.20),rgba(74,123,224,0) 65%);left:-380px;top:-380px}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:90px 90px}
.chart{position:absolute;left:0;width:100%;bottom:0;height:var(--ch);opacity:.4}
.wrap{direction:rtl;position:absolute;inset:100px 96px 150px;display:flex;flex-direction:column}
.brand{display:flex;align-items:center;gap:16px;font-weight:800;font-size:38px;direction:ltr;align-self:flex-end}
.dot{width:96px;height:96px;border-radius:24px;background:url(LOGO) center/cover;box-shadow:0 0 0 2px rgba(53,198,179,.5)}
.brand span{color:#35C6B3}
.kicker{margin-top:auto;display:inline-block;align-self:flex-start;font-weight:600;font-size:30px;color:#fff;background:linear-gradient(90deg,#35C6B3,#4A7BE0);padding:6px 26px;border-radius:40px}
.title{font-weight:800;font-size:var(--ts);line-height:1.25;margin-top:30px}
.title b{background:linear-gradient(90deg,#35C6B3,#5B8BEF);-webkit-background-clip:text;color:transparent;font-weight:800}
.line{width:130px;height:5px;background:#35C6B3;border-radius:4px;margin:38px 0}
.body{font-size:var(--bs);line-height:1.75;color:#C9CCD3;white-space:pre-line}
.foot{margin-top:56px;font-size:26px;color:#8A8F99}
.cta{margin-top:auto;align-self:flex-start;background:linear-gradient(90deg,#35C6B3,#4A7BE0);color:#fff;font-weight:800;font-size:40px;padding:30px 64px;border-radius:80px}
.disc{direction:rtl;position:absolute;bottom:40px;left:0;right:0;text-align:center;font-size:22px;color:#6B707A}
"""

CHART = """<svg class=chart viewBox="0 0 1080 300" preserveAspectRatio="none"><defs><linearGradient id=g x1=0 y1=0 x2=0 y2=1><stop offset=0 stop-color="#35C6B3" stop-opacity=".35"/><stop offset=1 stop-color="#4A7BE0" stop-opacity="0"/></linearGradient></defs>
<path d="M0,250 L90,230 L170,245 L250,190 L330,205 L420,150 L500,170 L590,120 L670,140 L760,90 L840,110 L930,60 L1080,40 L1080,300 L0,300Z" fill="url(#g)"/>
<path d="M0,250 L90,230 L170,245 L250,190 L330,205 L420,150 L500,170 L590,120 L670,140 L760,90 L840,110 L930,60 L1080,40" fill="none" stroke="#35C6B3" stroke-width="4"/></svg>"""


LOGO = (pathlib.Path(__file__).resolve().parent / "assets/sisco_logo.jpg").as_uri()
CSS = CSS.replace("url(LOGO)", f"url({LOGO})")


def e(s):
    return html.escape(s or "")


def title(t):
    parts = e(t).replace("\n", "<br>").split("*")
    return "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(parts))


def page(w, h, ts, bs, ch, inner):
    return (f"<html><head><meta charset=utf-8><style>{CSS}</style></head>"
            f"<body style='--w:{w}px;--h:{h}px;--ts:{ts}px;--bs:{bs}px;--ch:{ch}px'>"
            f"<div class=grid></div><div class=glow></div>{CHART}"
            f"<div class=wrap><div class=brand><div class=dot></div>Sisco<span>Hub</span></div>{inner}</div>"
            f"<div class=disc>محتوى تعليمي فقط · ليس نصيحة مالية</div></body></html>")


def main(spec_path, out):
    s = json.loads(pathlib.Path(spec_path).read_text(encoding="utf-8"))
    out = pathlib.Path(out).resolve(); out.mkdir(parents=True, exist_ok=True)
    jobs = []
    if s.get("post"):
        p = s["post"]
        jobs.append(("post", 1080, 1350, page(1080, 1350, 84, 38, 150,
            f"<div class=kicker>{e(p['kicker'])}</div><div class=title>{title(p['title'])}</div>"
            f"<div class=line></div><div class=body>{e(p['body'])}</div><div class=foot>{e(p.get('footer',''))}</div>")))
    if s.get("story"):
        st = s["story"]
        jobs.append(("story", 1080, 1920, page(1080, 1920, 104, 42, 380,
            f"<div class=kicker>{e(st['kicker'])}</div><div class=title>{title(st['title'])}</div>"
            f"<div class=line></div><div class=body>{e(st['body'])}</div><div class=cta>{e(st['cta'])}</div>"
            f"<div style='height:120px'></div>")))
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        for name, w, h, doc in jobs:
            f = out / f"{name}.html"; f.write_text(doc, encoding="utf-8")
            pg = b.new_page(viewport={"width": w, "height": h})
            pg.goto(f.as_uri()); pg.wait_for_timeout(500)
            pg.screenshot(path=str(out / f"{name}.png")); f.unlink()
        b.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
