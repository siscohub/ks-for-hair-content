"""KS for Hair — brand-matched designs (owner's poster style: cream, brown-gold serif, script accents, logo).
Usage: python3 render_ks.py spec.json outdir
spec: {"post": {...}, "story": {...}}  each optional. Fields:
  kicker, title (CAPS serif headline), script (handwritten accent line), body (lines, \n), cta (story),
  footer (post), swatch ("#hex" -> hair-strand colour sample), swatch_label, rows ([[label, value], ...] for formula cards)
HIDE_BODY=1 hides everything below the headline (for reel reveal).
"""
import json, sys, pathlib, html, os
from playwright.sync_api import sync_playwright

T = pathlib.Path(__file__).resolve().parent
F = T / "node_modules/@fontsource"
def ff(fam, file, w=400, style="normal"):
    return f"@font-face{{font-family:{fam};font-weight:{w};font-style:{style};src:url(file://{F}/{file})}}"
FONTS = (ff("Serif", "cormorant-garamond/files/cormorant-garamond-latin-600-normal.woff2", 600)
         + ff("Serif", "cormorant-garamond/files/cormorant-garamond-latin-700-normal.woff2", 700)
         + ff("Script", "great-vibes/files/great-vibes-latin-400-normal.woff2")
         + ff("Sans", "lato/files/lato-latin-400-normal.woff2") + ff("Sans", "lato/files/lato-latin-700-normal.woff2", 700))
LOGO = (T / "assets/ks_logo.png").as_uri()
HIDE = ".reveal{visibility:hidden}" if os.environ.get("HIDE_BODY") else ""

CSS = FONTS + """
*{margin:0;box-sizing:border-box}
body{width:var(--w);height:var(--h);overflow:hidden;position:relative;font-family:Sans;color:#3B2A20;
 background:radial-gradient(ellipse at 70% 20%,#F6EDE3 0%,#EBDCCB 55%,#E2CFBA 100%)}
.frame{position:absolute;inset:34px;border:2px solid #B89466;border-radius:6px}
.wrap{position:absolute;inset:80px 86px;display:flex;flex-direction:column;align-items:center;text-align:center}
.logo{width:var(--lw);height:auto}
.orn{color:#B89466;font-size:30px;letter-spacing:10px;margin:10px 0 6px}
.kicker{font-weight:700;font-size:24px;letter-spacing:6px;text-transform:uppercase;color:#9A7448;margin-top:var(--gap)}
.title{white-space:nowrap;max-width:100%;font-family:Serif;font-weight:700;font-size:var(--ts);line-height:1.0;color:#6B4423;text-transform:uppercase;margin-top:14px;letter-spacing:1px}
.script{font-family:Script;font-size:var(--ss);color:#8A6237;margin-top:2px;line-height:1.1}
.heart{color:#8A6237}
.rule{display:flex;align-items:center;gap:16px;margin:22px 0;color:#8A6237;font-size:26px}
.rule:before,.rule:after{content:"";width:120px;height:2px;background:#B89466}
.panel{background:rgba(250,244,236,.78);border:2px solid #D7C1A3;border-radius:28px;padding:34px 40px;width:100%;display:flex;gap:34px;align-items:center;text-align:left}
.strand{flex:0 0 var(--sw);height:calc(var(--sw)*1.55);border-radius:var(--sw) var(--sw) 40px 40px;
 background:linear-gradient(100deg,rgba(255,255,255,.18) 0 6%,transparent 6% 12%,rgba(0,0,0,.10) 12% 15%,transparent 15% 30%,rgba(255,255,255,.14) 30% 33%,transparent 33% 52%,rgba(0,0,0,.10) 52% 55%,transparent 55% 74%,rgba(255,255,255,.16) 74% 77%,transparent 77%),
 linear-gradient(180deg,rgba(0,0,0,.25),rgba(255,255,255,.08) 40%,rgba(0,0,0,.18)),var(--c);box-shadow:0 10px 24px rgba(80,50,20,.25)}
.slabel{font-family:Script;font-size:34px;color:#8A6237;text-align:center;margin-top:8px}
.rows{flex:1;display:flex;flex-direction:column;gap:var(--rg,16px)}
.row .k{font-weight:700;font-size:21px;letter-spacing:3px;text-transform:uppercase;color:#9A7448}
.row .v{font-family:Serif;font-weight:700;font-size:var(--vs);color:#3B2A20;line-height:1.1}
.body{font-size:var(--bs);line-height:1.6;color:#4A3A30;white-space:pre-line}
.note{font-size:var(--ns);color:#7A6455;margin-top:22px;line-height:1.45;white-space:pre-line}
.cta{margin-top:auto;background:#6B4423;color:#F6EDE3;font-weight:700;font-size:34px;letter-spacing:2px;padding:26px 60px;border-radius:70px}
.foot{margin-top:auto;font-family:Script;font-size:46px;color:#8A6237}
.small{font-size:20px;letter-spacing:4px;color:#7A6455;margin-top:6px}
"""

