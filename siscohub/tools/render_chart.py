"""SiscoHub chart-lesson reel frame (1080x1920): title + an illustrative candlestick chart
(synthetic data, no real prices) with annotations for one trading concept.

Usage:  [HIDE_BODY=1] python3 siscohub/tools/render_chart.py spec.json outdir
spec:   {"story": {"kicker","title","body","cta","chart": "<concept>", "legend": [optional list]}}
Every concept numbers its key candles (gold 1/2/3 on the chart) and a legend under the chart
names each numbered candle and what it does. "legend" in the spec overrides the default text
(one short line per number, ~34 chars max).
concepts: fvg, fvg_bear, choch, bos, order_block, liquidity_sweep, liquidity_sweep_high,
          support_resistance, engulfing, pin_bar,
          candle patterns: hammer, inverted_hammer, doji, morning_star, harami_bull, tweezer_bottom,
          three_white_soldiers, marubozu_bull, shooting_star, hanging_man, evening_star,
          engulfing_bear, three_black_crows, tweezer_top
HIDE_BODY=1 renders candles only (annotations, body and CTA hidden) for the reveal frame A.
Writes outdir/story.png. Reuses fonts/colours/logo from tools/render_sisco.py (not modified).
"""
import json, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import render_sisco as rs  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

UP, DN = "#35C6B3", "#E0565B"
GOLD, BLUE, MUTED = "#F2C14E", "#5B8BEF", "#8A8F99"

# ---- synthetic candles: (open, high, low, close), price 0..100 ----

def C(o, c, h=None, l=None):
    hi = max(o, c) + 2 if h is None else h
    lo = min(o, c) - 2 if l is None else l
    return (o, hi, lo, c)


def mirror(cs):
    return [(100 - o, 100 - l, 100 - h, 100 - c) for o, h, l, c in cs]


CONCEPTS = {}

# Bullish FVG: gap between high of c[6] and low of c[8]; price later returns into it and reacts.
_fvg = [C(44, 40), C(40, 37), C(37, 39), C(39, 35), C(35, 33), C(33, 36),
        C(36, 38, h=41),          # 6: candle 1 (high 41)
        C(38, 62, h=63, l=37),    # 7: impulse
        C(62, 66, h=68, l=52),    # 8: candle 3 (low 52)
        C(66, 70), C(70, 67), C(67, 63), C(63, 58), C(58, 54, l=48),
        C(54, 60), C(60, 66), C(66, 72), C(72, 76), C(76, 74), C(74, 80)]
CONCEPTS["fvg"] = dict(candles=_fvg, ann=[
    ("rect", 6, 19.6, 41, 52, GOLD, "FVG – فجوة القيمة العادلة"),
    ("mark", 6, 41, "1"), ("mark", 7, 63, "2"), ("mark", 8, 68, "3"),
    ("arrow", 13, 48, "رجوع للفجوة")])
CONCEPTS["fvg_bear"] = dict(candles=mirror(_fvg), ann=[
    ("rect", 6, 19.6, 48, 59, GOLD, "FVG هابطة"),
    ("mark", 6, 59, "1"), ("mark", 7, 37, "2"), ("mark", 8, 32, "3"),
    ("arrow_dn", 13, 52, "رجوع للفجوة")])

# CHoCH: downtrend (LH/LL) then break above last lower high.
_choch = [C(80, 74), C(74, 66), C(66, 70), C(70, 72, h=75),   # LH1 75
          C(72, 62), C(62, 55), C(55, 58), C(58, 63, h=65),   # LH2 65
          C(63, 52), C(52, 45, l=42),                         # LL 42
          C(45, 50), C(50, 55), C(55, 53), C(53, 60), C(60, 70, h=72),  # break 65
          C(70, 68), C(68, 74), C(74, 78), C(78, 76), C(76, 82)]
CONCEPTS["choch"] = dict(candles=_choch, ann=[
    ("label", 3, 75, "LH", MUTED), ("label", 7, 65, "LH", MUTED), ("label_dn", 9, 42, "LL", MUTED),
    ("hline", 7, 15, 65, BLUE, "CHoCH – تغيّر الاتجاه"),
    ("trend", [(0, 82), (3, 75), (5, 53), (7, 65), (9, 42)], DN),
    ("trend", [(9, 42), (14, 72)], UP)])

