#!/usr/bin/env python3
"""인스타그램 공식 API로 지난 14일 게시물 성과를 모아 report/weekly/ 에 저장한다.

환경 변수: IG_USER_ID, IG_ACCESS_TOKEN, IG_API_BASE(기본 https://graph.instagram.com), IG_GRAPH_VERSION
출력: report/weekly/YYYYMMDD.json (실행일 기준, 한국 시간)
토큰은 출력하지 않는다. 한 지표가 실패해도 나머지를 계속 모은다.
사용: python3 -I tools/ig_report.py [저장소 경로]
"""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
VER = os.environ.get("IG_GRAPH_VERSION", "").strip()
BASE = os.environ.get("IG_API_BASE", "https://graph.instagram.com").rstrip("/") + ("/" + VER if VER else "")
KST = dt.timezone(dt.timedelta(hours=9))
METRICS = ["views", "reach", "saved", "shares", "total_interactions"]


def scrub(t):
    return t.replace(TOKEN, "***") if TOKEN else t


def get(path, params):
    url = BASE + "/" + path + "?" + urllib.parse.urlencode(dict(params, access_token=TOKEN))
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(scrub("HTTP %s %s" % (e.code, e.read().decode(errors="replace")[:200])))
    except urllib.error.URLError as e:
        raise RuntimeError(scrub("연결 오류 %s" % e.reason))


def media_list(since):
    out, url_params = [], {
        "fields": "id,caption,media_type,media_product_type,permalink,timestamp,like_count,comments_count",
        "limit": 50}
    page = get("me/media", url_params)
    while True:
        for m in page.get("data", []):
            ts = dt.datetime.fromisoformat(m["timestamp"].replace("Z", "+00:00").replace("+0000", "+00:00"))
            if ts < since:
                return out
            m["time_kst"] = ts.astimezone(KST).strftime("%Y-%m-%d %H:%M")
            out.append(m)
        nxt = (page.get("paging") or {}).get("next")
        if not nxt:
            return out
        with urllib.request.urlopen(nxt, timeout=60) as r:
            page = json.loads(r.read().decode())


def insights(mid):
    res = {}
    for name in METRICS:  # 지표별로 따로 불러 한 지표 실패가 전체를 막지 않게 한다
        try:
            d = get(mid + "/insights", {"metric": name})
            vals = (d.get("data") or [{}])[0].get("values") or [{}]
            res[name] = vals[0].get("value")
        except Exception as e:
            res[name] = None
    return res


def main():
    if not TOKEN:
        print("IG_ACCESS_TOKEN 이 없어 보고서를 만들지 않음")
        return 0
    now = dt.datetime.now(dt.timezone.utc)
    items = []
    for m in media_list(now - dt.timedelta(days=14)):
        row = {k: m.get(k) for k in ("id", "time_kst", "media_product_type", "media_type",
                                      "permalink", "like_count", "comments_count")}
        row["caption_head"] = (m.get("caption") or "").strip().split("\n")[0][:60]
        row["caption"] = (m.get("caption") or "")[:300]
        row.update(insights(m["id"]))
        items.append(row)
    acct = {}
    try:
        acct = get("me", {"fields": "username,followers_count,media_count"})
    except Exception as e:
        acct = {"error": scrub(str(e))[:120]}
    today = now.astimezone(KST).strftime("%Y%m%d")
    out = {"generated_kst": now.astimezone(KST).strftime("%Y-%m-%d %H:%M"),
           "account": acct, "items": items}
    d = os.path.join(ROOT, "report", "weekly")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, today + ".json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("게시물 %d개 저장: report/weekly/%s.json" % (len(items), today))
    return 0


if __name__ == "__main__":
    sys.exit(main())
