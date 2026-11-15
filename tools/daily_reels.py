#!/usr/bin/env python3
"""매일 릴스 자동 제작(GitHub Actions 06:17 KST). 사용: python3 -I tools/daily_reels.py [저장소경로]
- 일출(대전) 기준 슬롯 +2/+6/+10/+14h, 평일 16:05~17:35 는 17:40, 주말은 3개.
- 구성 A/B 날짜 홀짝 교대: A=경제/의사/세제/가입자점검, B=경제/의료인/생명보험/연금, 화·금 4번째=화재보험.
- 경제 릴스는 Yahoo Finance 종가(공개 조회)로 자동 생성, 조회 실패·휴장이면 다른 소재로 대체.
- 소재 은행: tools/reel_bank.json (날짜 기반 순환). 결과: social/YYYYMMDD/{post*.mp4,queue.json,log.txt}
인스타 게시는 ig-publish 워크플로가 queue.json 으로 처리한다."""
import sys, os, json, math, datetime as dt, urllib.request, importlib.util
repo=os.path.abspath(sys.argv[1] if len(sys.argv)>1 else ".")
here=os.path.dirname(os.path.abspath(__file__))
sp=importlib.util.spec_from_file_location("rs",os.path.join(here,"reel_scenes.py")); rs=importlib.util.module_from_spec(sp); sp.loader.exec_module(rs)
KST=dt.timezone(dt.timedelta(hours=9)); now=dt.datetime.now(KST); today=now.date(); ymd=today.strftime("%Y%m%d")
out=os.path.join("/tmp/dry" if os.environ.get("DAILY_DRY") else os.path.join(repo,"social"),ymd); os.makedirs(out,exist_ok=True)
if os.path.exists(os.path.join(out,"queue.json")): print("이미 오늘 대기열이 있음 -> 종료"); sys.exit(0)
bank=json.load(open(os.path.join(here,"reel_bank.json"),encoding="utf8"))
RAW="https://raw.githubusercontent.com/raonplanner/newsletter-images/main/social/%s/post%d.mp4"
def sunrise(d,lat=36.35,lon=127.38):
    n=d.toordinal()-dt.date(2000,1,1).toordinal()+0.0008-lon/360
    M=(357.5291+0.98560028*n)%360; C=1.9148*math.sin(math.radians(M))+0.02*math.sin(math.radians(2*M))
    lam=(M+C+180+102.9372)%360; J=2451545+n+0.0053*math.sin(math.radians(M))-0.0069*math.sin(math.radians(2*lam))
    dec=math.asin(math.sin(math.radians(lam))*math.sin(math.radians(23.44)))
    w=math.acos((math.sin(math.radians(-0.833))-math.sin(math.radians(lat))*math.sin(dec))/(math.cos(math.radians(lat))*math.cos(dec)))
    Jr=J-math.degrees(w)/360  # 율리우스일(UTC)
    t=dt.datetime(2000,1,1,12,tzinfo=dt.timezone.utc)+dt.timedelta(days=Jr-2451545)
    return t.astimezone(KST)
sr=sunrise(today); wd=today.weekday()  # 0=월
base=sr.replace(second=0,microsecond=0)
def slot(h):
    t=base+dt.timedelta(hours=h); m=(t.minute+2)//5*5; t=t.replace(minute=0)+dt.timedelta(minutes=m)
    if wd<5 and dt.time(16,5)<=t.time()<=dt.time(17,35): t=t.replace(hour=17,minute=40)
    return t
slots=[slot(2),slot(6),base.replace(hour=19,minute=40)]  # 하루 3개: 아침·낮·저녁(19:40)
def yahoo(sym):
    if os.environ.get('YAHOO_MOCK'):  # 시험용
        return [(dt.date.fromisoformat(a),b) for a,b in json.load(open(os.environ['YAHOO_MOCK']))[sym]]
    u=f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(sym)}?range=10d&interval=1d"
    for _ in range(3):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=20)
            j=json.load(r)["chart"]["result"][0]; ts=j["timestamp"]; cl=j["indicators"]["quote"][0]["close"]; off=j["meta"].get("gmtoffset",0)
            pts=[(dt.datetime.utcfromtimestamp(t+off).date(),c) for t,c in zip(ts,cl) if c is not None]
            return pts
        except Exception as e: err=e
    raise err
