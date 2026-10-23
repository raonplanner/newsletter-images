#!/usr/bin/env python3
"""소식지 메일 본문 생성기.
사용: python3 -I tools/mail_html.py 입력.json 출력폴더 [이미지주소]
입력 JSON은 render.py와 같은 형식에 "greeting"(인사말 한 줄)을 더한다.
출력: 출력폴더/mail.html (Gmail htmlBody), mail.txt (일반 텍스트 body).
Gmail 도구는 외부 <img>와 style의 'background:' 줄임 표기를 지우므로
이미지 없이 표로 그리고, 배경색은 bgcolor 속성과 background-color 로만 넣는다.
"""
import sys, os, json, html

NAVY, GREEN, BROWN, RED = "#12294d", "#0e6b4f", "#7a4a12", "#c8102e"
DIR = {"up": ("▲ ", "#fbc9cc", RED), "down": ("▼ ", "#c3d8f8", "#1553b0"), "flat": ("", "#e6ebf5", "#6e7887")}
CONSULT = "https://brand.metlife.co.kr/bo/prps/selectMoblieCert.do?fccd=00323294"
ROWS = [("증시", NAVY, [("코스피", "kospi"), ("나스닥100", "ndx")]),
        ("환율", GREEN, [("달러 (1달러)", "usd"), ("엔 (100엔)", "jpy")]),
        ("유가", BROWN, [("WTI", "wti")])]
TAGS = {"medical": "오늘의 코너 · 의료계 소식", "news": "오늘의 코너 · 중요 경제기사", "quote": "오늘의 명언"}


def esc(t): return html.escape(str(t))


def bg(c): return f'bgcolor="{c}" style="background-color:{c};'


def table_html(r):
    th = "".join(f'<th {bg(NAVY)}color:#ffffff;font-size:13px;padding:6px{";text-align:right" if t == "종가" else ""}">{t}</th>'
                 for t in ("구분", "지표", "종가", "전일 대비"))
    out = [f"<tr>{th}</tr>"]
    for gi, (group, color, items) in enumerate(ROWS):
        last_group = gi == len(ROWS) - 1
        for i, (name, key) in enumerate(items):
            x = r[key]
            arrow, cbg, cfg = DIR[x.get("dir", "flat")]
            line = "" if last_group and i == len(items) - 1 else (
                "border-bottom:2px solid #ffffff" if i == len(items) - 1 else "border-bottom:1px solid #e6ebf5")
            g = (f'<td rowspan="{len(items)}" {bg(color)}color:#ffffff;text-align:center;font-weight:bold;padding:8px;'
                 f'border-bottom:2px solid #ffffff">{group}</td>') if i == 0 else ""
            out.append(f'<tr>{g}<td style="padding:8px;font-weight:bold;{line}">{esc(name)}</td>'
                       f'<td style="padding:8px;text-align:right;font-weight:bold;font-size:18px;{line}">{esc(x["v"])}</td>'
                       f'<td {bg(cbg)}padding:8px;text-align:center;font-weight:bold;color:{cfg};border-bottom:2px solid #ffffff">'
                       f'{arrow}{esc(x["c"])}</td></tr>')
    return ('<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-top:10px;font-size:16px">'
            + "\n".join(out) + "</table>")


def corner_html(c):
    tag = (f'<div style="text-align:center"><span style="display:inline-block;background-color:{RED};color:#ffffff;'
           f'font-size:13px;font-weight:bold;padding:3px 12px;border-radius:12px">{TAGS[c["type"]]}</span></div>')
    if c["type"] == "quote":
        body = (f'<p style="margin:10px 0 4px;font-size:16px;line-height:1.5;text-align:center;color:{NAVY};font-weight:bold">'
                f'“{esc(c["quote"])}”</p><p style="margin:4px 0;font-size:14px;text-align:center;color:#4a5568">— {esc(c["who"])}</p>')
    else:
        body = "".join(f'<p style="margin:8px 0 4px;font-size:14px;line-height:1.5"><b style="color:{NAVY}">{esc(i["h"])}</b>'
                       f' — {esc(i["b"])}</p>' for i in c["items"])
    close = f'<p style="margin:6px 0 0;font-size:13px;text-align:center;color:#3a4659">{esc(c["close"])}</p>' if c.get("close") else ""
    return f'<div style="margin-top:12px;border:2px solid {NAVY};border-radius:10px;padding:12px 14px">{tag}{body}{close}</div>'


