#!/usr/bin/env python3
"""소식지 메일 본문 생성기 (고객 메일: 링크·이미지 없음).
사용: python3 -I tools/mail_html.py 입력.json 출력폴더
입력 JSON 형식은 tools/nl.py 머리말 참고.
출력: 출력폴더/mail.html (Gmail htmlBody), mail.txt (일반 텍스트 body).
Gmail 도구는 외부 <img>와 style의 'background:' 줄임 표기를 지우고, 모든 링크를 구글 리디렉션 경유 주소로 바꿔
'리디렉션 알림' 경고창이 뜨게 하므로 이미지·링크 없이 표로만 그리고, 배경색은 bgcolor 속성과 background-color 로만 넣는다.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nl import *

BORDER = "border-collapse:collapse;border:1px solid #cfd6e4"
GAP = '<div style="height:16px;line-height:16px;font-size:0">&nbsp;</div>'


def bg(c): return f'bgcolor="{c}" style="background-color:{c};'


def block(title, color, body, body_bg=None, sub=None, risk=False, note=None):
    """제목 띠가 있는 상자 하나."""
    sub_html = f' <span style="font-weight:normal;font-size:12px;color:#e6eef5">· {esc(sub)}</span>' if sub else ""
    bb = f"{bg(body_bg)}" if body_bg else 'style="'
    rows = (f'<tr><td {bg(color)}color:#ffffff;font-size:14px;font-weight:bold;padding:8px 12px">{esc(title)}{sub_html}</td></tr>'
            f'<tr><td {bb}padding:12px;font-size:14px;line-height:1.7;word-break:keep-all">{body}'
            + (f'<br><span style="font-size:12px;color:#5a6577">{esc(note)}</span>' if note else "") + "</td></tr>")
    if risk:
        rows += (f'<tr><td {bg("#f6f8fb")}padding:10px 12px;font-size:12px;line-height:1.7;color:#3a4659;border-top:1px solid #cfd6e4">'
                 f'<b>{RISK_T}</b><br>{esc(RISK_B)}</td></tr>')
    return f'<table width="100%" cellpadding="0" cellspacing="0" style="{BORDER}">{rows}</table>{GAP}'


def cell_html(c):
    k = c.get("kind", "text")
    color = color_of(c.get("color", "teal"))
    bb = BODY_BG.get(c.get("color"))
    if k == "cal":
        trs = []
        for n, i in enumerate(c["items"]):
            line = "" if n == len(c["items"]) - 1 else "border-bottom:1px solid #e3e8f1"
            sub = f'<br><span style="font-size:12px;color:#5a6577">{esc(i["s"])}</span>' if i.get("s") else ""
            trs.append(f'<tr><td valign="top" style="padding:10px 12px;font-size:14px;font-weight:bold;white-space:nowrap;{line}">{esc(i["d"])}</td>'
                       f'<td valign="top" style="padding:10px 12px;font-size:14px;line-height:1.6;word-break:keep-all;{line}">{esc(i["t"])}{sub}</td></tr>')
        risk = (f'<tr><td colspan="2" {bg("#f6f8fb")}padding:10px 12px;font-size:12px;line-height:1.7;color:#3a4659;border-top:1px solid #cfd6e4">'
                f'<b>{RISK_T}</b><br>{esc(RISK_B)}</td></tr>') if c.get("risk") else ""
        return (f'<table width="100%" cellpadding="0" cellspacing="0" style="{BORDER}"><tr><td colspan="2" {bg(color)}color:#ffffff;'
                f'font-size:14px;font-weight:bold;padding:8px 12px">{esc(c["title"])}</td></tr>' + "".join(trs) + risk + f"</table>{GAP}")
    if k == "list":
        body = "<br>".join("· " + esc(i) for i in c["items"])
    else:
        body = esc(c["body"]).replace("\n\n", "<br><br>").replace("\n", "<br>")
    return block(c["title"], color, body, bb, risk=c.get("risk"), note=c.get("note"))


def tcell(text, align="left", bold=True, size=14, nowrap=True, extra=""):
    w = "white-space:nowrap;" if nowrap else ""
    return f'<td align="{align}" style="padding:12px 10px;font-size:{size}px;font-weight:{"bold" if bold else "normal"};{w}{extra}">{esc(text)}</td>'


def chg_cell(ch, col, bgc, extra=""):
    return (f'<td {bg(bgc)}padding:12px 6px;font-size:14px;font-weight:bold;color:{col};text-align:center;white-space:nowrap;{extra}">'
            f'{esc(ch)}</td>')


def table_block(title, sub, rows, widths, foot=None):
    """rows: [(이름, 값, 등락, 색, 배경, 이름크기)]"""
    cols = "".join(f'<col width="{w}%">' for w in widths)
    trs = []
    for n, (name, val, ch, col, bgc, nsize) in enumerate(rows):
        last = n == len(rows) - 1
        line = "" if last and not foot else "border-bottom:1px solid #e3e8f1;"
        trs.append(f'<tr>{tcell(name, size=nsize, extra=line)}{tcell(val, "right", size=16, extra=line)}{chg_cell(ch, col, bgc, line)}</tr>')
    f = f'<tr><td colspan="3" {bg("#f6f8fb")}padding:10px 12px;font-size:13px;line-height:1.8;color:#3a4659;border-top:1px solid #cfd6e4">{foot}</td></tr>' if foot else ""
    return (f'<table width="100%" cellpadding="0" cellspacing="0" style="{BORDER};table-layout:fixed"><colgroup>{cols}</colgroup>'
            f'<tr><td colspan="3" {bg(NAVY)}color:#ffffff;font-size:14px;font-weight:bold;padding:8px 12px">{esc(title)}'
            f' <span style="font-weight:normal;font-size:12px;color:#c9d6ee">· {esc(sub)}</span></td></tr>' + "".join(trs) + f + f"</table>{GAP}")


def build(d):
    r = d.get("rows") or {}
    h, t = [], []
    # --- 머리글 ---
    sub = (f'<div style="font-size:15px;font-weight:bold;margin-top:4px;color:#ffd666;line-height:1.5">{esc(d["subtitle"])}</div>'
           if d.get("subtitle") else "")
    h.append(f'<table width="100%" cellpadding="0" cellspacing="0" {bg(NAVY)}border-collapse:collapse;color:#ffffff"><tr><td {bg(NAVY)}padding:16px 18px">'
             f'<div style="font-size:13px;color:#c9d6ee;line-height:1.6">{esc(d["date_label"])}<br>{esc(basis_text(d))}</div>'
             f'<div style="font-size:26px;font-weight:bold;margin-top:8px;color:#ffffff">오늘의 소식지</div>'
             f'<div style="font-size:15px;font-weight:bold;margin-top:4px;color:#ffd666">[해외주식 비과세 투자상담]</div>{sub}</td></tr></table>{GAP}')
    t.append(f'오늘의 소식지\n[해외주식 비과세 투자상담]\n' + (d["subtitle"] + "\n" if d.get("subtitle") else "") + f'({d["date_label"]} · {basis_text(d)})')
    g1, g2 = greeting_lines(d)
    h.append(f'<p style="font-size:15px;line-height:1.7;margin:0;word-break:keep-all">{esc(g1)}<br>{esc(g2)}</p>{GAP}')
    t.append(f"{g1} {g2}")
    # --- 한 줄 요약 / 코너 ---
    s = summary(d)
    if s:
        h.append(block("한 줄 요약", COLORS["amber"], esc(s), "#fff9e6").replace("font-size:14px;line-height:1.7", "font-size:15px;line-height:1.7", 1))
        t.append(f"■ 한 줄 요약\n{s}")
    c = d["corner"]
    if c["type"] == "quote":
        body = f'<b style="color:{NAVY}">“{esc(c["quote"])}”</b><br>— {esc(c["who"])}'
    else:
        body = "<br>".join(f'<b style="color:{NAVY}">{esc(i["h"])}</b> — {esc(i["b"])}' for i in c["items"])
    if c.get("close"): body += f'<br><span style="color:#5a6577;font-size:13px">{esc(c["close"])}</span>'
    h.append(block(corner_tag(c), COLORS["red"], body))
    t.append(corner_text(c))
    # --- 당일종가(코스피·환율) ---
    rows = []
    for name, key in (("코스피", "kospi"), ("1달러", "usd"), ("100엔", "jpy")):
        if key in r:
            v, ch, col, bgc = row_view(key, r[key])
            rows.append((name, v, ch, col, bgc, 14))
    if rows:
        foot = None
        k = r.get("kospi")
        if k and not k.get("closed") and k.get("dir") in ("up", "down") and k["c"].endswith("%"):
            try:
                pc = float(k["c"].rstrip("%"))
                after = 100 * (1 + (pc if k["dir"] == "up" else -pc) / 100)
                foot = (f'<b>숫자 쉽게 읽기</b><br>코스피가 {k["c"]} {"올랐다" if k["dir"] == "up" else "내렸다"}는 건, '
                        f'100만 원이 하루 만에 약 {after * 10000:,.0f}원이 됐다는 뜻이에요.')
                foot = foot.replace(f"약 {after * 10000:,.0f}원", "약 " + _man(after * 10000))
            except Exception:
                foot = None
        h.append(table_block("당일종가", "코스피·환율", rows, (30, 40, 30), foot))
        t.append("■ 당일종가 · 코스피·환율\n" + "\n".join((f"{n} 휴장" if v == "휴장" else f"{n} {v} {ch}") for n, v, ch, _, _, _ in rows)
                 + (f"\n{_plain(foot)}" if foot else ""))
    # --- 전일종가(미국 ETF) ---
    el = etf_lines(d)
    if el:
        rows = [(n, v[0], v[1], v[2], v[3], 13) for n, v in el]
        gp = growth_pairs(d)
        foot = None
        if gp:
            foot = (f'<b>15년 누적수익률(환율 반영)</b><br>글로벌IT섹터ETF <b style="color:{UP}">{gp[0]:+.1f}%</b><br>'
                    f'나스닥100ETF <b style="color:{UP if gp[1] > 0 else DOWN}">{gp[1]:+.1f}%</b><br>'
                    f'<span style="font-size:11px;color:#6a7587;line-height:1.6">{DISC}</span>')
        h.append(table_block("전일종가", "미국 증시", rows, (40, 32, 28), foot))
        t.append("■ 전일종가 · 미국 증시\n" + "\n".join((f"{n} 휴장" if v[0] == "휴장" else f"{n} {v[0]} {v[1]}") for n, v in el)
                 + (f"\n15년 누적수익률(환율 반영)\n글로벌IT섹터ETF {gp[0]:+.1f}%\n나스닥100ETF {gp[1]:+.1f}%\n{DISC}" if gp else ""))
    # --- 순환 칸 ---
    for c in d.get("cells") or []:
        h.append(cell_html(c))
        t.append(cell_text(c))
    # --- 자격 / 연락처 ---
    qr = []
    for n, (a, b, lab, val) in enumerate(QUAL):
        line = "" if n == len(QUAL) - 1 else "border-bottom:1px solid #e3e8f1;"
        left = f'{esc(a)}' + (f'<br><span style="font-weight:normal;font-size:11px;color:#5a6577">{esc(b)}</span>' if b else "")
        right = (f'{esc(lab)}<br><b>{esc(val)}</b>' if lab else esc(val))
        qr.append(f'<tr><td valign="top" style="padding:10px 12px;font-size:13px;font-weight:bold;line-height:1.5;{line}">{left}</td>'
                  f'<td valign="top" align="right" style="padding:10px 12px;font-size:13px;line-height:1.5;white-space:nowrap;{line}">{right}</td></tr>')
    h.append(f'<table width="100%" cellpadding="0" cellspacing="0" style="{BORDER}"><tr><td colspan="2" {bg(COLORS["slate"])}color:#ffffff;'
             f'font-size:14px;font-weight:bold;padding:8px 12px">자격</td></tr>' + "".join(qr) + f"</table>{GAP}")
    t.append("■ 자격\n" + "\n".join(f"{a}" + (f" ({b})" if b else "") + " — " + (f"{lab} {val}" if lab else val) for a, b, lab, val in QUAL))
    h.append(f'<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse"><tr><td {bg(NAVY)}color:#ffffff;text-align:center;padding:14px 12px;line-height:1.6">'
             f'<div style="font-size:14px;font-weight:bold">{SIGN}</div><div style="font-size:18px;font-weight:bold;white-space:nowrap">{PHONE}</div>'
             f'<div style="font-size:12px;color:#c9d6ee;margin-top:6px">{REPLY}</div></td></tr></table>')
    t.append(f"{SIGN}\n{PHONE}\n{REPLY}")
    kr_w = "휴장" if d.get("kr_closed") else "마감"
    us_w = "휴장" if d.get("us_closed") else "마감"
    src = f'코스피·환율 {d.get("kr_date", "")} {kr_w} · 미국 {d.get("us_date", "")} {us_w} · 정보 제공용'
    h.append(f'<p style="font-size:11px;line-height:1.6;color:#6a7587;margin:10px 0 0;word-break:keep-all">{esc(src)}<br>※ 본 자료는 정보 제공용이에요. 투자 권유가 아니니 참고만 해주세요.</p>')
    t.append(f"{src}\n※ 본 자료는 정보 제공용이에요. 투자 권유가 아니니 참고만 해주세요.")
    page = ("<div style=\"max-width:560px;margin:0 auto;font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;"
            'color:#1b2433;word-break:keep-all">' + "".join(h) + "</div>")
    return page, "\n\n".join(t) + "\n"


def _man(won):
    """원 단위 금액을 '96만 5천 원' 꼴로."""
    won = int(round(won / 1000.0)) * 1000
    man, rest = divmod(won, 10000)
    return f"{man}만 {rest // 1000}천 원" if rest else f"{man}만 원"


def _plain(html_s):
    import re
    return re.sub(r"<[^>]+>", " ", html_s.replace("<br>", "\n")).replace("  ", " ").strip()


def main():
    inp, out = sys.argv[1], sys.argv[2]
    d = json.load(open(inp, encoding="utf8"))
    os.makedirs(out, exist_ok=True)
    page, text = build(d)
    bad = bad_words(page + text)
    if bad: raise SystemExit(f"고객에게 나가면 안 되는 문구가 있습니다: {bad}")
    open(os.path.join(out, "mail.html"), "w", encoding="utf8").write(page)
    open(os.path.join(out, "mail.txt"), "w", encoding="utf8").write(text)
    print(f"mail.html {len(page)}자, mail.txt {len(text)}자")


main()