# BOS: uptrend, higher highs, break of previous high continues trend.
_bos = [C(30, 36), C(36, 42), C(42, 47, h=50), C(47, 43), C(43, 40, l=37),
        C(40, 46), C(46, 52), C(52, 57, h=59), C(57, 53), C(53, 49, l=46),
        C(49, 55), C(55, 62, h=64), C(62, 66), C(66, 63), C(63, 59, l=56),
        C(59, 65), C(65, 72, h=74), C(72, 70), C(70, 76), C(76, 80)]
CONCEPTS["bos"] = dict(candles=_bos, ann=[
    ("hline", 2, 11, 50, BLUE, "BOS"), ("hline", 7, 16, 59, BLUE, "BOS"),
    ("label", 2, 50, "HH", MUTED), ("label", 7, 59, "HH", MUTED),
    ("label_dn", 4, 37, "HL", MUTED), ("label_dn", 9, 46, "HL", MUTED)])

# Bullish order block: last bearish candle before a strong move up; price returns to it.
_ob = [C(50, 47), C(47, 49), C(49, 45), C(45, 43), C(43, 45),
       C(45, 40, h=46, l=38),                     # 5: OB candle 38..46
       C(40, 52), C(52, 62), C(62, 70, h=72), C(70, 68), C(68, 64), C(64, 58), C(58, 52),
       C(52, 47, l=44), C(47, 55), C(55, 62), C(62, 69), C(69, 75), C(75, 73), C(73, 80)]
CONCEPTS["order_block"] = dict(candles=_ob, ann=[
    ("rect", 5, 19.6, 38, 46, BLUE, "Order Block – أوردر بلوك"),
    ("arrow", 13, 44, "رجوع للبلوك")])

# Liquidity sweep of equal lows: wick below, close back above, then rally.
_ls = [C(60, 55), C(55, 50), C(50, 46, l=40), C(46, 52), C(52, 56), C(56, 51),
       C(51, 45, l=40.3), C(45, 50), C(50, 54), C(54, 49), C(49, 44),
       C(44, 47, h=48, l=33),                     # 11: sweep wick
       C(47, 55), C(55, 62), C(62, 60), C(60, 67), C(67, 73), C(73, 71), C(71, 77), C(77, 82)]
CONCEPTS["liquidity_sweep"] = dict(candles=_ls, ann=[
    ("hline", 2, 13, 40, GOLD, "سيولة تحت القيعان المتساوية"),
    ("arrow", 11, 33, "Liquidity Sweep")])
CONCEPTS["liquidity_sweep_high"] = dict(candles=mirror(_ls), ann=[
    ("hline", 2, 13, 60, GOLD, "سيولة فوق القمم المتساوية"),
    ("arrow_dn", 11, 67, "Liquidity Sweep")])

# Support / resistance range.
_sr = [C(40, 48), C(48, 56), C(56, 62, h=66), C(62, 55), C(55, 47), C(47, 38, l=34), C(38, 45),
       C(45, 54), C(54, 61, h=65.5), C(61, 52), C(52, 44), C(44, 37, l=34.5), C(37, 46), C(46, 55),
       C(55, 60, h=65.8), C(60, 51), C(51, 42), C(42, 38, l=34.2), C(38, 47), C(47, 53)]
CONCEPTS["support_resistance"] = dict(candles=_sr, ann=[
    ("zone", 0, 19.6, 63.5, 66.5, DN, "مقاومة"), ("zone", 0, 19.6, 33.5, 36.5, UP, "دعم")])

# Bullish engulfing after a decline.
_eng = [C(75, 70), C(70, 66), C(66, 68), C(68, 62), C(62, 57), C(57, 59), C(59, 53), C(53, 48),
        C(48, 44, l=42), C(43, 51, h=52, l=42), C(51, 56), C(56, 54), C(54, 60), C(60, 65),
        C(65, 63), C(63, 68), C(68, 72), C(72, 70), C(70, 75), C(75, 78)]
