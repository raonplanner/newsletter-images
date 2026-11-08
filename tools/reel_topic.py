#!/usr/bin/env python3
"""코너 글용 20초 세로 릴스(1080x1920, 합성 배경음악). reel_promo.py 의 그리기 함수를 재사용한다.
사용: python3 -I reel_topic.py 입력.json 출력.mp4 [프레임폴더]
입력: {"theme":"fire|life|pension|doctor|medic|tax|check|estate|etc","label":"의원 화재보험 점검(약 14자)","title":"제목(약 16자, 2줄 이내)",
 "points":["항목(약 26자)",3~5개],"cta_extra":"(선택) 🔥 화재보험 견적신청·상담신청","note":"(선택) 면책 한 줄(약 30자)","cta":["지금 바로","상담 받으세요"](선택, 2줄 각 10자 이내)}
프레임 확인: f_1.8.png(첫 화면) f_9.5.png(항목) f_18.5.png(마무리)"""
import sys, json, subprocess, os, tempfile, importlib.util
here=os.path.dirname(os.path.abspath(__file__))
sp=importlib.util.spec_from_file_location("rp",os.path.join(here,"reel_promo.py")); rp=importlib.util.module_from_spec(sp); sp.loader.exec_module(rp)
globals().update({k:getattr(rp,k) for k in "W H FPS DUR F ease fade wrap layer ctext apply grad pill logo_on dots make_music PAL NAVY YEL WHITE Image ImageDraw".split()})
THEMES={"fire":[((190,60,30),(110,20,60)),((235,110,40),(200,40,70))],
        "life":[((25,40,140),(20,120,190)),((40,60,170),(20,150,200))],
        "pension":[((8,90,105),(22,150,120)),((10,110,120),(40,170,110))],
        "doctor":[((11,37,69),(27,75,130)),((20,50,95),(40,95,150))],
        "medic":[((18,55,42),(47,107,79)),((25,75,55),(60,125,95))],
        "tax":[((15,61,62),(31,122,122)),((20,80,80),(40,140,135))],
        "check":[((45,27,78),(91,58,140)),((60,38,100),(110,70,160))],
        "estate":[((30,38,48),(58,71,87)),((40,50,62),(75,90,108))],
        "etc":[((38,28,110),(142,45,150)),((60,40,130),(160,60,160))]}
def render(cfg,out,fd=None):
    th=THEMES.get(cfg.get("theme","etc"),THEMES["etc"]); b1,b2=grad(*th[0]),grad(*th[1])
    wav=os.path.join(tempfile.mkdtemp(),"bgm.wav"); make_music(wav)
    td=ImageDraw.Draw(Image.new("RGB",(W,H)))
    clean=lambda x:"".join(c for c in x if ord(c)<0x2000 or 0x3000<=ord(c)<0xD7B0 or c in "·—→").replace("☐","").strip()
    pts=[clean(x) for x in cfg["points"][:5]]; cfg["title"]=clean(cfg["title"]); TOP,BOT=470,1800
    for hs,bs in [(112,66),(104,62),(96,58),(88,54),(80,50),(72,46)]:
        fh,fb=F(hs),F(bs); hl=wrap(td,cfg["title"],fh,W-120)
        if len(hl)>2: continue
        bl=[wrap(td,b,fb,W-60-200-45) for b in pts]
        ch=[len(x)*(bs+14)+56 for x in bl]; tot=sum(ch)+26*(len(ch)-1)
        if tot<=BOT-TOP-(len(hl)-1)*(hs+10): break
    ty0=max(300+len(hl)*(hs+10)+30,TOP); extra=max(0,(BOT-ty0-tot)//(len(ch)+1))
    lab=cfg["label"]; ex="".join(c for c in cfg.get("cta_extra","") if ord(c)<0x2000).strip(); note=cfg.get("note","")
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",wav,"-shortest",
         "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-movflags","+faststart","-c:a","aac","-b:a","128k",out]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
    marks={int(x*FPS) for x in (1.8,9.5,18.5)}
    for i in range(FPS*DUR):
        t=i/FPS; im=(b2 if t>=4.2 else b1).copy()
        if 0<=t-4.2<0.5: im=Image.blend(b1,b2,ease((t-4.2)/0.5))
        dots(im,t)
        a=fade(t,0,0.6,3.6,4.2)
        if a>0:
            L,d=layer(); logo_on(L,110)
            pill(d,W/2,430,lab,F(80),YEL,NAVY)
            y=640
            for ln in hl: ctext(d,ln,y,F(hs+20),WHITE); y+=hs+40
            d.rounded_rectangle((W/2-110,y+30,W/2+110,y+44),radius=7,fill=YEL)
            ctext(d,"송근영 FP",1500,F(80),YEL); ctext(d,"메트라이프금융서비스",1620,F(60),WHITE)
            im=apply(im,L,a,dy=(1-a)*40)
        a=fade(t,4.2,4.8,15.2,15.8)
        if a>0:
            L,d=layer(); ctext(d,lab,190,F(52),YEL); y=300
            for ln in hl: ctext(d,ln,y,F(hs),WHITE); y+=hs+10
            y=ty0+extra
            for k,lines in enumerate(bl):
                ak=ease((t-(5.3+k*0.6))/0.45); h=ch[k]
                if ak>0:
                    c=PAL[k%len(PAL)]; cl,cd=layer()
                    cd.rounded_rectangle((60,y,W-60,y+h),radius=36,fill=c)
                    cd.ellipse((90,y+h/2-42,174,y+h/2+42),fill=NAVY)
                    nw=cd.textlength(str(k+1),font=F(52)); cd.text((132-nw/2,y+h/2-34),str(k+1),font=F(52),fill=c)
                    ty=y+28
                    for ln in lines: cd.text((200,ty),ln,font=F(bs),fill=NAVY); ty+=bs+14
                    cl.putalpha(cl.getchannel('A').point(lambda v:int(v*ak))); L.paste(cl,(int((1-ak)*120),0),cl)
                y+=h+26+extra
            im=apply(im,L,a)
        a=ease((t-15.8)/0.6)
        if a>0:
            L,d=layer()
            c1,c2=(cfg.get("cta") or ["궁금한 점은","DM으로 문의하세요"])[:2]
            ctext(d,c1,300,F(110),WHITE); ctext(d,c2,440,F(120 if len(c2)<=10 else 100),YEL)
            d.rounded_rectangle((W/2-110,620,W/2+110,634),radius=7,fill=YEL)
            pill(d,W/2,720,"상담신청 · 프로필 링크",F(70),NAVY,YEL)
            if ex: pill(d,W/2,880,ex,F(54),WHITE,NAVY)
            ctext(d,"송근영",1100,F(130),YEL); ctext(d,"메트라이프금융서비스",1280,F(84),WHITE)
            if note: ctext(d,note,1480,F(40),WHITE)
            logo_on(L,1650)
            im=apply(im,L,a,dy=(1-a)*30)
        rgb=im.convert("RGB")
        if fd and i in marks: rgb.save(os.path.join(fd,f"f_{i/FPS:.1f}.png"))
        p.stdin.write(rgb.tobytes())
    p.stdin.close(); p.wait()
if __name__=="__main__":
    cfg=json.load(open(sys.argv[1],encoding="utf-8")); fd=sys.argv[3] if len(sys.argv)>3 else None
    if fd: os.makedirs(fd,exist_ok=True)
    render(cfg,sys.argv[2],fd)
