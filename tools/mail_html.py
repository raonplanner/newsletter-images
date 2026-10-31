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
        ("환율", GREEN, [("1달러", "usd"), ("100엔", "jpy")]),
        ("유가", BROWN, [("국제유가", "wti")])]
FX = ("usd", "jpy")
TAGS = {"quote": "오늘의 명언", "medical": "의료계 소식", "news": "중요 경제기사", "schedule": "오늘의 주요 일정",
        "policy": "개원가·의료 정책", "calendar": "병·의원 경영 달력", "health": "계절 건강", "term": "쉬운 금융 용어"}


def corner_tag(c):
    """코너 꼬리표. "tag"가 있으면 그대로, 없으면 type 으로 정한다."""
    if c.get("tag"): return c["tag"]
    name = TAGS[c["type"]]
    return name if c["type"] == "quote" else f"오늘의 코너 · {name}"


def change(key, x):
    """직전 거래일 대비 문구. 환율은 '▲1.00원', 그 밖은 '▲ 3.52%'."""
    arrow = DIR[x.get("dir", "flat")][0].strip()
    c = x["c"]
    if key in FX:
        return arrow + (c if c in ("-", "") or c.endswith("원") else c + "원")
    return f"{arrow} {c}" if arrow else c


def esc(t): return html.escape(str(t))


def bg(c): return f'bgcolor="{c}" style="background-color:{c};'


def table_html(r):
    th = "".join(f'<th {bg(NAVY)}color:#ffffff;font-size:13px;padding:6px{";text-align:right" if t == "종가" else ""}">{t}</th>'
                 for t in ("구분", "지표", "종가", "직전 거래일 대비"))
    out = [f"<tr>{th}</tr>"]
    groups = [(g, c, [it for it in items if it[1] in r]) for g, c, items in ROWS]
    groups = [g for g in groups if g[2]]
    for gi, (group, color, items) in enumerate(groups):
        last_group = gi == len(groups) - 1
        for i, (name, key) in enumerate(items):
            x = r[key]
            _, cbg, cfg = DIR[x.get("dir", "flat")]
            line = "" if last_group and i == len(items) - 1 else (
                "border-bottom:2px solid #ffffff" if i == len(items) - 1 else "border-bottom:1px solid #e6ebf5")
            g = (f'<td rowspan="{len(items)}" {bg(color)}color:#ffffff;text-align:center;font-weight:bold;padding:8px;'
                 f'border-bottom:2px solid #ffffff">{group}</td>') if i == 0 else ""
            if x.get("closed"):
                if key in FX:
                    val = (f'<td colspan="2" style="padding:8px;text-align:right;font-weight:bold;font-size:18px;{line}">'
                           f'{esc(name)} 휴장</td>')
                else:
                    val = (f'<td style="padding:8px;font-weight:bold;{line}">{esc(name)}</td>'
                           f'<td style="padding:8px;text-align:right;font-weight:bold;font-size:18px;{line}">휴장</td>')
                out.append(f'<tr>{g}{val}<td {bg("#e6ebf5")}padding:8px;text-align:center;font-weight:bold;color:#6e7887;border-bottom:2px solid #ffffff">-</td></tr>')
                continue
            if key in FX:
                val = (f'<td colspan="2" style="padding:8px;text-align:right;font-weight:bold;font-size:18px;{line}">'
                       f'{esc(name)}={esc(x["v"])}</td>')
            else:
                val = (f'<td style="padding:8px;font-weight:bold;{line}">{esc(name)}</td>'
                       f'<td style="padding:8px;text-align:right;font-weight:bold;font-size:18px;{line}">{esc(x["v"])}</td>')
            out.append(f'<tr>{g}{val}'
                       f'<td {bg(cbg)}padding:8px;text-align:center;font-weight:bold;color:{cfg};border-bottom:2px solid #ffffff">'
                       f'{esc(change(key, x))}</td></tr>')
    return ('<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-top:10px;font-size:16px">'
            + "\n".join(out) + "</table>")