CONCEPTS["engulfing"] = dict(candles=_eng, ann=[
    ("rect", 7.6, 9.4, 40.5, 53.5, GOLD, ""), ("arrow", 9, 40.5, "ابتلاع شرائي")])

# Pin bar / hammer with long lower wick at a support zone.
_pin = [C(70, 66), C(66, 62), C(62, 64), C(64, 58), C(58, 54), C(54, 56), C(56, 50), C(50, 47),
        C(47, 49, h=50, l=36), C(49, 54), C(54, 58), C(58, 56), C(56, 61), C(61, 66), C(66, 64),
        C(64, 69), C(69, 73), C(73, 71), C(71, 76), C(76, 79)]
CONCEPTS["pin_bar"] = dict(candles=_pin, ann=[
    ("zone", 0, 19.6, 36, 40, UP, "منطقة دعم"), ("arrow", 8, 36, "بن بار – ذيل طويل")])

# ---- numbered key candles + legend (owner, 25 Nov 2026: name each candle and what it does) ----
CONCEPTS["choch"]["ann"] += [("mark_dn", 9, 38, "1"), ("mark", 14, 72, "2")]
CONCEPTS["bos"]["ann"] += [("mark", 6, 54, "1"), ("mark", 11, 64, "2")]
CONCEPTS["order_block"]["ann"] += [("mark", 5, 47, "1"), ("mark", 6, 54, "2"), ("mark", 13, 54, "3")]
CONCEPTS["liquidity_sweep"]["ann"] += [("mark", 6, 53, "1"), ("mark", 11, 48, "2"), ("mark", 12, 57, "3")]
CONCEPTS["liquidity_sweep_high"]["ann"] += [("mark", 6, 59.7, "1"), ("mark_dn", 11, 47, "2"), ("mark_dn", 12, 41, "3")]
CONCEPTS["support_resistance"]["ann"] += [("mark_dn", 2, 54, "1"), ("mark", 5, 49, "2")]
CONCEPTS["engulfing"]["ann"] += [("mark", 8, 55, "1"), ("mark", 9, 59, "2")]
CONCEPTS["pin_bar"]["ann"] += [("mark", 8, 50, "1"), ("mark", 9, 56, "2")]

LEGEND = {
    "fvg": ["شمعة قبل الحركة: قمتها بداية الفجوة",
            "الشمعة القوية: هي اللي بتعمل الفراغ",
            "الشمعة بعدها: قاعها نهاية الفجوة"],
    "fvg_bear": ["شمعة قبل الهبوط: قاعها بداية الفجوة",
                 "الشمعة الهابطة القوية: بتعمل الفراغ",
                 "الشمعة بعدها: قمتها نهاية الفجوة"],
    "choch": ["آخر قاع أدنى (LL): الاتجاه لسا هابط",
              "شمعة الكسر: بتسكّر فوق آخر قمة أدنى"],
    "bos": ["شمعة الكسر: بتسكّر فوق القمة السابقة",
            "كسر تاني: الاتجاه الصاعد عم يكمّل"],
    "order_block": ["آخر شمعة هابطة قبل الصعود = البلوك",
                    "شمعة الاندفاع: بتبيّن قوة الحركة",
                    "رجوع السعر لمنطقة البلوك"],
    "liquidity_sweep": ["قيعان متساوية: تحتها أوامر ستوب",
                        "شمعة السحب: ذيل تحت وتسكير فوق",
                        "شمعة الارتداد بعد السحب"],
    "liquidity_sweep_high": ["قمم متساوية: فوقها أوامر ستوب",
                             "شمعة السحب: ذيل فوق وتسكير تحت",
                             "شمعة النزول بعد السحب"],
    "support_resistance": ["لمسة المقاومة: السعر رجع نزل",
                           "لمسة الدعم: السعر رجع طلع"],
    "engulfing": ["شمعة هابطة صغيرة: البيع عم يضعف",
                  "شمعة صاعدة بتبلع جسم اللي قبلها"],
    "pin_bar": ["بن بار: ذيل طويل تحت وجسم صغير",
                "شمعة بعدها: بتسكّر أعلى وبتأكد الرفض"],
}


