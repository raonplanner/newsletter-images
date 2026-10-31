#!/usr/bin/env python3
"""소식지 이미지 생성기.
사용: python3 -I tools/render.py 입력.json 출력폴더
출력: 출력폴더/post.png (인스타 1장, 1080x1350 원본), mail.png (메일 첨부용, base64 28,000자 이하), 요약은 stdout.
입력 JSON 형식은 tools/README.md 참고. data/ndx_monthly.csv 의 해당 월 값을 갱신(upsert)한다.
"""
import sys, os, json, csv, math, base64, html
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "data", "ndx_monthly.csv")
PALETTE = [(255,255,255),(18,41,77),(27,36,51),(200,16,46),(21,83,176),(251,201,204),
           (195,216,248),(14,107,79),(122,74,18),(110,120,135),(201,211,230)]
LIMIT = 27500  # 메일 첨부 base64 길이 한도(28,000 미만 여유)

CSS = """*{box-sizing:border-box;margin:0;padding:0}
body{width:1080px;height:1350px;font-family:"Noto Sans CJK KR",sans-serif;background:#fff;overflow:hidden;color:#1b2433}
.wrap{width:1080px;height:1350px;display:flex;flex-direction:column}
header{background:#12294d;color:#fff;padding:22px 40px 18px;display:flex;justify-content:space-between;align-items:flex-end}
header .date{font-size:26px;color:#c9d6ee}
header h1{font-size:50px;font-weight:700;margin-top:4px}header h1 .ttl{font-size:28px;color:#ffd666;margin-left:8px}
header .sub{font-size:28px;font-weight:700;color:#ffd666;margin-top:6px}
header .me{text-align:right;font-size:23px;line-height:1.5;color:#c9d6ee}
header .me b{color:#fff;font-size:30px}
main{flex:1;padding:18px 40px 0}
table{width:100%;border-collapse:collapse;font-size:36px}
th{background:#12294d;color:#fff;font-size:28px;padding:8px 12px;text-align:center}
td{padding:8px 14px;border-bottom:2px solid #fff;text-align:right;font-weight:700}
td.g{color:#fff;text-align:center;font-size:34px;width:140px}
td.g1{background:#12294d}td.g2{background:#0e6b4f}td.g3{background:#7a4a12}
td.n{text-align:left;font-weight:700;background:#fff;font-size:38px}
td.v{background:#fff;font-size:46px}
td.fx{text-align:right;background:#fff;font-size:44px}
td.u{background:#fbc9cc;color:#c8102e;width:250px;font-size:42px}
td.d{background:#c3d8f8;color:#1553b0;width:250px;font-size:42px}
td.f{background:#e6ebf5;color:#6e7887;width:250px;font-size:36px}
tr.sp td{height:16px;padding:0;background:#fff;border:0}
.chart{margin-top:16px;border:3px solid #12294d;border-radius:14px;padding:8px 18px 6px}
.ct{font-size:26px;font-weight:700;color:#12294d}
.corner{margin-top:0;margin-bottom:16px;border:3px solid #12294d;border-radius:14px;padding:14px 24px 12px;text-align:center}
.corner .tag{display:inline-block;background:#c8102e;color:#fff;font-size:24px;font-weight:700;padding:4px 16px;border-radius:20px}
.corner .quote{font-size:32px;line-height:1.45;color:#12294d;font-weight:700;margin-top:12px}
.corner .who{font-size:26px;color:#4a5568;margin-top:6px}
.corner .close{font-size:25px;color:#3a4659;margin-top:6px}
.corner ul{list-style:none;text-align:left;margin-top:10px}
.corner li{font-size:27px;line-height:1.4;color:#1b2433;margin-bottom:6px}
.corner li b{color:#12294d}
.src{font-size:20px;color:#6a7587;text-align:center;padding:14px 0 18px}"""


def esc(t): return html.escape(str(t)).replace("\n", "<br>")


FX = {"usd": "1달러", "jpy": "100엔"}
TAGS = {"quote": "오늘의 명언", "medical": "의료계 소식", "news": "중요 경제기사", "schedule": "오늘의 주요 일정",
        "policy": "개원가·의료 정책", "calendar": "병·의원 경영 달력", "health": "계절 건강", "term": "쉬운 금융 용어"}