def econ():
    names=[("다우존스","^DJI"),("S&P500","^GSPC"),("나스닥","^IXIC")]; rows=[]; dates=set()
    for n,s in names:
        p=yahoo(s); (d1,c1),(d0,c0)=p[-1],p[-2]; dates.add(d1); rows.append([n,round(c1,2),round((c1/c0-1)*100,2)])
    d=max(dates)
    if len(dates)!=1 or (today-d).days>4 or wd==6: return None   # 휴장·불일치·일요일
    fx=yahoo("KRW=X"); tn=yahoo("^TNX"); f1,f0=fx[-1][1],fx[-2][1]; t1=tn[-1][1]
    day=["월","화","수","목","금","토","일"][d.weekday()]
    return {"date":d,"day":day,"rows":rows,"fx":(round(f1,2),round((f1/f0-1)*100,2)),"tn":round(t1,2)}
def econ_reel(e):
    r=e["rows"]; up=sum(1 for x in r if x[2]>0)
    word="세 지수 모두 상승 마감" if up==3 else "세 지수 모두 하락 마감" if up==0 else "지수별로 엇갈린 마감"
    top=max(r,key=lambda x:abs(x[2]))
    when="어젯밤" if (today-e["date"]).days<=1 else f"지난 {e['day']}요일"
    fxs=f"{e['fx'][0]:,.2f}원 ({e['fx'][1]:+.2f}%)"
    cfg={"label":"지난 밤 해외경제","scenes":[
     {"style":"q","lines":[f"{when} 미국 증시, 어떻게 마감했을까요?"]},
     {"style":"indices","head":f"{e['date'].month}/{e['date'].day}({e['day']}) 미국 증시 마감","rows":r,"foot":word},
     {"style":"card","head":"원/달러 환율","lines":[f"{fxs}","환율은 수입물가와 해외투자에 영향을 줘요"]},
     {"style":"card","head":"미국 10년물 금리","lines":[f"{e['tn']:.2f}%","금리가 오르면 성장주에 부담이 될 수 있어요"]},
     {"style":"close","line":"이렇게 확인하는 게 좋아요","sub":"지수·환율·금리를 함께 보며 흐름 읽기","note":"참고용 정보이며 투자 권유가 아닙니다"}]}
    cap=(f"{when} 미국 증시, 어떻게 마감했을까요? 📉\n"+" · ".join(f"{n} {v:,.2f} ({p:+.2f}%)" for n,v,p in r)+
         f"\n{word}. 원/달러 {fxs}, 미국 10년물 금리 {e['tn']:.2f}%예요.\n💬 궁금한 점은 DM으로 남겨주세요 (프로필 링크 → 상담신청)\n참고용 정보이며 투자 권유가 아닙니다.\n#생명보험 #비과세 #연금 #경제공부 #재테크")
    return cfg,cap
def topic_reel(it):
    # 호기심 유발형: 핵심 포인트 2개만 짧게 보여 주고 자세한 내용은 DM으로 유도(구체 설명·수치는 싣지 않음)
    cards=it["cards"][:2]
    sc=[{"style":"q","lines":[it["q"]]}]+[{"style":"card","head":h,"lines":l} for h,l in cards]
    sc.append({"style":"close","line":"이렇게 확인해 보는 게 좋아요","sub":"내 경우는 어떨지 궁금하다면","note":it["note"],**({"extra":it["extra"]} if it.get("extra") else {})})
    cfg={"label":it["label"],"calm":it.get("calm",False),"scenes":sc}
    cta="💬 "+("화재보험 견적신청·상담신청은 " if it.get("extra") else "자세한 내용이 궁금하다면 ")+"DM으로 남겨주세요 (프로필 링크 → 상담신청)"
    cap=it["q"]+"\n"+"\n".join("✔ "+h for h,_ in cards)+"\n"+it["note"]+".\n"+cta+"\n#생명보험 #비과세 #연금 "+it["tags"]
    return cfg,cap
