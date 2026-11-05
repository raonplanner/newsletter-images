# 지난 밤 해외경제 이슈 릴스 템플릿

사용: `python3 -I tools/reel_econ.py 입력.json 출력.mp4 [프레임확인폴더]`

- 9:16(1080x1920) 20초 무음 mp4. 필요: ffmpeg, Pillow, numpy, Noto Sans CJK(ttc index=1).
- 입력 형식은 reel_econ_sample.json 참고 (date_label, indices 3개, issues 2~3개, schedule, creds, cta).
- 지수 값과 이슈 문구는 확인된 값만 넣는다. 정치·정당 표현, 확인되지 않은 가격 수치는 쓰지 않는다.
- 면책 문구는 영상이 아니라 캡션 끝에 넣는다: "참고용 정보이며 투자 권유가 아닙니다."
