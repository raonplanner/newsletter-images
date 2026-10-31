#!/usr/bin/env python3
"""인스타 1번째 장(전일종가 + 15년 성장 곡선(환율 반영) + 투자 안내·자격) 이미지 생성기.
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
    if kr: parts.append(f"코스피·환율 {kr} " + ("휴장" if d.get("kr_closed") else "당일종가"))
    if us: parts.append(f"미국 증시 {us} " + ("휴장" if d.get("us_closed") else "전일종가"))
    return (" · ".join(parts) + " 기준") if parts else "직전 거래일 종가 기준"


def main():
    inp, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    d = json.load(open(inp, encoding="utf8"))
    mk = d.get("markets") or {}
    gj = d.get("growth_json")
    gr = json.load(open(gj, encoding="utf8")) if gj and os.path.exists(gj) else None
    G = gr["global_tech"][-1] if gr else None
    N = gr["nasdaq100"][-1] if gr else None
    for k in ("global_tech", "nasdaq100"):
        m = mk.get(k) or {}
        if m.get("closed"): continue
        if m.get("close") is None or m.get("day_pct") is None:
            raise SystemExit("펀드 종가 자료가 없어 post2.png를 만들지 않는다(빈 칸·확인 불가 표기 금지).")
    if G is None or N is None:
        raise SystemExit("15년 성장 자료(growth_json)가 없어 post2.png를 만들지 않는다.")
    fig = plt.figure(figsize=(10.8, 13.5), dpi=100); fig.patch.set_facecolor("white")
    bg = fig.add_axes([0, 0, 1, 1]); bg.set_xlim(0, 1080); bg.set_ylim(1350, 0); bg.axis("off")
    bg.add_patch(plt.Rectangle((0, 0), 1080, 176, color=NAVY))
    bg.text(40, 26, d["date_label"], color="#c9d6ee", fontsize=17, va="center")
    bg.text(40, 52, basis_text(d), color="#c9d6ee", fontsize=17, va="center")
    bg.text(40, 98, "오늘의 소식지", color="white", fontsize=40, fontweight="bold", va="center")
    bg.text(40, 145, "[해외주식 비과세 투자상담]", color="#ffd666", fontsize=21, fontweight="bold", va="center")
    bg.text(40, 215, "전일종가", fontsize=30, fontweight="bold", va="center")
    bg.text(190, 217, "· 미국 증시", fontsize=20, color="#555", va="center")
    for i, (name, key) in enumerate((("글로벌IT섹터ETF", "global_tech"), ("나스닥100ETF", "nasdaq100"))):
        y = 255 + i * 110
        bg.add_patch(FancyBboxPatch((40, y), 1000, 92, boxstyle="round,pad=0,rounding_size=14", fc="#f3f5fa", ec="none"))
        bg.text(70, y + 46, name, fontsize=27, va="center")
        m = mk.get(key) or {}
        if m.get("closed"):
            bg.text(1010, y + 46, "휴장", fontsize=30, fontweight="bold", color="#555", va="center", ha="right"); continue
        if m.get("close") is None or m.get("day_pct") is None:
            bg.text(1010, y + 46, "확인 불가", fontsize=26, color="#777", va="center", ha="right"); continue
        pct = float(m["day_pct"]); col = R if pct > 0 else (B if pct < 0 else "#555")
        arrow = "▲" if pct > 0 else ("▼" if pct < 0 else "")
        bg.text(480, y + 46, f'종가 ${float(m["close"]):,.2f}', fontsize=27, fontweight="bold", va="center")
        bg.text(1010, y + 46, f"{arrow}{abs(pct):.2f}%", fontsize=28, fontweight="bold", color=col, va="center", ha="right")
    bg.text(40, 520, f'최근 15년 성장 추이 ({gr["base_label"]} = 100, 환율 반영)', fontsize=30, fontweight="bold", va="center")
    G, N = float(G), float(N)
    bg.text(40, 577, "15년 누적수익률", fontsize=21, va="center")
    bg.text(290, 577, f"글로벌IT섹터ETF {G-100:+.1f}%", fontsize=21, fontweight="bold", color=R, va="center")
    bg.text(695, 577, f"나스닥100ETF {N-100:+.1f}%", fontsize=21, fontweight="bold", color=B, va="center")
    g, n = gr["global_tech"], gr["nasdaq100"]
    ds0 = [dt.date.fromisoformat(a_) for a_ in gr["dates"]]; x = np.array([(a_ - ds0[0]).days for a_ in ds0], float)
    xs = np.linspace(x[0], x[-1], 400); ds = [ds0[0] + dt.timedelta(days=float(v)) for v in xs]
    a = fig.add_axes([0.07, 0.235, 0.85, 0.275])
    a.plot(ds, P(x, n)(xs), color=B, lw=4, label="나스닥100ETF"); a.plot(ds, P(x, g)(xs), color=R, lw=4, label="글로벌IT섹터ETF")
    a.annotate(f"{g[-1]:.0f}", (ds[-1], g[-1]), xytext=(8, 0), textcoords="offset points", color=R, fontsize=16, fontweight="bold", va="center")
    a.annotate(f"{n[-1]:.0f}", (ds[-1], n[-1]), xytext=(8, 0), textcoords="offset points", color=B, fontsize=16, fontweight="bold", va="center")
    a.axhline(100, color="#999", lw=1, ls="--"); a.set_ylim(0, max(g[-1], n[-1]) * 1.12); a.set_xlim(ds[0], ds[-1] + dt.timedelta(days=620))
    h_, l_ = a.get_legend_handles_labels(); a.legend(h_[::-1], l_[::-1], loc="upper left", frameon=False, fontsize=16); a.tick_params(labelsize=14)
    for s_ in ("top", "right"): a.spines[s_].set_visible(False)
    a.grid(axis="y", color="#e5e5e5")
    f5 = gr.get("five_year") or {}
    if f5:
        if f5["global_tech"] > f5["nasdaq100"]:
            l1 = "최근 5년은 반도체 비중이 높은 글로벌IT섹터ETF가 앞서 있습니다."
            l2 = "AI·자율형 로봇에는 반도체가 많이 쓰여 이 흐름의 영향을 받습니다."
        else:
            l1 = "최근 5년은 나스닥100ETF가 앞서 있습니다."
            l2 = "AI·자율형 로봇 등 산업 흐름에 따라 향후 성과는 달라질 수 있습니다."
        bg.text(40, 608, l1, fontsize=15, color="#333", va="center")
        bg.text(40, 636, l2, fontsize=15, color="#333", va="center")
    fxd = gr.get("kr_date") or ""
    bg.text(40, 1062, f'※ 해외 ETF(배당 재투자) 수익률에 원/달러 환율(연말 서울 종가, 현재는 {fxd} 종가 {gr["fx_today"]:,.1f}원)을 반영한\n   원화 기준 개략 추이이며 연말 기준 근사값입니다. 환전·세금·수수료는 반영하지 않았고 실제 투자 수익과\n   다를 수 있습니다. 과거 수익률은 미래 수익을 보장하지 않습니다.', fontsize=12.5, color="#777", va="top", linespacing=1.4)
    bg.add_patch(plt.Rectangle((40, 1148), 1000, 62, color="#f6f8fb", ec="#cfd6e4", lw=1.5))
    bg.text(58, 1165, "투자 전 꼭 알아두세요", fontsize=14, fontweight="bold", color="#3a4659", va="center")
    bg.text(58, 1193, "투자는 원금 손실이 날 수 있어요. 투자 전 상담은 꼭 전문가에게 받아 보시고, 본인이 결정하셔야 합니다.", fontsize=14, color="#3a4659", va="center")
    bg.add_patch(plt.Rectangle((40, 1218), 1000, 52, color="#3a4659"))
    bg.text(58, 1232, "자격 · 증권투자권유대행인(골든트리투자자문 소속, 등록번호 8217000309)", fontsize=12.5, color="white", va="center")
    bg.text(58, 1256, "변액보험판매관리사(2010.10.28 합격) · 펀드투자상담사(2013.09.27 합격)", fontsize=12.5, color="white", va="center")
    bg.add_patch(plt.Rectangle((0, 1280), 1080, 70, color=NAVY))
    bg.text(540, 1301, "메트라이프금융서비스 송근영팀장", fontsize=17, fontweight="bold", color="white", ha="center", va="center")
    bg.text(540, 1330, "010-3224-1517", fontsize=22, fontweight="bold", color="white", ha="center", va="center")
    p = os.path.join(out, "post2.png")
    fig.savefig("/tmp/_post2_rgba.png", dpi=100)
    from PIL import Image
    Image.open("/tmp/_post2_rgba.png").convert("RGB").save(p, optimize=True)
    print(f"post2={Image.open(p).size}")


main()