def corner_html(c):
    tag = (f'<div style="text-align:center"><span style="display:inline-block;background-color:{RED};color:#ffffff;'
           f'font-size:13px;font-weight:bold;padding:3px 12px;border-radius:12px">{esc(corner_tag(c))}</span></div>')
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
    tag = corner_tag(c)
    if tag.startswith("오늘의 코너 · "): tag = f"오늘의 코너({tag[len('오늘의 코너 · '):]})"
    return f'■ {tag}\n' + "\n".join(lines)


def text_rows(r):
    unit = {"kospi": "%", "ndx": "%", "usd": "원", "jpy": "원", "wti": "달러"}
    out = []
    for _, _, items in ROWS:
        for name, key in items:
            if key not in r: continue
            x = r[key]
            if x.get("closed"):
                out.append(f'{name} 휴장' if key not in FX else f'{name} 휴장')
                continue
            if key in FX:
                out.append(f'{name}={x["v"]} {change(key, x)}')
                continue
            arrow = DIR[x.get("dir", "flat")][0].strip()
            c = x["c"] if x["c"].endswith("%") or x["c"] == "-" else x["c"] + unit[key]
            out.append(f'{name} {x["v"]} ({arrow}{c})')
    return "\n".join(out)


def basis_text(d):
    """맨 위 기준 문구. kr_date/us_date(예 '10/30','10/29')가 있으면 날짜를 밝힌다."""
    kr, us = d.get("kr_date"), d.get("us_date")
    parts = []
    if kr: parts.append(f"코스피·환율 {kr} " + ("휴장" if d.get("kr_closed") else "종가"))
    if us: parts.append(f"미국 증시 {us} " + ("휴장" if d.get("us_closed") else "종가"))
    return (" · ".join(parts) + " 기준") if parts else "직전 거래일 종가 기준"


def _pct(m):
    """종가 행 한 줄: 값이 없으면 '확인 불가'. 반환 (이름 색 화살표 텍스트)."""
    if m and m.get("closed"): return "closed"
    if not m or m.get("close") is None or m.get("day_pct") is None: return None
    p = float(m["day_pct"])
    return float(m["close"]), p, ("#d62728" if p > 0 else "#1f4fd8" if p < 0 else "#555555"), ("▲" if p > 0 else "▼" if p < 0 else "")


def markets_lines(d):
    mk = d.get("markets") or {}
    out = []
    for name, key in (("글로벌IT섹터ETF", "global_tech"), ("나스닥100ETF", "nasdaq100")):
        v = _pct(mk.get(key))
        out.append((name, v))
    return out


def _growth(d):
    gj = d.get("growth_json")
    if gj and os.path.exists(gj): return json.load(open(gj, encoding="utf8"))
    return None


def growth_line(d):
    g = _growth(d)
    if not g: return None
    return f'15년 누적수익률(환율 반영) 글로벌IT섹터ETF {g["global_tech"][-1] - 100:+.1f}% / 나스닥100ETF {g["nasdaq100"][-1] - 100:+.1f}%'


DISC = "해외 ETF 수익률에 원/달러 환율을 반영한 원화 기준 개략 추이이며, 과거 성과는 미래 수익을 보장하지 않습니다. 정보 제공용입니다."


def view_url(u):
    """raw.githubusercontent.com 주소는 Gmail이 '리디렉션 알림' 경고창을 띄우므로 github.com 보기 주소로 바꾼다."""
    pre = "https://raw.githubusercontent.com/"
    if u and u.startswith(pre):
        o, r, br, rest = u[len(pre):].split("/", 3)
        return f"https://github.com/{o}/{r}/blob/{br}/{rest}"
    return u


def markets_html(d):
    """펀드 종가 블록. 값이 없는 줄·블록은 흔적 없이 뺀다. 그래프는 첨부 대신 링크(graph_url)."""
    rows = []
    for name, v in markets_lines(d):
        if v is None: continue
        if v == "closed":
            rows.append(f'<p style="margin:6px 0;font-size:15px"><b>{esc(name)}</b> 휴장</p>')
            continue
        c, p, col, ar = v
        rows.append(f'<p style="margin:6px 0;font-size:15px"><b>{esc(name)}</b> 종가 ${c:,.2f} / 직전 거래일 대비 '
                    f'<b style="color:{col}">{ar}{abs(p):.2f}%</b></p>')
    gl = growth_line(d)
    url = view_url(d.get("graph_url")) if gl else None
    if not rows and not gl: return ""
    body = "".join(rows)
    if gl:
        body += f'<p style="margin:8px 0 2px;font-size:14px;font-weight:bold">{esc(gl)}</p>'
    if url:
        body += f'<p style="margin:2px 0;font-size:14px"><a href="{esc(url)}">종가·15년 성장 그래프 이미지 크게 보기</a></p>'
    body += f'<p style="margin:2px 0;font-size:11px;color:#6a7587">{DISC}</p>'
    return (f'<div style="margin-top:12px;border-top:2px solid {NAVY};padding-top:8px"><b style="color:{NAVY};font-size:15px">직전 거래일 종가</b>'
            + body + '</div>')