def corner_tag(c):
    """코너 꼬리표. "tag"가 있으면 그대로, 없으면 type 으로 정한다."""
    if c.get("tag"): return c["tag"]
    name = TAGS[c["type"]]
    return name if c["type"] == "quote" else f"오늘의 코너 · {name}"


def fx_change(r):
    """환율 변동폭: ▲1.00원 처럼 화살표와 원 단위를 붙인다."""
    c = r["c"]
    return c if c in ("-", "") or c.endswith("원") else c + "원"


def cell(r, fx=False, unit=""):
    d = r.get("dir", "flat")
    arrow = {"up": "▲", "down": "▼", "flat": ""}[d] + ("" if fx or d == "flat" else " ")
    cls = {"up": "u", "down": "d", "flat": "f"}[d]
    return f'<td class="{cls}">{arrow}{esc(fx_change(r) if fx else (r["c"] + unit if unit and not r["c"].endswith(unit) and r["c"] not in ("-", "") else r["c"]))}</td>'


def load_csv():
    with open(CSV, encoding="utf8") as f:
        return [(r["month"], float(r["close"])) for r in csv.DictReader(f)]


def save_csv(rows):
    with open(CSV, "w", encoding="utf8") as f:
        f.write("month,close\n" + "\n".join(f"{m},{v:.2f}" for m, v in rows) + "\n")


def chart_svg(rows, last_label, last_date, H):
    v = [x for _, x in rows]
    W, L, R, T, B = 940, 86, 26, 38, 28
    lo, hi = math.log10(100), math.log10(max(33000, max(v) * 1.08))
    X = lambda i: L + i * (W - L - R) / (len(v) - 1)
    Y = lambda x: T + (hi - math.log10(x)) / (hi - lo) * (H - T - B)
    line = " ".join(f"{X(i):.1f},{Y(x):.1f}" for i, x in enumerate(v))
    area = f"{L},{H-B} " + line + f" {X(len(v)-1):.1f},{H-B}"
    grid = ""
    for g in (100, 1000, 10000):
        grid += (f'<line x1="{L}" y1="{Y(g):.1f}" x2="{W-R}" y2="{Y(g):.1f}" stroke="#c9d3e6" stroke-width="2"/>'
                 f'<text x="{L-8}" y="{Y(g)+8:.1f}" font-size="22" fill="#6e7887" text-anchor="end">{g:,}</text>')
    ip = [i for i, (m, _) in enumerate(rows) if m == "2000-03"]
    peak = ""
    if ip:
        i = ip[0]
        peak = (f'<circle cx="{X(i):.1f}" cy="{Y(v[i]):.1f}" r="6" fill="#7a4a12"/>'
                f'<text x="{X(i)+10:.1f}" y="{Y(v[i])-10:.1f}" font-size="22" fill="#7a4a12" font-weight="700">2000 닷컴 4,398</text>')
    ex, ey = X(len(v) - 1), Y(v[-1])
    return (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">{grid}'
            f'<polygon points="{area}" fill="#c3d8f8"/>'
            f'<polyline points="{line}" fill="none" stroke="#1553b0" stroke-width="4" stroke-linejoin="round"/>{peak}'
            f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="8" fill="#c8102e"/>'
            f'<text x="{ex-14:.1f}" y="{ey-6:.1f}" font-size="26" fill="#c8102e" font-weight="700" text-anchor="end">{esc(last_label)}</text>'
            f'<text x="{L}" y="{H-4}" font-size="22" fill="#6e7887">1985.10</text>'
            f'<text x="{W-R}" y="{H-4}" font-size="22" fill="#6e7887" text-anchor="end">{esc(last_date)}</text></svg>')


def corner_html(c):
    t = c["type"]
    if t == "quote":
        return (f'<div class="corner"><span class="tag">{esc(corner_tag(c))}</span><div class="quote">“{esc(c["quote"])}”</div>'
                f'<div class="who">— {esc(c["who"])}</div><div class="close">{esc(c["close"])}</div></div>')
    tag = esc(corner_tag(c))
    li = "".join(f'<li><b>{esc(i["h"])}</b> — {esc(i["b"])}</li>' for i in c["items"])
    close = f'<div class="close">{esc(c["close"])}</div>' if c.get("close") else ""
    return f'<div class="corner"><span class="tag">{tag}</span><ul>{li}</ul>{close}</div>'


