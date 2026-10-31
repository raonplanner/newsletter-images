#!/usr/bin/env python3
"""인스타 2장(직전 거래일 종가 + 10년 성장 곡선) 이미지 생성기.
사용: python3 -I tools/render2.py 입력2.json 출력폴더   ->  출력폴더/post2.png (1080x1350)
입력2.json 예: {"date_label":"2026년 10월 23일 금요일",
 "markets":{"global_tech":{"close":136.97,"day_pct":0.62},"nasdaq100":{"close":704.40,"day_pct":-0.01}},
 "growth10y":{"global_tech":806.0,"nasdaq100":638.9}}
값이 없으면(null 또는 키 없음) 해당 줄/그래프는 '확인 불가'로 표시한다. 영문 티커는 쓰지 않는다.
"""
import sys, os, json, datetime as dt
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch
from scipy.interpolate import PchipInterpolator as P

for f in fm.findSystemFonts():
    if "CJK" in f: fm.fontManager.addfont(f)
plt.rcParams.update({"font.family": "Noto Sans CJK KR", "axes.unicode_minus": False})
R, B, NAVY = "#d62728", "#1f4fd8", "#12294d"
D = ["2016-10-23","2017-12-31","2018-12-31","2019-12-31","2020-12-31","2021-12-31","2022-12-31","2023-12-31","2024-12-31","2025-12-31","2026-10-23"]
G0 = [100,141.3,133.6,197.6,283.8,367.8,258.0,394.7,492.8,617.2,806.0]
N0 = [100,133.5,133.3,185.2,275.2,350.6,236.4,366.1,459.8,555.3,638.9]


def basis_text(d):
    """맨 위 기준 문구. kr_date/us_date(예 '10/30','10/29')가 있으면 날짜를 밝힌다."""
    kr, us = d.get("kr_date"), d.get("us_date")
    parts = []
    if kr: parts.append(f"코스피·환율 {kr} 종가")
    if us: parts.append(f"미국 증시 {us} 종가")
    return (" · ".join(parts) + " 기준") if parts else "직전 거래일 종가 기준"


