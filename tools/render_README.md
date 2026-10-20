# 소식지 렌더러

`python3 -I tools/render.py 입력.json 출력폴더` → `post.png`(페이스북용), `mail.png`(메일 첨부용, base64 28,000자 이하).
`data/ndx_monthly.csv`(나스닥100 월말 종가, 1985.10~)의 해당 월 값을 그날 종가로 갱신한다.

입력 JSON:
```
{"date_label":"2026년 10월 16일 금요일",
 "rows":{"kospi":{"v":"5,554.22","c":"7.57%","dir":"down"},
         "ndx":{"v":"29,935.59","c":"0.05%","dir":"down","num":29935.59,"date":"2026-10-15"},
         "usd":{"v":"1,344.60원","c":"6.30","dir":"up"},"jpy":{...},"wti":{"v":"$97.97","c":"2.88","dir":"up"}},
 "corner":{"type":"quote","quote":"...","who":"...","close":"..."}
        | {"type":"medical"|"news","items":[{"h":"소제목","b":"요약"}],"close":"(선택)"},
 "src":"증시 10/15 마감 · ... · 정보 제공용"}
```
dir: up/down/flat. 확인 불가 값은 v:"확인 불가", c:"-", dir:"flat". 나스닥100 num 은 숫자(종가).