FIT_JS = "<script>document.querySelectorAll('.title').forEach(t=>{let f=parseFloat(getComputedStyle(t).fontSize);while(t.scrollWidth>t.parentElement.clientWidth&&f>40){f-=2;t.style.fontSize=f+'px'}})</script>"

def e(s): return html.escape(s or "")

def block(d, story):
    out = f"<img class=logo src='{LOGO}'><div class=orn>— ✦ —</div>"
    if d.get("kicker"): out += f"<div class=kicker>{e(d['kicker'])}</div>"
    out += f"<div class=title>{e(d['title']).replace(chr(10), '<br>')}</div>"
    if d.get("script"): out += f"<div class=script>{e(d['script'])} <span class=heart>♡</span></div>"
    out += "<div class=reveal style='width:100%;display:flex;flex-direction:column;align-items:center;flex:1'>"
    out += "<div class=rule>♥</div>"
    if d.get("swatch") or d.get("rows"):
        sw = ""
        if d.get("swatch"):
            sw = f"<div><div class=strand style='--c:{e(d['swatch'])}'></div><div class=slabel>{e(d.get('swatch_label',''))}</div></div>"
        rows = "".join(f"<div class=row><div class=k>{e(k)}</div><div class=v>{e(v)}</div></div>" for k, v in d.get("rows", []))
        body = f"<div class=body style='margin-top:6px'>{e(d['body'])}</div>" if d.get("body") and not rows else ""
        out += f"<div class=panel>{sw}<div class=rows>{rows}{body}</div></div>"
        if d.get("note"): out += f"<div class=note>{e(d['note'])}</div>"
    elif d.get("body"):
        out += f"<div class=body>{e(d['body'])}</div>"
    if story and d.get("cta"): out += f"<div class=cta>{e(d['cta'])}</div>"
    out += f"<div class=foot>{e(d.get('footer') or 'Dein Style. Dein Moment.')}</div>" if not story else "<div class=small>KS FOR HAIR · GRAZ</div>"
    out += "</div>"
    return out

def page(w, h, v, inner):
    style = ";".join(f"--{k}:{x}" for k, x in v.items())
    return f"<html><head><meta charset=utf-8><style>{CSS}{HIDE}</style></head><body style='--w:{w}px;--h:{h}px;{style}'><div class=frame></div><div class=wrap>{inner}</div>{FIT_JS}</body></html>"

def main(spec, out):
    s = json.loads(pathlib.Path(spec).read_text(encoding="utf-8"))
    out = pathlib.Path(out).resolve(); out.mkdir(parents=True, exist_ok=True)
    jobs = []
    if s.get("post"):
        jobs.append(("post", 1080, 1350, page(1080, 1350, {"lw": "300px", "gap": "18px", "ts": "88px", "ss": "70px", "bs": "34px", "sw": "170px", "vs": "38px", "ns": "20px"}, block(s["post"], False))))
    if s.get("story"):
        jobs.append(("story", 1080, 1920, page(1080, 1920, {"lw": "360px", "gap": "70px", "ts": "110px", "ss": "92px", "bs": "42px", "sw": "250px", "vs": "54px", "ns": "26px", "rg": "26px"}, block(s["story"], True))))
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        for name, w, h, doc in jobs:
            f = out / f"{name}.html"; f.write_text(doc, encoding="utf-8")
            pg = b.new_page(viewport={"width": w, "height": h}); pg.goto(f.as_uri()); pg.wait_for_timeout(500)
            pg.screenshot(path=str(out / f"{name}.png")); f.unlink()
        b.close()

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