def main():
    inp, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    d = json.load(open(inp, encoding="utf8"))
    mk = d.get("markets") or {}
    gr = d.get("growth10y") or {}
    G, N = gr.get("global_tech"), gr.get("nasdaq100")
    for k in ("global_tech", "nasdaq100"):
        m = mk.get(k) or {}
        if m.get("close") is None or m.get("day_pct") is None:
            raise SystemExit("펀드 종가 자료가 없어 post2.png를 만들지 않는다(빈 칸·확인 불가 표기 금지).")
    if G is None or N is None:
        raise SystemExit("10년 성장 자료가 없어 post2.png를 만들지 않는다.")
    fig = plt.figure(figsize=(10.8, 13.5), dpi=100); fig.patch.set_facecolor("white")
    bg = fig.add_axes([0, 0, 1, 1]); bg.set_xlim(0, 1080); bg.set_ylim(1350, 0); bg.axis("off")
    bg.add_patch(plt.Rectangle((0, 0), 1080, 154, color=NAVY))
    bg.text(40, 26, d["date_label"], color="#c9d6ee", fontsize=17, va="center")
    bg.text(40, 52, basis_text(d), color="#c9d6ee", fontsize=17, va="center")
    bg.text(40, 105, "오늘의 소식지", color="white", fontsize=40, fontweight="bold", va="center")
    bg.text(374, 110, "[해외주식 비과세]", color="#ffd666", fontsize=21, fontweight="bold", va="center")
    bg.text(1040, 45, "송근영 Mentor", color="white", fontsize=23, fontweight="bold", va="center", ha="right")
    bg.text(1040, 80, "메트라이프금융서비스(주) 중부직할지점", color="#c9d6ee", fontsize=17, va="center", ha="right")
    bg.text(1040, 112, "m. 010-3224-1517", color="#c9d6ee", fontsize=17, va="center", ha="right")
    bg.text(40, 215, "직전 거래일 종가", fontsize=30, fontweight="bold", va="center")
    for i, (name, key) in enumerate((("글로벌IT섹터펀드", "global_tech"), ("나스닥100ETF", "nasdaq100"))):
        y = 255 + i * 110
        bg.add_patch(FancyBboxPatch((40, y), 1000, 92, boxstyle="round,pad=0,rounding_size=14", fc="#f3f5fa", ec="none"))
        bg.text(70, y + 46, name, fontsize=27, va="center")
        m = mk.get(key) or {}
        if m.get("close") is None or m.get("day_pct") is None:
            bg.text(1010, y + 46, "확인 불가", fontsize=26, color="#777", va="center", ha="right"); continue
        pct = float(m["day_pct"]); col = R if pct > 0 else (B if pct < 0 else "#555")
        arrow = "▲" if pct > 0 else ("▼" if pct < 0 else "")
        bg.text(480, y + 46, f'종가 ${float(m["close"]):,.2f}', fontsize=27, fontweight="bold", va="center")
        bg.text(1010, y + 30, "직전 거래일 대비", fontsize=16, color="#555", va="center", ha="right")
        bg.text(1010, y + 64, f"{arrow}{abs(pct):.2f}%", fontsize=28, fontweight="bold", color=col, va="center", ha="right")
    bg.text(40, 520, "최근 10년 성장 추이 (2016.10 = 100)", fontsize=30, fontweight="bold", va="center")
    if G is not None and N is not None:
        G, N = float(G), float(N)
        bg.text(40, 577, "10년 누적수익률", fontsize=21, va="center")
        bg.text(245, 577, f"글로벌IT섹터펀드 {G-100:+.1f}%", fontsize=21, fontweight="bold", color=R, va="center")
        bg.text(685, 577, f"나스닥100ETF {N-100:+.1f}%", fontsize=21, fontweight="bold", color=B, va="center")
        g, n, dd = G0[:], N0[:], D[:]
        g.append(G); n.append(N); dd.append("2026-10-24")
        ds0 = [dt.date.fromisoformat(a) for a in dd]; x = np.array([(a - ds0[0]).days for a in ds0], float)
        if G == g[-2] and N == n[-2]: x, g, n, ds0 = x[:-1], g[:-1], n[:-1], ds0[:-1]
        xs = np.linspace(x[0], x[-1], 300); ds = [ds0[0] + dt.timedelta(days=float(v)) for v in xs]
        a = fig.add_axes([0.07, 0.19, 0.85, 0.35])
        a.plot(ds, P(x, n)(xs), color=B, lw=4, label="나스닥100ETF"); a.plot(ds, P(x, g)(xs), color=R, lw=4, label="글로벌IT섹터펀드")
        a.annotate(f"{g[-1]:.1f}", (ds[-1], g[-1]), xytext=(8, 0), textcoords="offset points", color=R, fontsize=16, fontweight="bold", va="center")
        a.annotate(f"{n[-1]:.1f}", (ds[-1], n[-1]), xytext=(8, 0), textcoords="offset points", color=B, fontsize=16, fontweight="bold", va="center")
        a.axhline(100, color="#999", lw=1, ls="--"); a.set_ylim(0, max(g[-1], n[-1]) * 1.12); a.set_xlim(ds[0], ds[-1] + dt.timedelta(days=420))
        a.legend(loc="upper left", frameon=False, fontsize=16); a.tick_params(labelsize=14)
        for s in ("top", "right"): a.spines[s].set_visible(False)
        a.grid(axis="y", color="#e5e5e5")
    else:
        bg.text(40, 700, "10년 성장 그래프: 확인 불가", fontsize=26, color="#777", va="center")
    bg.text(40, 1160, "※ 해외 ETF(달러, 배당 재투자) 시세를 환산한 개략 추이이며 연말 기준 근사값입니다.\n   실제 펀드 수익률과 다를 수 있으며 환율은 반영하지 않았습니다.\n   과거 수익률은 미래 수익을 보장하지 않습니다.", fontsize=14, color="#777", va="top", linespacing=1.6)
    bg.add_patch(plt.Rectangle((0, 1260), 1080, 90, color="#f3f5fa"))
    bg.text(540, 1290, "상담 문의 010-3224-1517", fontsize=24, fontweight="bold", ha="center", va="center")
    bg.text(540, 1325, "※ 본 자료는 정보 제공용입니다.", fontsize=15, color="#777", ha="center", va="center")
    p = os.path.join(out, "post2.png")
    fig.savefig("/tmp/_post2_rgba.png", dpi=100)
    from PIL import Image
    Image.open("/tmp/_post2_rgba.png").convert("RGB").save(p, optimize=True)
    print(f"post2={Image.open(p).size}")


main()
