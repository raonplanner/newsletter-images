#!/usr/bin/env python3
"""입력 JSON -> 종목 분석 이미지(report.png)와 분석 시트용 CSV(analysis.csv).

사용: python3 -I tools/stock_report.py input.json 출력폴더
입력 JSON:
{"asof":"2026-10-16",
 "stocks":[{"ticker":"TRV","name":"The Travelers Companies","desc":"미국 대형 손해보험사",
            "dates":["YYYY-MM-DD",...],      # 오래된 날짜부터, 25개 이상
            "closes":[...], "vols":[...],    # dates와 같은 길이
            "hi52":398.70,"lo52":262.90,"pe":10.2,"peg":15.73,"mcap_b":79.83}],
 "notes":["해석 문장", ...]}                  # CSV 오른쪽 아래에 적힐 문장(선택)
이미지는 앞의 4종목까지, CSV는 모든 종목을 담는다.
"""
import sys, os, json, csv, io, glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.gridspec import GridSpec

def setup_font():
    cands = glob.glob("/usr/share/fonts/**/NotoSansCJK*.ttc", recursive=True) + \
            glob.glob("/usr/share/fonts/**/NotoSansKR*.*", recursive=True) + \
            glob.glob("/usr/share/fonts/**/Nanum*.*", recursive=True)
    for p in cands:
        try: fm.fontManager.addfont(p)
        except Exception: pass
    names = {f.name for f in fm.fontManager.ttflist}
    for n in ("Noto Sans CJK KR", "Noto Sans KR", "NanumGothic", "Noto Sans CJK JP"):
        if n in names:
            plt.rcParams["font.family"] = n
            return n
    raise SystemExit("한글 글꼴을 찾지 못했습니다")

BG="#0f1720"; CARD="#182433"; TXT="#e2e8f0"; SUB="#9fb3c8"; GOLD="#ffd166"; UP="#2ec4b6"; DN="#ef476f"

def metrics(s):
    fl, vo = s["closes"], s["vols"]; n = len(fl)
    assert len(vo) == n == len(s["dates"]) and n >= 25, f'{s["ticker"]}: 자료는 25거래일 이상 필요'
    c = fl[-5:]; prev = fl[-6:-1]
    chg = [(a/b-1)*100 for a, b in zip(c, prev)]
    ma = lambda k: [sum(fl[j-k+1:j+1])/k for j in range(n-5, n)]
    avg = [sum(vo[j-20:j])/20 for j in range(n-5, n)]
    return dict(n=n, c=c, chg=chg, m5=ma(5), m20=ma(20), v5=vo[-5:], avg=avg,
                ratio=[v/m for v, m in zip(vo[-5:], avg)], dates5=s["dates"][-5:])

def label(d):
    import datetime
    y, m, dd = map(int, d.split("-")); w = "월화수목금토일"[datetime.date(y, m, dd).weekday()]
    return f"{m}/{dd}({w})"