# ---- CANDLESTICK PATTERNS (owner, 27 Nov 2026: "أشكال الشموع وأسمائهم") ----
# Each: decline (or rise) into the pattern, pattern candles highlighted + numbered, then reaction.
_DOWN = [C(75, 71), C(71, 67), C(67, 69), C(69, 63), C(63, 59), C(59, 61), C(61, 55), C(55, 50)]
_UPAFTER = [C(56, 61), C(61, 59), C(59, 64), C(64, 69), C(69, 67), C(67, 72), C(72, 76)]


def _bull(pattern, lo, hi, marks, label, after_from=None):
    """Bullish reversal at the bottom of a decline. pattern starts at index 8."""
    cs = _DOWN + pattern
    start = after_from if after_from is not None else pattern[-1][3]
    shift = start - _UPAFTER[0][0]
    cs += [(o + shift, h + shift, l + shift, c + shift) for o, h, l, c in _UPAFTER]
    cs = cs[:20]
    n = len(pattern)
    ann = [("rect", 7.6, 7.4 + n, lo, hi, GOLD, ""), ("arrow", 7 + (n + 1) / 2, lo, label)]
    ann += [(m[0], 8 + k, m[1], str(k + 1)) for k, m in enumerate(marks)]
    if n == 1:  # single-candle pattern: number the confirmation candle too
        ann.append(("mark", 9, cs[9][1], "2"))
    # zoom in: keep 4 candles before the pattern and ~4 after, so the pattern is big
    cut = 4
    cs = cs[cut:8 + n + 4]
    ann = [(a[0], a[1] - cut, a[2] - cut) + a[3:] if a[0] == "rect" else (a[0], a[1] - cut) + a[2:] for a in ann]
    return dict(candles=cs, ann=ann)


def _bear(d):
    """Mirror a bullish pattern into the bearish version (top of a rise)."""
    out = dict(candles=mirror(d["candles"]), ann=[])
    for a in d["ann"]:
        if a[0] == "rect":
            out["ann"].append(("rect", a[1], a[2], 100 - a[4], 100 - a[3], a[5], a[6]))
        elif a[0] == "arrow":
            out["ann"].append(("arrow_dn", a[1], 100 - a[2], a[3]))
        elif a[0] in ("mark", "mark_dn"):
            out["ann"].append(("mark_dn" if a[0] == "mark" else "mark", a[1], 100 - a[2], a[3]))
    return out


CONCEPTS["hammer"] = _bull([C(50, 52, h=53, l=38)], 36, 55, [("mark", 53)], "هامر")
CONCEPTS["inverted_hammer"] = _bull([C(50, 52, h=63, l=49)], 47, 65, [("mark", 63)], "هامر مقلوب")
CONCEPTS["doji"] = _bull([C(50, 50.3, h=56, l=44)], 42, 58, [("mark", 56)], "دوجي")
CONCEPTS["morning_star"] = _bull([C(55, 46, h=56, l=45), C(45, 46, h=48, l=42), C(46, 54, h=55, l=45)],
                                 40, 58, [("mark", 56), ("mark", 48), ("mark", 55)], "نجمة الصباح")
CONCEPTS["harami_bull"] = _bull([C(56, 45, h=57, l=44), C(47, 51, h=52, l=46)], 42, 59,
                                [("mark", 57), ("mark", 52)], "هارامي شرائي")
CONCEPTS["tweezer_bottom"] = _bull([C(52, 46, h=53, l=42), C(46, 52, h=53, l=42)], 40, 55,
                                   [("mark", 53), ("mark", 53)], "قاع الملقط")
CONCEPTS["three_white_soldiers"] = _bull([C(49, 54, h=55, l=48), C(53, 59, h=60, l=52), C(58, 64, h=65, l=57)],
                                         46, 67, [("mark", 55), ("mark", 60), ("mark", 65)], "الجنود الثلاثة")
