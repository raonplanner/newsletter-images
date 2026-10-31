#!/usr/bin/env python3
"""소식지 공통 모듈 (메일 mail_html.py · 인스타 이미지 render.py · 설명글 caption.py 가 함께 쓴다).

입력 JSON(예, 값은 모두 조회한 실제 값):
{"date_label":"2026년 10월 30일 금요일","kr_date":"10/30","us_date":"10/29","kr_closed":false,"us_closed":false,
 "subtitle":"미국 기술주가 약했고, 코스피도 3%대 내렸어요",
 "greeting":"늘 건강하고 평안한 날들 보내시길 바랄게요.",
 "rows":{"kospi":{"v":"5,730.74","c":"3.48%","dir":"down"},"usd":{"v":"1,334.30원","c":"2.50","dir":"down"},
         "ndx":{"v":"29,402.51","c":"1.38%","dir":"down"}},          # 휴장이면 {"closed":true}, 못 구한 행은 키 삭제
 "markets":{"global_tech":{"close":141.94,"day_pct":-1.39},"nasdaq100":{"close":715.34,"day_pct":-1.42}},
 "growth_json":"/tmp/work/growth.json",
 "corner":{"type":"news","items":[{"h":"미국 기술주 약세","b":"..."}]},          # quote 형식도 가능(quote/who/close)
 "cells":[{"kind":"text","title":"오늘의 연금 한 줄","color":"teal","body":"...","risk":true},
          {"kind":"cal","title":"원장님 경영 달력","color":"green","items":[{"d":"11/10(화)","t":"원천세 신고·납부","s":"10월 급여 지급분"}]},
          {"kind":"list","title":"연금저축 vs IRP, 뭐가 달라요?","color":"slate","items":["...","..."]}],
 "image_cell":0,                 # 인스타 2번째 장에 넣을 칸 번호(기본 0)
 "hashtags":"#오늘의소식지 #연금저축 #IRP"}
칸(cells)의 color: amber teal green purple slate red navy. 칸에 "risk":true 이면 '투자 전 꼭 알아두세요' 안내가 자동으로 붙는다.
"""
import re, os, json, html

NAVY = "#12294d"
SIGN = "메트라이프금융서비스 송근영팀장"
PHONE = "010-3224-1517"
RISK_T = "투자 전 꼭 알아두세요"
RISK_B = "투자는 원금 손실이 날 수 있어요. 투자 전 상담은 꼭 전문가에게 받아 보시고, 본인이 결정하셔야 합니다."
REPLY = "궁금한 점은 이 메일에 답장으로 편하게 남겨 주세요."
DISC = "해외 ETF 수익률에 원/달러 환율을 반영한 원화 기준 개략 추이이고, 과거 성과가 앞으로를 보장하지는 않아요."
QUAL = [("증권투자권유대행인", "골든트리투자자문 소속", "등록번호", "8217000309"),
        ("변액보험판매관리사", None, None, "2010.10.28 합격"),
        ("펀드투자상담사", None, None, "2013.09.27 합격")]
COLORS = {"amber": "#b7791f", "teal": "#0b7285", "green": "#0e6b4f", "purple": "#5b3fa0",
          "slate": "#3a4659", "red": "#c8102e", "navy": NAVY}
BODY_BG = {"amber": "#fff9e6", "green": "#f1f8f4"}
UP, DOWN, FLAT = "#d62728", "#1553b0", "#555555"
UPBG, DOWNBG = "#fde3e4", "#e3edfc"
FX = ("usd", "jpy")


def esc(t): return html.escape(str(t))


def bad_words(text):
    """고객에게 나가면 안 되는 문구 검사. 걸린 단어 목록을 돌려준다."""
    return [w for w in ("확인 불가", "자료 없음", "조회 실패", "IXN", "QQQ", "글로벌IT섹터펀드", "나스닥100펀드", "전일 대비", "직전 거래일 대비") if w in text]


def basis_text(d):
    kr, us = d.get("kr_date"), d.get("us_date")
    parts = []
    if kr: parts.append(f"코스피·환율 {kr} " + ("휴장" if d.get("kr_closed") else "당일종가"))
    if us: parts.append(f"미국 증시 {us} " + ("휴장" if d.get("us_closed") else "전일종가"))
    return (" · ".join(parts) + " 기준") if parts else "당일종가·전일종가 기준"


def greeting_lines(d):
    g = re.sub(r"^안녕하세요[,.!\s]*", "", (d.get("greeting") or "").strip())
    g = g.replace(f"{SIGN}입니다.", "").strip()
    return [f"안녕하세요, {SIGN}입니다.", g or "늘 건강하고 평안한 날들 보내시길 바랄게요."]


def date_short(d):
    m = re.search(r"(\d+)월\s*(\d+)일\s*(\S+요일)", d.get("date_label", ""))
    return f"{m.group(1)}월 {m.group(2)}일 {m.group(3)}" if m else d.get("date_label", "")