def make_png(data, out):
    stocks = data["stocks"][:4]
    k = len(stocks)
    H = 1.6 + k * 9.2
    fig = plt.figure(figsize=(10.8, H), dpi=100, facecolor=BG)
    fig.text(0.055, 1-0.35/H, "S&P500 저평가·거래량급증 종목 — 직전 일주일", fontsize=24, fontweight="bold", color="white", va="top")
    d5 = metrics(stocks[0])["dates5"]
    fig.text(0.055, 1-0.85/H, f"{label(d5[0])} ~ {label(d5[-1])} 5거래일 · 미국장 종가·거래량 · 기준일 {data['asof']}", fontsize=14, color=SUB, va="top")
    gs = GridSpec(3*k, 1, figure=fig, height_ratios=[1.0, 2.3, 1.7]*k, top=1-1.3/H, bottom=0.95/H, hspace=0.42, left=0.09, right=0.95)
    x = list(range(5))
    for i, s in enumerate(stocks):
        m = metrics(s); c = m["c"]
        wk = (c[-1]/c[0]-1)*100
        h = fig.add_subplot(gs[i*3]); h.axis("off")
        h.text(0, 0.78, s["ticker"], fontsize=34, fontweight="bold", color=GOLD, va="center", transform=h.transAxes)
        h.text(0.2, 0.78, s["name"], fontsize=17, color=TXT, va="center", transform=h.transAxes)
        h.text(0, 0.30, s.get("desc", ""), fontsize=14, color=SUB, va="center", transform=h.transAxes)
        h.text(1, 0.78, f"주간 {wk:+.1f}%", fontsize=20, fontweight="bold", color=UP if wk >= 0 else DN, ha="right", va="center", transform=h.transAxes)
        lo, hi = s["lo52"], s["hi52"]; cur = c[-1]; pos = min(max((cur-lo)/(hi-lo), 0), 1)
        bx0, bx1, by = 0.56, 1.0, 0.22
        h.plot([bx0, bx1], [by, by], color="#2d3f55", lw=8, solid_capstyle="round", transform=h.transAxes, clip_on=False)
        h.plot([bx0+(bx1-bx0)*pos], [by], marker="o", ms=13, color=GOLD, transform=h.transAxes, clip_on=False, zorder=5)
        h.text(bx0, by-0.2, f"52주 저 {lo:,.2f}", fontsize=11, color=SUB, ha="left", va="top", transform=h.transAxes)
        h.text(bx1, by-0.2, f"고 {hi:,.2f}", fontsize=11, color=SUB, ha="right", va="top", transform=h.transAxes)
        h.text(bx0, by+0.16, f"52주 범위 내 위치 {pos*100:.0f}% · 고점 대비 {(cur/hi-1)*100:+.1f}%", fontsize=12.5, fontweight="bold", color=TXT, ha="left", va="bottom", transform=h.transAxes)
        a = fig.add_subplot(gs[i*3+1]); a.set_facecolor(CARD)
        a.plot(x, m["m5"], color="#4cc9f0", lw=2.4, label="5일선")
        a.plot(x, m["m20"], color="#ff9f68", lw=2.4, ls="--", label="20일선")
        a.plot(x, c, color=GOLD, lw=3.2, marker="o", ms=9, label="종가", zorder=5)
        allv = c + m["m5"] + m["m20"]; lo2, hi2 = min(allv), max(allv); pad = (hi2-lo2)*0.35 or 1
        a.set_ylim(lo2-pad*1.3, hi2+pad*2.0); a.set_xlim(-0.4, 4.4)
        for xi, (y, g) in enumerate(zip(c, m["chg"])):
            a.annotate(f"{y:,.2f}", (xi, y), textcoords="offset points", xytext=(0, 26), ha="center", color="white", fontsize=14, fontweight="bold")
            a.annotate(f"{g:+.1f}%", (xi, y), textcoords="offset points", xytext=(0, 10), ha="center", color=UP if g >= 0 else DN, fontsize=12, fontweight="bold")
        a.annotate(f"5일 {m['m5'][-1]:,.2f}", (4, m["m5"][-1]), textcoords="offset points", xytext=(-6, -20), ha="right", color="#4cc9f0", fontsize=12, fontweight="bold")
        a.annotate(f"20일 {m['m20'][-1]:,.2f}", (4, m["m20"][-1]), textcoords="offset points", xytext=(-6, -20), ha="right", color="#ff9f68", fontsize=12, fontweight="bold")
        a.set_title("주가 (종가, $) · 등락률 · 5일선·20일선", loc="left", color=SUB, fontsize=14, pad=10)
        a.legend(loc="upper left", facecolor=CARD, edgecolor="none", labelcolor=TXT, fontsize=12)
        a.set_xticks(x); a.set_xticklabels([]); a.tick_params(colors=SUB, labelsize=12, length=0)
        a.grid(axis="y", color="#2d3f55", lw=1)
        for sp in a.spines.values(): sp.set_visible(False)
        b = fig.add_subplot(gs[i*3+2]); b.set_facecolor(CARD)
        b.bar(x, [v/1e6 for v in m["v5"]], color=[GOLD if q == 4 else "#5b7a99" for q in x], width=0.55)
        b.plot(x, [v/1e6 for v in m["avg"]], color="white", lw=2, ls=":", marker="_", ms=26, label="직전 20일 평균", zorder=5)
        for xi, (v, r) in enumerate(zip(m["v5"], m["ratio"])):
            b.annotate(f"{v/1e6:.2f}M", (xi, v/1e6), textcoords="offset points", xytext=(0, 22), ha="center", color="white", fontsize=13, fontweight="bold")
            b.annotate(f"×{r:.1f}", (xi, v/1e6), textcoords="offset points", xytext=(0, 6), ha="center", color=DN if r >= 2 else SUB, fontsize=13, fontweight="bold")
        b.set_ylim(0, max(m["v5"])/1e6*1.4); b.set_xlim(-0.4, 4.4)
        b.set_title("거래량 (백만 주) · 20일 평균 대비 배수 (빨강 = 2배 이상)", loc="left", color=SUB, fontsize=14, pad=10)
        b.legend(loc="upper center", facecolor=CARD, edgecolor="none", labelcolor=TXT, fontsize=11)
        b.set_xticks(x); b.set_xticklabels([label(d) for d in m["dates5"]], color=TXT, fontsize=13)
        b.tick_params(axis="y", colors=SUB, labelsize=12, length=0)
        b.grid(axis="y", color="#2d3f55", lw=1); b.set_axisbelow(True)
        for sp in b.spines.values(): sp.set_visible(False)
    fig.text(0.055, 0.3/H, "※ 자료: 공개 시세(Yahoo Finance·StockAnalysis 등). 20일 평균 = 해당일 직전 20거래일 평균. 정보 제공용이며 투자 권유가 아닙니다.", fontsize=10.5, color="#7d90a6")
    fig.savefig(out, facecolor=BG)