def markets_text(d):
    out = []
    for name, v in markets_lines(d):
        if v is None: continue
        if v == "closed":
            out.append(f"{name} 휴장"); continue
        c, p, _, ar = v
        out.append(f"{name} 종가 ${c:,.2f} / 직전 거래일 대비 {ar}{abs(p):.2f}%")
    gl = growth_line(d)
    if gl: out.append(gl)
    if gl and d.get("graph_url"): out.append(f"종가·15년 성장 그래프 이미지: {view_url(d['graph_url'])}")
    if not out: return ""
    return "■ 직전 거래일 종가\n" + "\n".join(out) + "\n" + DISC + "\n\n"


def main():
    inp, out = sys.argv[1], sys.argv[2]
    img = sys.argv[3] if len(sys.argv) > 3 else ""
    d = json.load(open(inp, encoding="utf8"))
    os.makedirs(out, exist_ok=True)
    sub_html = (f'<div style="font-size:15px;font-weight:bold;margin-top:4px;color:#ffd666">{esc(d["subtitle"])}</div>'
                if d.get("subtitle") else "")
    head = (f'<table width="100%" cellpadding="0" cellspacing="0" {bg(NAVY)}border-collapse:collapse;color:#ffffff">'
            f'<tr><td {bg(NAVY)}padding:14px 18px"><div style="font-size:13px;color:#c9d6ee">{esc(d["date_label"])} · {esc(basis_text(d))}</div>'
            f'<div style="font-size:26px;font-weight:bold;margin-top:2px;color:#ffffff">오늘의 소식지 <span style="font-size:15px;color:#ffd666">[해외주식 비과세 투자상담]</span></div>{sub_html}</td>'
            f'</tr></table>')
    link = (f'<p style="font-size:14px;margin:4px 0"><a href="{esc(img)}">소식지 이미지(나스닥100 장기 추이 차트 포함) 크게 보기</a></p>'
            if img else "")
    page = (f'<div style="max-width:560px;margin:0 auto;font-family:\'Apple SD Gothic Neo\',\'Malgun Gothic\',sans-serif;color:#1b2433">'
            f'{head}{corner_html(d["corner"])}{table_html(d["rows"])}{markets_html(d)}'
            f'<p style="font-size:14px;margin:14px 0 4px">{esc(d["greeting"])}</p>{link}'
            f'<p style="font-size:14px;margin:10px 0 4px">상담 문의 010-3224-1517<br>상담 신청 <a href="{CONSULT}">{CONSULT}</a></p>'
            f'<p style="font-size:11px;color:#6a7587;margin-top:10px">{esc(d["src"])}<br>※ 본 자료는 정보 제공용입니다.</p></div>')
    text = (f'오늘의 소식지 {d["date_label"]} ({basis_text(d)})\n' + (f'{d["subtitle"]}\n' if d.get("subtitle") else '') + f'\n{d["greeting"]}\n\n{corner_text(d["corner"])}\n\n■ 직전 거래일 시장\n{text_rows(d["rows"])}\n\n{markets_text(d)}' + (f"소식지 이미지: {img}\n\n" if img else "")
            + f'상담 문의 010-3224-1517\n상담 신청 {CONSULT}\n\n※ 본 자료는 정보 제공용입니다.\n')
    open(os.path.join(out, "mail.html"), "w", encoding="utf8").write(page)
    open(os.path.join(out, "mail.txt"), "w", encoding="utf8").write(text)
    print(f"mail.html {len(page)}자, mail.txt {len(text)}자")


main()