def corner_text(c):
    if c["type"] == "quote":
        lines = [f'"{c["quote"]}" - {c["who"]}']
    else:
        lines = [f'· {i["h"]} — {i["b"]}' for i in c["items"]]
    if c.get("close"): lines.append(c["close"])
    return f'■ {TAGS[c["type"]].replace("오늘의 코너 · ", "오늘의 코너(")}{")" if c["type"] != "quote" else ""}\n' + "\n".join(lines)


def text_rows(r):
    unit = {"kospi": "%", "ndx": "%", "usd": "원", "jpy": "원", "wti": "달러"}
    out = []
    for _, _, items in ROWS:
        for name, key in items:
            x = r[key]
            arrow = DIR[x.get("dir", "flat")][0].strip()
            c = x["c"] if x["c"].endswith("%") or x["c"] == "-" else x["c"] + unit[key]
            out.append(f'{name.replace(" (1달러)", "").replace("달러", "원/달러") if key == "usd" else name} {x["v"]} ({arrow}{c})')
    return "\n".join(out)


def main():
    inp, out = sys.argv[1], sys.argv[2]
    img = sys.argv[3] if len(sys.argv) > 3 else ""
    d = json.load(open(inp, encoding="utf8"))
    os.makedirs(out, exist_ok=True)
    sub_html = (f'<div style="font-size:15px;font-weight:bold;margin-top:4px;color:#ffd666">{esc(d["subtitle"])}</div>'
                if d.get("subtitle") else "")
    head = (f'<table width="100%" cellpadding="0" cellspacing="0" {bg(NAVY)}border-collapse:collapse;color:#ffffff">'
            f'<tr><td {bg(NAVY)}padding:14px 18px"><div style="font-size:13px;color:#c9d6ee">{esc(d["date_label"])} · 전일 마감 기준</div>'
            f'<div style="font-size:26px;font-weight:bold;margin-top:2px;color:#ffffff">오늘의 소식지</div>{sub_html}</td>'
            f'<td {bg(NAVY)}padding:14px 18px;text-align:right;font-size:12px;color:#c9d6ee;line-height:1.5">'
            f'<b style="font-size:15px;color:#ffffff">송근영 Mentor</b><br>메트라이프금융서비스(주) 중부직할지점<br>m. 010-3224-1517</td></tr></table>')
    link = (f'<p style="font-size:14px;margin:4px 0"><a href="{esc(img)}">소식지 이미지(나스닥100 장기 추이 차트 포함) 크게 보기</a></p>'
            if img else "")
    page = (f'<div style="max-width:560px;margin:0 auto;font-family:\'Apple SD Gothic Neo\',\'Malgun Gothic\',sans-serif;color:#1b2433">'
            f'{head}{table_html(d["rows"])}{corner_html(d["corner"])}'
            f'<p style="font-size:14px;margin:14px 0 4px">{esc(d["greeting"])}</p>{link}'
            f'<p style="font-size:14px;margin:10px 0 4px">상담 문의 010-3224-1517<br>상담 신청 <a href="{CONSULT}">{CONSULT}</a></p>'
            f'<p style="font-size:11px;color:#6a7587;margin-top:10px">{esc(d["src"])}<br>※ 본 자료는 정보 제공용입니다.</p></div>')
    text = (f'오늘의 소식지 {d["date_label"]} (전일 마감 기준)\n' + (f'{d["subtitle"]}\n' if d.get("subtitle") else '') + f'\n{d["greeting"]}\n\n■ 전일 주요 경제동향\n{text_rows(d["rows"])}\n\n'
            f'{corner_text(d["corner"])}\n\n' + (f"소식지 이미지: {img}\n\n" if img else "")
            + f'상담 문의 010-3224-1517\n상담 신청 {CONSULT}\n\n※ 본 자료는 정보 제공용입니다.\n')
    open(os.path.join(out, "mail.html"), "w", encoding="utf8").write(page)
    open(os.path.join(out, "mail.txt"), "w", encoding="utf8").write(text)
    print(f"mail.html {len(page)}자, mail.txt {len(text)}자")


main()