def col(i):  # 0-based -> A1 letters
    s = ""
    i += 1
    while i: i, r = divmod(i-1, 26); s = chr(65+r) + s
    return s

def make_csv(data, out):
    stocks = data["stocks"]
    N = 5 + sum(len(s["closes"]) for s in stocks) + 3
    rows = [[""]*(11+len(stocks)) for _ in range(max(N, 50))]
    def put(r, c, v): rows[r-1][c] = v
    put(1, 0, "S&P500 저평가·거래량급증 종목 분석")
    put(2, 0, f"기준일 {data['asof']}(직전 미국 거래일). 이동평균·배수·등락률은 아래 일별 데이터에서 계산한 값입니다.")
    for j, h in enumerate(["종목","날짜","종가($)","거래량(주)","등락률(%)","직전20일 평균거래량","거래량 배수","5일선","20일선"]): put(4, j, h)
    put(4, 10, "항목")
    labels = ["회사 소개","P/E (입력)","PEG (입력)","시가총액 ($B, 입력)","52주 저가 ($, 입력)","52주 고가 ($, 입력)",
              "직전영업일 종가 ($)","52주 범위 내 위치(%)","52주 고점 대비(%)","주간 등락률(%) 5거래일 전 종가→직전영업일 종가",
              "전체 기간 등락률(%) 첫날 종가→직전영업일 종가","5일선 ($)","20일선 ($)","종가 vs 5일선(%)","5일선 vs 20일선(%)",
              "직전영업일 거래량 배수(직전 20일 평균 대비)","최근 5일 중 최대 배수","최근 5일 중 2배 이상인 날 수","일 등락률 변동성(최근 20일, 표준편차 %)"]
    for i, t in enumerate(labels): put(5+i, 10, t)
    r0 = 5
    for si, s in enumerate(stocks):
        n = len(s["closes"]); end = r0+n-1; sc = col(11+si)
        put(4, 11+si, s["ticker"])
        for k in range(n):
            r = r0+k
            put(r, 0, s["ticker"]); put(r, 1, s["dates"][k]); put(r, 2, s["closes"][k]); put(r, 3, s["vols"][k])
            if k >= 1: put(r, 4, f"=ROUND((C{r}/C{r-1}-1)*100,2)")
            if k >= 20:
                put(r, 5, f"=ROUND(AVERAGE(D{r-20}:D{r-1}),0)"); put(r, 6, f"=ROUND(D{r}/F{r},2)")
            if k >= 4: put(r, 7, f"=ROUND(AVERAGE(C{r-4}:C{r}),2)")
            if k >= 19: put(r, 8, f"=ROUND(AVERAGE(C{r-19}:C{r}),2)")
        c = 11+si
        vals = [s.get("desc",""), s.get("pe",""), s.get("peg",""), s.get("mcap_b",""), s["lo52"], s["hi52"],
                f"=C{end}",
                f"=ROUND(({sc}11-{sc}9)/({sc}10-{sc}9)*100,0)",
                f"=ROUND(({sc}11/{sc}10-1)*100,1)",
                f"=ROUND((C{end}/C{end-4}-1)*100,1)",
                f"=ROUND((C{end}/C{r0}-1)*100,1)",
                f"=H{end}", f"=I{end}",
                f"=ROUND(({sc}11/{sc}16-1)*100,1)",
                f"=ROUND(({sc}16/{sc}17-1)*100,1)",
                f"=G{end}", f"=MAX(G{end-4}:G{end})", f'=COUNTIF(G{end-4}:G{end},">=2")',
                f"=ROUND(STDEV(E{end-19}:E{end}),2)"]
        for i, v in enumerate(vals): put(5+i, c, v)
        r0 += n
    nr = 26
    put(nr, 10, "해석 (공부용 정리, 투자 권유 아님)")
    for i, t in enumerate(data.get("notes", [])): put(nr+1+i, 10, t)
    put(nr+len(data.get("notes", []))+2, 10, "직전 20일 평균 = 해당일 직전 20거래일 거래량 평균. 배수가 2 이상이면 급증으로 봄. 정보 제공용이며 투자 권유가 아닙니다.")
    buf = io.StringIO(); w = csv.writer(buf, lineterminator="\n")
    last = max(i for i, r in enumerate(rows) if any(r))
    for r in rows[:last+1]: w.writerow(r)
    open(out, "w", encoding="utf-8").write(buf.getvalue().rstrip("\n"))

if __name__ == "__main__":
    inp, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    data = json.load(open(inp, encoding="utf-8"))
    setup_font()
    make_png(data, os.path.join(outdir, "report.png"))
    make_csv(data, os.path.join(outdir, "analysis.csv"))
    print("ok", len(data["stocks"]), "stocks")