CONCEPTS["marubozu_bull"] = _bull([C(49, 61, h=61, l=49)], 47, 63, [("mark", 61)], "ماروبوزو صاعدة")
CONCEPTS["shooting_star"] = _bear(_bull([C(50, 48, h=51, l=37)], 35, 53, [("mark", 51)], "نجمة ساقطة"))
CONCEPTS["hanging_man"] = _bear(_bull([C(50, 52, h=63, l=49)], 47, 65, [("mark", 63)], "الرجل المشنوق"))
CONCEPTS["evening_star"] = _bear(_bull([C(55, 46, h=56, l=45), C(45, 46, h=48, l=42), C(46, 54, h=55, l=45)],
                                       40, 58, [("mark", 56), ("mark", 48), ("mark", 55)], "نجمة المساء"))
CONCEPTS["engulfing_bear"] = _bear(_bull([C(48, 46, h=49, l=45), C(45, 53, h=54, l=44)], 42, 56,
                                         [("mark", 49), ("mark", 54)], "ابتلاع بيعي"))
CONCEPTS["three_black_crows"] = _bear(_bull([C(49, 54, h=55, l=48), C(53, 59, h=60, l=52), C(58, 64, h=65, l=57)],
                                            46, 67, [("mark", 55), ("mark", 60), ("mark", 65)], "الغربان الثلاثة"))
CONCEPTS["tweezer_top"] = _bear(_bull([C(52, 46, h=53, l=42), C(46, 52, h=53, l=42)], 40, 55,
                                      [("mark", 53), ("mark", 53)], "قمة الملقط"))

LEGEND.update({
    "hammer": ["هامر: ذيل طويل تحت وجسم صغير فوق", "شمعة التأكيد: بتسكّر أعلى من الهامر"],
    "inverted_hammer": ["هامر مقلوب: ذيل طويل فوق وجسم صغير", "شمعة التأكيد: بتسكّر أعلى"],
    "doji": ["دوجي: فتح وسكّر تقريباً على نفس السعر", "الشمعة بعدها بتحدد مين ربح"],
    "morning_star": ["شمعة هابطة كبيرة", "شمعة صغيرة: البيع عم يتعب", "شمعة صاعدة قوية: ممكن انعكاس لفوق"],
    "harami_bull": ["شمعة هابطة كبيرة", "شمعة صغيرة جوّا جسم اللي قبلها: الزخم ضعف"],
    "tweezer_bottom": ["قاع أول", "قاع تاني على نفس المستوى: رفض للنزول"],
    "three_white_soldiers": ["شمعة صاعدة أولى", "التانية بتسكّر أعلى", "التالتة كمان: زخم شرائي واضح"],
    "marubozu_bull": ["ماروبوزو: جسم كامل بلا ذيول تقريباً", "الصعود بيكمّل بعدها"],
    "shooting_star": ["نجمة ساقطة: ذيل طويل فوق بعد صعود", "شمعة التأكيد: بتسكّر أدنى"],
    "hanging_man": ["الرجل المشنوق: ذيل طويل تحت بعد صعود", "شمعة التأكيد: بتسكّر أدنى"],
    "evening_star": ["شمعة صاعدة كبيرة", "شمعة صغيرة: الشراء عم يتعب", "شمعة هابطة قوية: ممكن انعكاس لتحت"],
    "engulfing_bear": ["شمعة صاعدة صغيرة: الشراء عم يضعف", "شمعة هابطة بتبلع جسم اللي قبلها"],
    "three_black_crows": ["شمعة هابطة أولى", "التانية بتسكّر أدنى", "التالتة كمان: زخم بيعي واضح"],
    "tweezer_top": ["قمة أولى", "قمة تانية على نفس المستوى: رفض للصعود"],
})


# ---- SVG ----
W, H = 888, 640
PAD_T, PAD_B, PAD_L, PAD_R = 100, 115, 26, 26


