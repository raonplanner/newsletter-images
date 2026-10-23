# 소식지 렌더러

`python3 -I tools/render.py 입력.json 출력폴더` → `post.png`(페이스북용), `mail.png`(메일 첨부용, base64 28,000자 이하).
`data/ndx_monthly.csv`(나스닥100 월말 종가, 1985.10~)의 해당 월 값을 그날 종가로 갱신한다.

입력 JSON (선택 항목 `"subtitle":"그날의 한 줄 부제"` — 있으면 제목 아래에 표시, 없으면 생략):
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

# 메일 본문 생성기

`python3 -I tools/mail_html.py 입력.json 출력폴더 [이미지주소]` → `mail.html`(Gmail htmlBody), `mail.txt`(일반 텍스트 body).
입력 JSON은 위와 같고 `"greeting":"인사말 한 줄"`을 더한다. 이미지 없이 표로 소식지를 그린다
(Gmail 도구가 외부 `<img>`와 style의 `background:` 줄임 표기를 지우므로 `bgcolor`/`background-color`만 쓴다).