n=today.toordinal(); AB="A" if n%2==0 else "B"; ix=(n//2)%4
pick=lambda k,off=0: bank[k][((((n-2)//4)*2+n%2)%len(bank[k])) if k=="worker" else ((n//4+off)%len(bank[k]))]
WK=(n//2)%2==1  # 2번째 슬롯: 의사·의료인 코너와 직장인 직종 코너 번갈아
plan=[("econ",None),("worker" if WK else ("doctor" if AB=="A" else "medic"),None),(["tax","life","pension","check"][n%4],None)]  # 3번째 슬롯: 세금·생명보험·연금·가입자점검 4일 주기 순환
if wd in (1,4): plan[2]=("fire",None)
reels=[]; log=[f"구성: {AB}\n{today} ({'월화수목금토일'[wd]}) 일출 {sr:%H:%M}. GitHub Actions 자동 제작(tools/daily_reels.py)."]
fb=False
for k,_ in plan:
    if k=="econ":
        try:
            e=econ()
        except Exception as ex: e=None; log.append(f"경제 릴스 조회 실패({type(ex).__name__}) -> 대체 소재")
        if e: reels.append(("해외경제 마감",)+econ_reel(e)); log.append(f"해외경제: {e['date']} 종가 {e['rows']} 환율 {e['fx']} 10년물 {e['tn']} (Yahoo Finance)"); continue
        if k=="econ" and not any("조회 실패" in x for x in log): log.append("경제 릴스 생략(휴장·일요일·날짜 불일치) -> 대체 소재")
        k="pension"; fb=True
    off=3 if k=="fire" and wd==4 else (1 if fb else 0)
    fb=False
    it=pick(k,off); reels.append((it["label"],)+topic_reel(it)); log.append(f"{it['label']}: {it['q']}")
queue=[]
EVENT_DAYS=(dt.date(2026,11,16),dt.date(2026,11,18),dt.date(2026,11,20))  # 11/21(토) 행사 안내: 4번째 릴스 대신(하루 5개 상한)
for i,(name,cfg,cap) in enumerate(reels[:min(len(slots),2 if today in EVENT_DAYS else len(slots))],1):
    f=os.path.join(out,f"post{i}.mp4"); rs.render(cfg,f)
    queue.append({"id":f"post{i}","time":slots[i-1].strftime("%Y-%m-%dT%H:%M:00+09:00"),"type":"REELS","media":[RAW%(ymd,i)],"caption":cap})
    log.append(f"슬롯 {slots[i-1]:%H:%M} post{i} = {name}")
if today in EVENT_DAYS:  # 월·수·금 21:05 행사 안내 릴스
    import shutil; shutil.copy(os.path.join(here,"assets","job_event.mp4"),os.path.join(out,"event.mp4"))
    cap=("📍대전 | 메트라이프금융서비스 직업설명회\n11/21(토) 오전 10:30, 직접 들어보세요.\n막연하게 모르는 것보다, 한 번 참석해 들어보는 것이 인생의 전환점이 될 수 있습니다.\n\n"
         "🗓 11/21(토) 오전 10:30 (매주 금요일 10:30~12:30에도 진행)\n📍 대전 서구 둔산대로117번길 34 4층 (만년동)\n📝 신청 https://naver.me/Fm3lll5s\n📞 010-3224-1517\n\n"
         "#대전서구 #대전유성구 #보험설계사 #채용 #취업")
    queue.append({"id":"event","time":today.strftime("%Y-%m-%dT21:05:00+09:00"),"type":"REELS","media":["https://raw.githubusercontent.com/raonplanner/newsletter-images/main/social/%s/event.mp4"%ymd],"caption":cap})
    log.append("슬롯 21:05 event = 11/21 행사 안내(4번째 릴스 대체)")
if wd==5 and today>=dt.date(2026,11,28):  # 토요일 21:05 직업설명회 릴스(매주)
    import shutil; shutil.copy(os.path.join(here,"assets","job_promo.mp4"),os.path.join(out,"promo.mp4"))
    cap=("📍대전 | 메트라이프금융서비스 직업설명회\n막연하게 모르는 것보다, 한 번 직접 들어보세요.\n인생의 전환점이 될 수 있습니다.\n\n"
         "🗓 매주 금요일 10:30~12:30\n📍 대전 서구 둔산대로117번길 34 4층 (만년동)\n📝 신청 https://naver.me/Fm3lll5s\n📞 010-3224-1517\n\n"
         "#대전서구 #대전유성구 #보험설계사 #채용 #취업")
    queue.append({"id":"promo","time":today.strftime("%Y-%m-%dT21:05:00+09:00"),"type":"REELS","media":["https://raw.githubusercontent.com/raonplanner/newsletter-images/main/social/%s/promo.mp4"%ymd],"caption":cap})
    log.append("슬롯 21:05 promo = 직업설명회")
json.dump(queue,open(os.path.join(out,"queue.json"),"w",encoding="utf8"),ensure_ascii=False,indent=1)
open(os.path.join(out,"log.txt"),"w",encoding="utf8").write("\n".join(log)+f"\n다음 구성: {'B' if AB=='A' else 'A'}\n")
print("\n".join(log))