def svg(concept):
    d = CONCEPTS[concept]
    cs = d["candles"]
    n = len(cs)
    lo = min(c[2] for c in cs) - 6
    hi = max(c[1] for c in cs) + 8
    step = (W - PAD_L - PAD_R) / n
    bw = step * 0.62

    def X(i):
        return PAD_L + step * (i + 0.5)

    def Y(p):
        return PAD_T + (hi - p) / (hi - lo) * (H - PAD_T - PAD_B)

    out = [f"<svg width={W} height={H} viewBox='0 0 {W} {H}' xmlns='http://www.w3.org/2000/svg'>"]
    for k in range(1, 6):  # grid
        y = PAD_T + k * (H - PAD_T - PAD_B) / 6
        out.append(f"<line x1=0 x2={W} y1={y:.0f} y2={y:.0f} stroke='rgba(255,255,255,.05)'/>")
    ann_bg, ann_fg = [], []
    for a in d["ann"]:
        kind = a[0]
        if kind in ("rect", "zone"):
            _, i0, i1, p0, p1, col, lab = a
            x0 = X(i0) - step * 0.5 if kind == "rect" else PAD_L
            x1 = X(min(i1, n - 1)) + step * 0.5 if kind == "rect" else W - PAD_R
            y0, y1 = Y(max(p0, p1)), Y(min(p0, p1))
            ann_bg.append(f"<rect x={x0:.0f} y={y0:.0f} width={x1 - x0:.0f} height={y1 - y0:.0f} rx=6 "
                          f"fill='{col}' fill-opacity=.18 stroke='{col}' stroke-opacity=.8 stroke-width=2/>")
            if lab:
                ty = y0 - 14 if kind == "rect" else (y0 - 12 if p0 > 50 else y1 + 36)
                ann_fg.append(f"<text x={x1 - 6:.0f} y={ty:.0f} fill='{col}' font-size=30 font-weight=800 text-anchor=start direction=rtl>{lab}</text>")
        elif kind == "hline":
            _, i0, i1, p, col, lab = a
            y = Y(p)
            ann_bg.append(f"<line x1={X(i0) - step * .4:.0f} x2={X(i1) + step * .5:.0f} y1={y:.0f} y2={y:.0f} stroke='{col}' stroke-width=3 stroke-dasharray='12 9'/>")
            ann_fg.append(f"<text x={X(i1) + step * .5:.0f} y={y + 40:.0f} fill='{col}' font-size=30 font-weight=800 text-anchor=start direction=rtl>{lab}</text>")
        elif kind == "trend":
            _, pts, col = a
            path = " ".join(f"{X(i):.0f},{Y(p):.0f}" for i, p in pts)
            ann_bg.append(f"<polyline points='{path}' fill=none stroke='{col}' stroke-opacity=.55 stroke-width=3 stroke-dasharray='4 8'/>")
        elif kind in ("label", "label_dn"):
            _, i, p, t, col = a
            y = Y(p) - 14 if kind == "label" else Y(p) + 36
            ann_fg.append(f"<text x={X(i):.0f} y={y:.0f} fill='{col}' font-size=26 font-weight=700 text-anchor=middle>{t}</text>")
        elif kind == "mark":
            _, i, p, t = a
            ann_fg.append(f"<circle cx={X(i):.0f} cy={Y(p) - 32:.0f} r=19 fill='{GOLD}' style='stroke:none'/>"
                          f"<text x={X(i):.0f} y={Y(p) - 23:.0f} fill='#0B0F14' style='stroke:none' font-size=26 font-weight=800 text-anchor=middle>{t}</text>")
        elif kind == "mark_dn":
            _, i, p, t = a
            ann_fg.append(f"<circle cx={X(i):.0f} cy={Y(p) + 32:.0f} r=19 fill='{GOLD}' style='stroke:none'/>"
                          f"<text x={X(i):.0f} y={Y(p) + 41:.0f} fill='#0B0F14' style='stroke:none' font-size=26 font-weight=800 text-anchor=middle>{t}</text>")
        elif kind in ("arrow", "arrow_dn"):
            _, i, p, t = a
            x = X(i)
            if kind == "arrow":  # arrow pointing up at a low, label below
                y = Y(p) + 10
                ann_fg.append(f"<path d='M{x:.0f},{y:.0f} l-14,26 h9 v34 h10 v-34 h9 z' fill='{GOLD}'/>")
                if t:
                    ann_fg.append(f"<text x={x:.0f} y={y + 96:.0f} fill='{GOLD}' font-size=28 font-weight=800 text-anchor=middle direction=rtl>{t}</text>")
            else:  # arrow pointing down at a high, label above
                y = Y(p) - 10
                ann_fg.append(f"<path d='M{x:.0f},{y:.0f} l-14,-26 h9 v-34 h10 v34 h9 z' fill='{GOLD}'/>")
                if t:
                    ann_fg.append(f"<text x={x:.0f} y={y - 76:.0f} fill='{GOLD}' font-size=28 font-weight=800 text-anchor=middle direction=rtl>{t}</text>")
    out.append("<g class=ann>" + "".join(ann_bg) + "</g>")
    for i, (o, h, l, c) in enumerate(cs):
        col = UP if c >= o else DN
        x = X(i)
        top, bot = Y(max(o, c)), Y(min(o, c))
        out.append(f"<line x1={x:.1f} x2={x:.1f} y1={Y(h):.1f} y2={Y(l):.1f} stroke='{col}' stroke-width=3/>"
                   f"<rect x={x - bw / 2:.1f} y={top:.1f} width={bw:.1f} height={max(bot - top, 3):.1f} rx=3 fill='{col}'/>")
    halo = "<g class=ann style='paint-order:stroke;stroke:#0E1218;stroke-width:9px;stroke-linejoin:round'>"
    out.append(halo + "".join(ann_fg) + "</g>")
    out.append(f"<text x={W - 18} y=40 fill='{MUTED}' font-size=24 text-anchor=start direction=rtl>مثال للتوضيح فقط · بيانات افتراضية</text>")
    out.append("</svg>")
    return "".join(out).replace("/>", " />")


