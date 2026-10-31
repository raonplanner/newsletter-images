#!/usr/bin/env python3
"""인스타그램 설명글(caption.txt) 생성기. 사용: python3 -I tools/caption.py 입력.json 출력폴더
설명글에는 ETF 종가·15년 수익률·링크를 넣지 않는다(이전 결정). 요일 칸은 image_cell 하나만 싣는다.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nl import *


def build(d):
    r = d.get("rows") or {}
    g1, g2 = greeting_lines(d)
    L = [f"{g1} {g2}", f"{date_short(d)} 소식지를 전해드려요."]
    s = summary(d)
    if s: L.append(f"■ 한 줄 요약\n{s}")
    L.append(corner_text(d["corner"]))
    kr = []
    for name, key in (("코스피", "kospi"), ("1달러", "usd"), ("100엔", "jpy")):
        if key in r:
            v, ch, _, _ = row_view(key, r[key])
            kr.append(f"{name} {v} {ch}".rstrip(" -") if v != "휴장" else f"{name} 휴장")
    if kr:
        L.append(f"■ 당일종가 (코스피·환율 {d.get('kr_date', '')}" + (" 휴장" if d.get("kr_closed") else "") + ")\n" + "\n".join(kr))
    if "ndx" in r:
        v, ch, _, _ = row_view("ndx", r["ndx"])
        L.append(f"■ 전일종가 (미국 {d.get('us_date', '')}" + (" 휴장" if d.get("us_closed") else "") + ")\n"
                 + (f"나스닥100 {v} {ch}" if v != "휴장" else "나스닥100 휴장"))
    cells = d.get("cells") or []
    if cells:
        c = cells[min(int(d.get("image_cell", 0)), len(cells) - 1)]
        L.append(cell_text(c))
    L.append(f"{SIGN} {PHONE}\n증권투자권유대행인(골든트리투자자문 소속, 등록번호 8217000309) · 변액보험판매관리사 · 펀드투자상담사")
    L.append("※ 본 자료는 정보 제공용이에요.")
    L.append(d.get("hashtags") or "#오늘의소식지 #연금저축 #IRP #경제동향 #코스피 #나스닥100 #환율")
    return "\n\n".join(L) + "\n"


def main():
    d = json.load(open(sys.argv[1], encoding="utf8"))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    text = build(d)
    bad = bad_words(text)
    if bad: raise SystemExit(f"설명글에 나가면 안 되는 문구: {bad}")
    open(os.path.join(out, "caption.txt"), "w", encoding="utf8").write(text)
    print(f"caption.txt {len(text)}자")


main()