def basis_text(d):
    """맨 위 기준 문구. kr_date/us_date(예 '10/30','10/29')가 있으면 날짜를 밝힌다."""
    kr, us = d.get("kr_date"), d.get("us_date")
    parts = []
    if kr: parts.append(f"코스피·환율 {kr} 종가")
    if us: parts.append(f"미국 증시 {us} 종가")
    return (" · ".join(parts) + " 기준") if parts else "직전 거래일 종가 기준"


def build_html(d, rows, H):
    r = d["rows"]
    ndx = r.get("ndx")
    chart_html = ""
    if ndx:
        last_label = f'{ndx["num"]:,.0f}'
        mmdd = ndx["date"][5:].replace("-", ".")
        svg = chart_svg(rows, last_label, f'{ndx["date"][:4]}.{mmdd}', H)
        chart_html = f'<div class="chart"><div class="ct">나스닥100 상장 이후 추이 (월말 종가, 로그 눈금)</div>{svg}</div>'
    def tr(label, key, g=None, span=1, sp=False):
        x = r[key]
        gcell = f'<td class="g {g}" rowspan="{span}">{label[0]}</td>' if g else ""
        if key in FX:
            return f'<tr>{gcell}<td class="fx" colspan="2">{esc(FX[key])}={esc(x["v"])}</td>{cell(x, fx=True)}</tr>'
        return f'<tr>{gcell}<td class="n">{esc(label[1])}</td><td class="v">{esc(x["v"])}</td>{cell(x, unit="달러" if key == "wti" else "")}</tr>'
    spacer = '<tr class="sp"><td colspan="4"></td></tr>'
    groups = []
    for glabel, gcls, keys in (("증시", "g1", (("코스피", "kospi"), ("나스닥100", "ndx"))),
                               ("환율", "g2", (("", "usd"), ("", "jpy"))),
                               ("유가", "g3", (("국제유가", "wti"),))):
        present = [(n, k) for n, k in keys if k in r]
        if not present: continue
        part = ""
        for i, (n, k) in enumerate(present):
            part += tr((glabel if i == 0 else "", n), k, gcls if i == 0 else None, len(present))
        groups.append(part)
    table = "<table><tr><th>구분</th><th>지표</th><th>종가</th><th>직전 거래일 대비</th></tr>" + spacer.join(groups) + "</table>"
    sub_html = f'<div class="sub">{esc(d["subtitle"])}</div>' if d.get("subtitle") else ""
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="wrap">'
            f'<header><div><div class="date">{esc(d["date_label"])}<br><span style="white-space:nowrap">{esc(basis_text(d))}</span></div><h1>오늘의 소식지 <span class="ttl">[해외주식 비과세 투자상담]</span></h1>{sub_html}</div>'
            f'</header>'
            f'<main>{corner_html(d["corner"])}{table}{chart_html}'
            f'</main><div class="src">{esc(d["src"])}</div></div></body></html>')


def quantize(im):
    p = Image.new("P", (1, 1)); flat = []
    for c in PALETTE: flat += list(c)
    p.putpalette(flat + [0] * (768 - len(flat)))
    return im.convert("RGB").quantize(palette=p, dither=Image.Dither.NONE)


def main():
    inp, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    d = json.load(open(inp, encoding="utf8"))
    rows = load_csv()
    ndx = d["rows"].get("ndx")
    if ndx:
        month = ndx["date"][:7]
        if rows[-1][0] == month: rows[-1] = (month, float(ndx["num"]))
        elif rows[-1][0] < month: rows.append((month, float(ndx["num"])))
        else:
            raise SystemExit("ndx.date 월이 CSV 마지막 월보다 과거입니다.")
    path = os.path.join(out, "page.html")
    with sync_playwright() as p:
        b = p.chromium.launch()
        chosen = None
        for H in (215, 190, 165, 140):
            open(path, "w", encoding="utf8").write(build_html(d, rows, H))
            pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
            pg.goto("file://" + os.path.abspath(path))
            bottom = pg.evaluate("document.querySelector('.src').getBoundingClientRect().bottom")
            pg.close()
            if bottom <= 1350.5:
                chosen = H; break
        if chosen is None:
            raise SystemExit("내용이 길어 한 장에 들어가지 않습니다. 코너 문장을 줄이세요.")
        pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        pg.goto("file://" + os.path.abspath(path)); pg.screenshot(path=os.path.join(out, "post.png")); pg.close()
        b.close()
    if ndx: save_csv(rows)
    os.remove(path)
    print(f"chart_height={chosen} post=1080x1350")


main()