CSS_EXTRA = """
.wrap{inset:90px 96px 110px}
.kicker{margin-top:40px}
.title{font-size:80px;margin-top:20px;line-height:1.22}
.panel{margin-top:34px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:28px;overflow:hidden;direction:ltr}
.panel svg{display:block;font-family:C}
.legend{margin-top:26px;display:flex;flex-direction:column;gap:12px}
.legend .row{display:flex;align-items:center;gap:18px;font-size:33px;font-weight:700;color:#E8EAED;line-height:1.3}
.legend .n{flex:none;width:44px;height:44px;border-radius:50%;background:#F2C14E;color:#0B0F14;font-weight:800;font-size:28px;display:flex;align-items:center;justify-content:center}
.body{margin-top:24px;font-size:36px;line-height:1.55}
.cta{font-size:38px;padding:24px 56px}
"""
HIDE = ".body,.cta,.ann,.legend{visibility:hidden}" if os.environ.get("HIDE_BODY") else ""


def main(spec_path, out):
    st = json.loads(pathlib.Path(spec_path).read_text(encoding="utf-8"))["story"]
    out = pathlib.Path(out).resolve(); out.mkdir(parents=True, exist_ok=True)
    e = rs.e
    items = st.get("legend") or LEGEND.get(st["chart"], [])
    legend = "".join(f"<div class=row><span class=n>{k}</span><span>{e(t)}</span></div>" for k, t in enumerate(items, 1))
    doc = (f"<html><head><meta charset=utf-8><style>{rs.CSS}{CSS_EXTRA}{HIDE}.chart{{display:none}}</style></head>"
           f"<body style='--w:1080px;--h:1920px;--ts:80px;--bs:38px;--ch:0px'>"
           f"<div class=grid></div><div class=glow></div>"
           f"<div class=wrap><div class=brand><div class=dot></div>Sisco<span>Hub</span></div>"
           f"<div class=kicker>{e(st['kicker'])}</div><div class=title>{rs.title(st['title'])}</div>"
           f"<div class=panel>{svg(st['chart'])}</div>"
           f"<div class=legend>{legend}</div>"
           f"<div class=body>{e(st['body'])}</div><div class=cta>{e(st['cta'])}</div></div>"
           f"<div class=disc>محتوى تعليمي فقط · ليس نصيحة مالية</div></body></html>")
    f = out / "story.html"; f.write_text(doc, encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(f.as_uri()); pg.wait_for_timeout(600)
        over = pg.evaluate("document.querySelector('.cta').getBoundingClientRect().bottom")
        pg.screenshot(path=str(out / "story.png")); b.close()
    f.unlink()
    if over > 1830:
        print(f"WARNING: layout overflow (cta bottom {over:.0f}px > 1830) — shorten title/body", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
