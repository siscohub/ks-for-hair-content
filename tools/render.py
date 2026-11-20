"""Render KS for Hair Instagram post (1080x1350) and story (1080x1920) from a JSON spec.
Usage: python3 render.py day.json outdir
JSON: {"post": {"kicker","title","body","footer"}, "story": {"kicker","title","body","cta"}}
"""
import json, sys, pathlib, html
from playwright.sync_api import sync_playwright

F = pathlib.Path(__file__).parent / "node_modules/@fontsource"
FONTS = f"""
@font-face{{font-family:PF;src:url(file://{F}/playfair-display/files/playfair-display-latin-400-normal.woff2)}}
@font-face{{font-family:PF;font-style:italic;src:url(file://{F}/playfair-display/files/playfair-display-latin-400-italic.woff2)}}
@font-face{{font-family:PF;font-weight:700;src:url(file://{F}/playfair-display/files/playfair-display-latin-700-normal.woff2)}}
@font-face{{font-family:MS;src:url(file://{F}/montserrat/files/montserrat-latin-400-normal.woff2)}}
@font-face{{font-family:MS;font-weight:600;src:url(file://{F}/montserrat/files/montserrat-latin-600-normal.woff2)}}
"""

def e(s): return html.escape(s or "").replace("\n", "<br>")

CSS = FONTS + """
*{margin:0;box-sizing:border-box}
body{width:var(--w);height:var(--h);background:#F4EDE4;color:#2B211C;font-family:MS;overflow:hidden;position:relative}
.frame{position:absolute;inset:44px;border:2px solid #B8956A;}
.arc{position:absolute;width:900px;height:900px;border-radius:50%;background:#E8DACB;right:-330px;top:-330px}
.arc2{position:absolute;width:520px;height:520px;border-radius:50%;border:2px solid #B8956A;right:-260px;bottom:-260px}
.wrap{position:absolute;inset:110px 110px;display:flex;flex-direction:column}
.brand{font-family:PF;font-size:40px;letter-spacing:2px}
.brand i{color:#9A7650}
.kicker{font-weight:600;font-size:26px;letter-spacing:7px;text-transform:uppercase;color:#9A7650;margin-top:auto}
.title{font-family:PF;font-weight:700;font-size:var(--ts);line-height:1.08;margin-top:28px}
.title i{font-weight:400;color:#9A7650}
.line{width:120px;height:3px;background:#B8956A;margin:44px 0}
.body{font-size:var(--bs);line-height:1.55;color:#4A3C33}
.foot{margin-top:auto;font-size:24px;letter-spacing:4px;text-transform:uppercase;color:#7A6455}
.cta{margin-top:auto;align-self:flex-start;background:#2B211C;color:#F4EDE4;font-weight:600;font-size:34px;letter-spacing:3px;padding:34px 56px;border-radius:80px}
"""

def page(w, h, ts, bs, inner):
    return f"<html><head><style>{CSS}</style></head><body style='--w:{w}px;--h:{h}px;--ts:{ts}px;--bs:{bs}px'><div class=arc></div><div class=arc2></div><div class=frame></div><div class=wrap><div class=brand>KS <i>for</i> Hair</div>{inner}</div></body></html>"

def title(t):  # *word* -> italic accent
    parts = e(t).split("*")
    return "".join(f"<i>{p}</i>" if i % 2 else p for i, p in enumerate(parts))

def main(spec_path, out):
    s = json.loads(pathlib.Path(spec_path).read_text())
    out = pathlib.Path(out).resolve(); out.mkdir(parents=True, exist_ok=True)
    p, st = s["post"], s["story"]
    post = page(1080, 1350, 96, 36, f"<div class=kicker>{e(p['kicker'])}</div><div class=title>{title(p['title'])}</div><div class=line></div><div class=body>{e(p['body'])}</div><div class=foot style='margin-top:60px'>{e(p.get('footer',''))}</div>")
    story = page(1080, 1920, 118, 40, f"<div class=kicker>{e(st['kicker'])}</div><div class=title>{title(st['title'])}</div><div class=line></div><div class=body>{e(st['body'])}</div><div class=cta>{e(st['cta'])}</div>")
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        for name, h, w, hh in [("post", post, 1080, 1350), ("story", story, 1080, 1920)]:
            f = out / f"{name}.html"; f.write_text(h)
            pg = b.new_page(viewport={"width": w, "height": hh})
            pg.goto(f.as_uri()); pg.wait_for_timeout(400)
            pg.screenshot(path=str(out / f"{name}.png"))
            f.unlink()
        b.close()

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
