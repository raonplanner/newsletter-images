#!/usr/bin/env python3
"""15년 성장 추이(환율 반영, 원화 기준) 계산 + 그래프 이미지.
사용: python3 -I tools/growth.py 글로벌IT섹터ETF종가 나스닥100ETF종가 오늘원달러환율 출력.json 출력.png [kr_date(M/D)]
 - 종가: 직전 미국 정규장 종가(USD), 환율: 소식지에 표시하는 오늘 원/달러 종가(예 1334.30)
 - data/growth_15y.json 의 연간 총수익률·연말 환율로 2011년 말=100 기준 원화 지수를 만든다.
출력.json: render2.py·mail_html.py 가 "growth_json" 으로 읽는다. 출력.png: 메일 링크용 그래프(첨부 안 함).
"""
import sys, os, json, datetime as dt
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from scipy.interpolate import PchipInterpolator as P

HERE = os.path.dirname(os.path.abspath(__file__))
G, N, FX = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
out_json, out_png = sys.argv[4], sys.argv[5]
kr = sys.argv[6] if len(sys.argv) > 6 else ""
d = json.load(open(os.path.join(HERE, "..", "data", "growth_15y.json"), encoding="utf8"))
b = d["base"]; a0 = d["ytd_anchor"]
dates = [b["date"]]; ug = [100.0]; un = [100.0]; fx = [b["fx"]]
for r in d["years"]:
    dates.append(f'{r["y"]}-12-31'); ug.append(ug[-1] * (1 + r["g"] / 100)); un.append(un[-1] * (1 + r["n"] / 100)); fx.append(r["fx"])
today = dt.date.today().isoformat()
dates.append(today)
ug.append(ug[-1] * a0["g_factor"] * G / a0["g_ref_close"]); un.append(un[-1] * a0["n_factor"] * N / a0["n_ref_close"]); fx.append(FX)
kg = [v * f / b["fx"] for v, f in zip(ug, fx)]; kn = [v * f / b["fx"] for v, f in zip(un, fx)]
res = {"label": "15", "base_label": b["label"], "dates": dates, "global_tech": kg, "nasdaq100": kn,
       "fx_today": FX, "fx_base": b["fx"], "kr_date": kr, "usd_global_tech": ug[-1], "usd_nasdaq100": un[-1]}
i5 = dates.index("2021-12-31")
res["five_year"] = {"global_tech": kg[-1] / kg[i5] - 1, "nasdaq100": kn[-1] / kn[i5] - 1}
json.dump(res, open(out_json, "w"), ensure_ascii=False)

for f in fm.findSystemFonts():
    if "CJK" in f: fm.fontManager.addfont(f)
plt.rcParams.update({"font.family": "Noto Sans CJK KR", "axes.unicode_minus": False})
dd = [dt.date.fromisoformat(x) for x in dates]; x = np.array([(v - dd[0]).days for v in dd], float)
xs = np.linspace(x[0], x[-1], 400); ds = [dd[0] + dt.timedelta(days=float(v)) for v in xs]
f, ax = plt.subplots(figsize=(8, 4.5), dpi=125)
ax.plot(ds, P(x, kn)(xs), color="#1f4fd8", lw=3, label="나스닥100ETF"); ax.plot(ds, P(x, kg)(xs), color="#d62728", lw=3, label="글로벌IT섹터ETF")
ax.annotate(f"{kg[-1]:.0f} (+{kg[-1]-100:.0f}%)", (ds[-1], kg[-1]), xytext=(6, 0), textcoords="offset points", color="#d62728", fontsize=10, fontweight="bold", va="center")
ax.annotate(f"{kn[-1]:.0f} (+{kn[-1]-100:.0f}%)", (ds[-1], kn[-1]), xytext=(6, 0), textcoords="offset points", color="#1f4fd8", fontsize=10, fontweight="bold", va="center")
ax.axhline(100, color="#999", lw=1, ls="--"); ax.set_title(f'최근 15년 성장 추이 ({b["label"]} = 100, 환율 반영)', loc="left", fontweight="bold")
ax.set_xlim(ds[0], ds[-1] + dt.timedelta(days=650)); ax.set_ylim(0, max(kg[-1], kn[-1]) * 1.1); h_, l_ = ax.get_legend_handles_labels(); ax.legend(h_[::-1], l_[::-1], loc="upper left", frameon=False)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#e5e5e5"); f.tight_layout(); f.savefig(out_png)
print(f"15년(환율 반영) 글로벌IT섹터ETF {kg[-1]-100:+.1f}% 나스닥100ETF {kn[-1]-100:+.1f}%  (달러 기준 {ug[-1]-100:+.1f}% / {un[-1]-100:+.1f}%)")
