#!/usr/bin/env python3
"""인스타그램 공식 API(콘텐츠 게시)로 예약 대기열을 게시한다.

대기열: social/YYYYMMDD/queue.json
  [{"id": "post1",
    "time": "2026-11-13T09:10:00+09:00",   # 게시 시각(시간대 포함)
    "type": "REELS",                        # REELS | IMAGE | CAROUSEL
    "media": ["https://raw.githubusercontent.com/.../post1.mp4"],
    "caption": "설명글 전문"}]
결과: social/YYYYMMDD/published.json  (id -> 상태). 이미 기록된 id 는 다시 올리지 않는다.

환경 변수
  IG_USER_ID       인스타그램 비즈니스 계정 ID
  IG_ACCESS_TOKEN  게시 권한(instagram_content_publish)이 있는 토큰
  IG_GRAPH_VERSION (선택) 예: v25.0. 비우면 앱 기본 버전
  IG_DRY_RUN=1     실제 호출 없이 게시 대상만 출력
  IG_STALE_MIN     (선택) 이 분 수보다 오래 지난 글은 건너뜀. 기본 180

사용: python3 -I tools/ig_publish.py [저장소 경로]
토큰은 절대 출력하지 않는다.
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
IG_ID = os.environ.get("IG_USER_ID", "").strip()
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
VER = os.environ.get("IG_GRAPH_VERSION", "").strip()
DRY = os.environ.get("IG_DRY_RUN", "") == "1"
STALE_MIN = int(os.environ.get("IG_STALE_MIN", "180"))
BASE = os.environ.get("IG_API_BASE", "https://graph.facebook.com").rstrip("/") + ("/" + VER if VER else "")
KST = dt.timezone(dt.timedelta(hours=9))


def scrub(text):
    return text.replace(TOKEN, "***") if TOKEN else text


def call(method, path, params):
    params = dict(params, access_token=TOKEN)
    data = urllib.parse.urlencode(params)
    url = BASE + "/" + path
    if method == "GET":
        req = urllib.request.Request(url + "?" + data)
    else:
        req = urllib.request.Request(url, data=data.encode())
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(scrub("HTTP %s %s" % (e.code, body[:500])))
    except urllib.error.URLError as e:
        raise RuntimeError(scrub("연결 오류 %s" % e.reason))


def wait_ready(container_id, limit_sec=420):
    """영상 처리 완료(FINISHED)까지 기다린다."""
    start = time.time()
    while time.time() - start < limit_sec:
        st = call("GET", container_id, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError("영상 처리 실패: %s" % st.get("status", code))
        time.sleep(10)
    raise RuntimeError("영상 처리 시간 초과")


def container(item, url, carousel_child=False):
    is_video = url.lower().split("?")[0].endswith((".mp4", ".mov"))
    p = {}
    if is_video:
        p["video_url"] = url
        p["media_type"] = "VIDEO" if carousel_child else "REELS"
        if not carousel_child:
            p["share_to_feed"] = "true"
    else:
        p["image_url"] = url
    if carousel_child:
        p["is_carousel_item"] = "true"
    else:
        p["caption"] = item.get("caption", "")
    cid = call("POST", IG_ID + "/media", p)["id"]
    if is_video:
        wait_ready(cid)
    return cid


def publish(item):
    media = item.get("media") or []
    kind = (item.get("type") or "").upper()
    if not media:
        raise RuntimeError("media 가 비어 있음")
    if kind == "CAROUSEL" or len(media) > 1:
        kids = [container(item, u, carousel_child=True) for u in media]
        cid = call("POST", IG_ID + "/media", {
            "media_type": "CAROUSEL", "children": ",".join(kids),
            "caption": item.get("caption", "")})["id"]
    else:
        cid = container(item, media[0])
    return call("POST", IG_ID + "/media_publish", {"creation_id": cid})["id"]


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def main():
    now = dt.datetime.now(dt.timezone.utc)
    if not DRY and not (IG_ID and TOKEN):
        print("IG_USER_ID / IG_ACCESS_TOKEN 이 없어 게시하지 않음(설정 전).")
        return 0
    social = os.path.join(ROOT, "social")
    days = sorted(d for d in os.listdir(social) if d.isdigit())[-3:]
    failed = 0
    for day in days:
        qpath = os.path.join(social, day, "queue.json")
        queue = load(qpath, None)
        if not queue:
            continue
        ppath = os.path.join(social, day, "published.json")
        done = load(ppath, {})
        changed = False
        for item in queue:
            pid = str(item.get("id", ""))
            if not pid or pid in done:
                continue
            try:
                when = dt.datetime.fromisoformat(item["time"])
                if when.tzinfo is None:
                    when = when.replace(tzinfo=KST)
            except (KeyError, ValueError):
                done[pid] = {"status": "error", "reason": "time 형식 오류"}
                changed, failed = True, failed + 1
                continue
            if when > now:
                continue
            late = (now - when).total_seconds() / 60
            stamp = now.astimezone(KST).strftime("%Y-%m-%d %H:%M")
            if late > STALE_MIN:
                done[pid] = {"status": "skipped", "at": stamp,
                             "reason": "예정 시각을 %d분 넘김" % late}
                changed = True
                print("건너뜀 %s/%s (%d분 지남)" % (day, pid, late))
                continue
            if DRY:
                print("게시 대상 %s/%s %s %s" % (day, pid, item.get("type"), item["time"]))
                continue
            try:
                mid = publish(item)
                done[pid] = {"status": "published", "at": stamp, "media_id": mid}
                print("게시 완료 %s/%s" % (day, pid))
            except Exception as e:  # 한 글의 실패가 다른 글을 막지 않게 한다
                msg = scrub(str(e))[:300]
                print("게시 실패 %s/%s: %s" % (day, pid, msg))
                failed += 1
                # 2회까지는 다음 실행에서 다시 시도, 그 뒤에는 실패로 확정
                fails = done.get("_fails", {})
                fails[pid] = fails.get(pid, 0) + 1
                done["_fails"] = fails
                if fails[pid] >= 3:
                    done[pid] = {"status": "failed", "at": stamp, "reason": msg}
                    del fails[pid]
            changed = True
        if changed and not DRY:
            with open(ppath, "w", encoding="utf-8") as f:
                json.dump(done, f, ensure_ascii=False, indent=1)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
