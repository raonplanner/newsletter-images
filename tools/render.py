#!/usr/bin/env python3
"""인스타 2번째 장(소식지) 이미지 생성기.
사용: python3 -I tools/render.py 입력.json 출력폴더   ->  출력폴더/post.png (1080x1350)
입력 JSON 형식은 tools/nl.py 머리말 참고. 내용이 길면 글자를 자동으로 줄여 한 장에 맞춘다.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nl import *
from playwright.sync_api import sync_playwright

CSS = """*{box-sizing:border-box;margin:0;padding:0}
body{width:1080px;height:1350px;font-family:"Noto Sans CJK KR",sans-serif;background:#fff;color:#1b2433;word-break:keep-all;overflow:hidden}
.hd{background:#12294d;color:#fff;padding:20px 40px 16px}
.hd .dt{font-size:22px;color:#c9d6ee;line-height:1.5}
.hd h1{font-size:52px;margin-top:4px}
.hd .t{font-size:27px;font-weight:700;color:#ffd666;margin-top:5px;line-height:1.3}
.box{margin:12px 40px 0;border:2px solid #cfd6e4}
.bt{color:#fff;font-size:25px;font-weight:700;padding:7px 20px}
.bt small{font-weight:400;font-size:21px;opacity:.85;margin-left:8px}
table{width:100%;border-collapse:collapse}
td{padding:7px 18px;font-size:31px;font-weight:700;border-bottom:2px solid #e3e8f1;white-space:nowrap}
td.l{font-size:28px}
td.r{text-align:right;font-size:34px}td.c{text-align:center;width:240px;font-size:31px}
td.k{font-size:27px;font-weight:700;vertical-align:top}td.m{white-space:normal;font-size:27px;font-weight:400;line-height:1.4}
td.m small{font-size:21px;color:#5a6577}
.tx{padding:12px 22px;font-size:27px;line-height:1.5}
.nt{background:#f6f8fb;border-top:2px solid #cfd6e4;padding:9px 22px;font-size:22px;line-height:1.55;color:#3a4659}
.q{background:#3a4659;color:#fff;margin:12px 40px 0;padding:10px 22px;font-size:22px;line-height:1.55}
.q b{font-size:23px}
.bd{background:#12294d;color:#fff;margin:12px 40px 0;text-align:center;padding:12px}
.bd .a{font-size:26px;font-weight:700}.bd .b{font-size:34px;font-weight:700;margin-top:2px}
.src{font-size:19px;color:#6a7587;text-align:center;margin-top:12px;padding-bottom:10px}"""


def cell_box(c):
    color = color_of(c.get("color", "teal"))
    k = c.get("kind", "text")
    if k == "cal":
        inner = "<table>" + "".join(
            f'<tr><td class="k">{esc(i["d"])}</td><td class="m">{esc(i["t"])}' + (f'<br><small>{esc(i["s"])}</small>' if i.get("s") else "") + "</td></tr>"
            for i in c["items"]) + "</table>"
    elif k == "list":
        inner = '<div class="tx">' + "<br>".join("· " + esc(i) for i in c["items"]) + "</div>"
    else:
        inner = f'<div class="tx">{esc(c["body"]).replace(chr(10), "<br>")}</div>'
    risk = f'<div class="nt"><b>{RISK_T}</b><br>{esc(RISK_B)}</div>' if c.get("risk") else ""
    return f'<div class="box"><div class="bt" style="background:{color}">{esc(c["title"])}</div>{inner}{risk}</div>'


def build_html(d, z):
    r = d.get("rows") or {}
    c = d["corner"]
    sub = f'<div class="t">{esc(d["subtitle"])}</div>' if d.get("subtitle") else ""
    if c["type"] == "quote":
        cbody = f'<div class="tx"><b style="color:#12294d">“{esc(c["quote"])}”</b><br>— {esc(c["who"])}</div>'
    else:
        cbody = '<div class="tx">' + "<br>".join(f'<b style="color:#12294d">{esc(i["h"])}</b> — {esc(i["b"])}' for i in c["items"]) + "</div>"
    if c.get("close"): cbody = cbody.replace("</div>", f'<br><span style="font-size:23px;color:#5a6577">{esc(c["close"])}</span></div>', 1)
    out = [f'<div class="hd"><div class="dt">{esc(d["date_label"])}<br>{esc(basis_text(d))}</div><h1>오늘의 소식지</h1>'
           f'<div class="t">[해외주식 비과세 투자상담]</div>{sub}</div>',
           f'<div class="box"><div class="bt" style="background:#c8102e">{esc(corner_tag(c))}</div>{cbody}</div>']
    kr = []
    for name, key in (("코스피", "kospi"), ("1달러", "usd"), ("100엔", "jpy")):
        if key in r:
            v, ch, col, bgc = row_view(key, r[key])
            kr.append(f'<tr><td class="l">{name}</td><td class="r">{esc(v)}</td><td class="c" style="background:{bgc};color:{col}">{esc(ch)}</td></tr>')
    if kr:
        out.append(f'<div class="box"><div class="bt" style="background:#12294d">당일종가<small>· 코스피·환율</small></div><table>{"".join(kr)}</table></div>')
    if "ndx" in r:
        v, ch, col, bgc = row_view("ndx", r["ndx"])
        out.append(f'<div class="box"><div class="bt" style="background:#12294d">전일종가<small>· 미국 증시</small></div><table><tr><td class="l">나스닥100</td>'
                   f'<td class="r">{esc(v)}</td><td class="c" style="background:{bgc};color:{col}">{esc(ch)}</td></tr></table></div>')
    cells = d.get("cells") or []
    if cells:
        out.append(cell_box(cells[min(int(d.get("image_cell", 0)), len(cells) - 1)]))
    out.append(f'<div class="q"><b>자격</b> · 증권투자권유대행인(골든트리투자자문 소속, 등록번호 8217000309)<br>'
               f'변액보험판매관리사(2010.10.28 합격) · 펀드투자상담사(2013.09.27 합격)</div>')
    out.append(f'<div class="bd"><div class="a">{SIGN}</div><div class="b">{PHONE}</div></div>')
    kw = "휴장" if d.get("kr_closed") else "마감"
    uw = "휴장" if d.get("us_closed") else "마감"
    out.append(f'<div class="src">코스피·환율 {esc(d.get("kr_date", ""))} {kw} · 미국 {esc(d.get("us_date", ""))} {uw} · 정보 제공용</div>')
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<div id="z" style="zoom:{z}">{"".join(out)}</div></body></html>')


def main():
    inp, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    d = json.load(open(inp, encoding="utf8"))
    path = os.path.join(out, "page.html")
    with sync_playwright() as p:
        b = p.chromium.launch()
        chosen = None
        for z in (1.0, 0.95, 0.9, 0.85, 0.8):
            open(path, "w", encoding="utf8").write(build_html(d, z))
            pg = b.new_page(viewport={"width": 1080, "height": 1350})
            pg.goto("file://" + os.path.abspath(path))
            bottom = pg.evaluate("document.querySelector('.src').getBoundingClientRect().bottom")
            pg.close()
            if bottom <= 1350.5: chosen = z; break
        if chosen is None:
            raise SystemExit("내용이 길어 한 장에 들어가지 않습니다. 칸 문장을 줄이세요.")
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto("file://" + os.path.abspath(path)); pg.screenshot(path=os.path.join(out, "post.png")); pg.close(); b.close()
    os.remove(path)
    print(f"zoom={chosen} post=1080x1350")


main()