# ---------- 시세 ----------
def row_view(key, x):
    """반환: (값 문자열, 등락 문자열, 색, 배경) 또는 휴장이면 ('휴장','-',FLAT,'#eef1f5')."""
    if x.get("closed"): return "휴장", "-", FLAT, "#eef1f5"
    d = x.get("dir", "flat")
    arrow = {"up": "▲", "down": "▼", "flat": ""}[d]
    c = x["c"]
    if key in FX:
        c = c if c in ("-", "") or c.endswith("원") else c + "원"
        ch = f"{arrow} {c}".strip()
    else:
        ch = f"{arrow} {c}".strip()
    col = {"up": UP, "down": DOWN, "flat": FLAT}[d]
    bgc = {"up": UPBG, "down": DOWNBG, "flat": "#eef1f5"}[d]
    return x["v"], ch, col, bgc


def etf_view(m):
    """ETF 한 줄. 반환 None(못 구함, 줄 삭제) / 휴장 / (종가문자열, 등락문자열, 색, 배경)."""
    if m and m.get("closed"): return "휴장", "-", FLAT, "#eef1f5"
    if not m or m.get("close") is None or m.get("day_pct") is None: return None
    p = float(m["day_pct"])
    arrow = "▲" if p > 0 else "▼" if p < 0 else ""
    col = UP if p > 0 else DOWN if p < 0 else FLAT
    bgc = UPBG if p > 0 else DOWNBG if p < 0 else "#eef1f5"
    return f"${float(m['close']):,.2f}", f"{arrow} {abs(p):.2f}%".strip(), col, bgc


def etf_lines(d):
    mk = d.get("markets") or {}
    out = []
    for name, key in (("글로벌IT섹터ETF", "global_tech"), ("나스닥100ETF", "nasdaq100")):
        v = etf_view(mk.get(key))
        if v is not None: out.append((name, v))
    return out


def growth(d):
    gj = d.get("growth_json")
    if gj and os.path.exists(gj): return json.load(open(gj, encoding="utf8"))
    return None


def growth_pairs(d):
    g = growth(d)
    if not g: return None
    return (g["global_tech"][-1] - 100, g["nasdaq100"][-1] - 100)


def _word(sign): return {1: "올랐어요", -1: "내렸어요", 0: "보합이에요"}[sign]


def _link(sign): return {1: "올랐고", -1: "내렸고", 0: "보합이고"}[sign]


def summary(d):
    """한 줄 요약(코드가 숫자로 만든다). 휴장·누락 항목도 처리한다."""
    r = d.get("rows") or {}
    live, shut = [], []
    k = r.get("kospi")
    if k is not None:
        if k.get("closed"): shut.append("코스피")
        else: live.append(("코스피", k["c"], {"up": 1, "down": -1}.get(k.get("dir"), 0)))
    nv = etf_view((d.get("markets") or {}).get("nasdaq100"))
    if nv is not None:
        if nv[0] == "휴장": shut.append("나스닥100ETF")
        else:
            p = float(d["markets"]["nasdaq100"]["day_pct"])
            live.append(("나스닥100ETF", f"{abs(p):.2f}%", 1 if p > 0 else -1 if p < 0 else 0))
    out = []
    if len(live) == 2:
        (n1, v1, s1), (n2, v2, s2) = live
        out.append(f"{n1}는 {v1}, {n2}는 {v2} {_word(s1)}." if s1 == s2 else f"{n1}는 {v1} {_link(s1)}, {n2}는 {v2} {_word(s2)}.")
    elif live:
        n1, v1, s1 = live[0]
        out.append(f"{n1}는 {v1} {_word(s1)}.")
    out += [f"{n}는 휴장이었어요." for n in shut]
    u = r.get("usd")
    if u:
        out.append("환율은 휴장이었어요." if u.get("closed") else f"환율은 1달러에 {u['v']}이에요.")
    return " ".join(out)


# ---------- 칸 ----------
def color_of(c): return COLORS.get(c, c if str(c).startswith("#") else COLORS["teal"])


def cell_text(c):
    """칸의 일반 텍스트(메일 txt·인스타 설명글 공용)."""
    lines = [f"■ {c['title']}"]
    k = c.get("kind", "text")
    if k == "text":
        lines.append(c["body"])
    elif k == "list":
        lines += [f"· {i}" for i in c["items"]]
    elif k == "cal":
        for i in c["items"]:
            lines.append(f"{i['d']} {i['t']}" + (f" ({i['s']})" if i.get("s") else ""))
    if c.get("risk"): lines.append(f"※ {RISK_B}")
    return "\n".join(lines)


def corner_tag(c):
    names = {"quote": "오늘의 명언", "news": "중요 경제기사", "schedule": "오늘의 주요 일정", "policy": "개원가·의료 정책",
             "calendar": "병·의원 경영 달력", "health": "계절 건강", "term": "쉬운 금융 용어", "medical": "의료계 소식"}
    if c.get("tag"): return c["tag"]
    return "오늘의 코너 · " + names.get(c["type"], "중요 경제기사") if c["type"] != "quote" else "오늘의 명언"


def corner_text(c):
    lines = [f'"{c["quote"]}" - {c["who"]}'] if c["type"] == "quote" else [f'{i["h"]} — {i["b"]}' for i in c["items"]]
    if c.get("close"): lines.append(c["close"])
    return f"■ {corner_tag(c)}\n" + "\n".join(lines)
