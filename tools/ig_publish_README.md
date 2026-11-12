# 인스타 공식 API 예약 게시

- 대기열: `social/YYYYMMDD/queue.json` (형식은 `tools/ig_publish.py` 머리말)
- 10분마다 GitHub Actions(`.github/workflows/ig-publish.yml`)가 시각이 된 글을 게시하고
  `social/YYYYMMDD/published.json` 에 결과를 적는다. 시각은 5~20분 늦을 수 있다.
- 예정 시각을 3시간 넘긴 글은 올리지 않고 건너뛴다. 같은 글이 3번 실패하면 실패로 확정한다.
- 저장소 Secrets: `IG_USER_ID`, `IG_ACCESS_TOKEN` (Instagram 로그인 방식 토큰, 약 60일 유효 → 만료 전 재발급 필요). 없으면 아무것도 게시하지 않는다
- 이미지는 JPG 만 된다(PNG 불가). 영상은 MP4.
