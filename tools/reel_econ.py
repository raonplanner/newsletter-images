#!/usr/bin/env python3
"""지난 밤 해외경제 이슈 릴스(9:16, 20초, 무음) 생성기.
사용: python3 -I reel_econ.py 입력.json 출력.mp4 [프레임확인폴더]
입력.json 형식은 reel_econ_sample.json 참고. 지수 값·이슈 문구는 검증된 값만 넣는다."""
import sys, json, subprocess, math, os
from PIL import Image, ImageDraw, ImageFont
W,H,FPS,DUR=1080,1920,30,20
RF="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BF="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def F(s,b=True): return ImageFont.truetype(BF if b else RF,s,index=1)
SKY=(124,196,242); WHITE=(255,255,255); SOFT=(176,196,214)
UP=(229,72,77); DOWN=(59,130,246); CARD=(36,56,78); CARDLN=(70,100,130)
def ease(t): t=max(0.0,min(1.0,t)); return 1-(1-t)**3
def fade(t,t0,t1,t2,t3):  # in at t0-t1, out at t2-t3
    return ease((t-t0)/(t1-t0))*(1-ease((t-t2)/(t3-t2))) if t3>t2 else ease((t-t0)/(t1-t0))
def wrap(d,text,font,maxw):
    lines=[];cur=""
    for word in text.split(" "):
        trial=(cur+" "+word).strip()
        if d.textlength(trial,font=font)<=maxw: cur=trial; continue
        if cur: lines.append(cur); cur=""
        if d.textlength(word,font=font)<=maxw: cur=word; continue
        piece=""
        for ch in word:
            if d.textlength(piece+ch,font=font)<=maxw: piece+=ch
            else: lines.append(piece); piece=ch
        cur=piece
    if cur: lines.append(cur)
    return lines
def build(cfg):
    bg=Image.new("RGB",(W,H)); px=bg.load()
    c1=(22,33,46); c2=(36,52,71)
    for y in range(H):
        t=y/(H-1); col=tuple(int(c1[i]*(1-t)+c2[i]*t) for i in range(3))
        for x in range(W): px[x,y]=col
    dd=ImageDraw.Draw(bg)
    dd.ellipse((760,-200,1300,340),outline=(46,70,96),width=6)
    dd.ellipse((-220,1560,360,2140),outline=(46,70,96),width=6)
    import numpy as np
    arr=np.asarray(bg).astype(np.int16)
    rng=np.random.default_rng(7)
    arr+=rng.integers(-2,3,(H,W,1),dtype=np.int16)
    bg=Image.fromarray(np.clip(arr,0,255).astype("uint8"))
    return bg
def layer(): 
    im=Image.new("RGBA",(W,H),(0,0,0,0)); return im,ImageDraw.Draw(im)
def tri(d,cx,cy,s,up,fill):
    pts=[(cx,cy-s),(cx-s,cy+s),(cx+s,cy+s)] if up else [(cx,cy+s),(cx-s,cy-s),(cx+s,cy-s)]
    d.polygon(pts,fill=fill)
def ctext(d,txt,y,font,fill):
    w=d.textlength(txt,font=font); d.text(((W-w)/2,y),txt,font=font,fill=fill)
def apply(base,lay,a,dy=0):
    if a<=0.003: return base
    if dy: 
        l2=Image.new("RGBA",(W,H),(0,0,0,0)); l2.paste(lay,(0,int(dy))); lay=l2
    if a<1: 
        al=lay.getchannel("A").point(lambda v:int(v*a)); lay=lay.copy(); lay.putalpha(al)
    base.paste(lay,(0,0),lay); return base
def render(cfg,out,frames_dir=None):
    bg=build(cfg)
    idx=cfg["indices"]; iss=cfg["issues"][:3]; sch=cfg.get("schedule")
    disc=cfg.get("disclaimer","참고용 정보이며 투자 권유가 아닙니다.")
    tmp=Image.new("RGB",(W,H)); td=ImageDraw.Draw(tmp)
    # pre-layout issues
    sizes=[(54,44),(48,40),(42,36)]
    for hs,bs in sizes:
        fh,fb=F(hs),F(bs,False); tot=0; lay_out=[]
        for it in iss:
            hl=wrap(td,it["h"],fh,W-2*(110+50)); bl=wrap(td,it["b"],fb,W-2*(110+50))
            hh=len(hl)*(hs+14)+len(bl)*(bs+12)+110
            lay_out.append((hl,bl,hh)); tot+=hh+40
        if tot<=1000: break
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
         "-f","lavfi","-i","anullsrc=channel_layout=stereo:sample_rate=44100","-shortest",
         "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709","-movflags","+faststart",
         "-c:a","aac","-b:a","96k",out]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
    marks={int(x*FPS) for x in (1.5,6.5,12.0,17.0,19.2)}
    for i in range(FPS*DUR):
        t=i/FPS; im=bg.copy().convert("RGBA")
        # S1 title
        a=fade(t,0.0,0.7,2.5,3.2)
        if a>0:
            L,d=layer()
            ctext(d,"지난 밤",640,F(70,False),SKY)
            ctext(d,"해외경제 이슈",740,F(124),WHITE)
            d.rectangle((W/2-80,930,W/2+80,936),fill=SKY)
            ctext(d,cfg["date_label"],990,F(54,False),SOFT)
            ctext(d,cfg.get("basis","미국 정규장 마감 기준"),1070,F(44,False),SOFT)
            im=apply(im,L,a,dy=(1-a)*30)
        # tag (safe zone)
        a=ease((t-2.8)/0.6)
        if a>0 and t<18.6:
            L,d=layer()
            tag=cfg.get("tag","지난 밤 해외경제 이슈")+" · "+cfg["date_label"]
            ctext(d,tag,290,F(40),SKY)
            im=apply(im,L,a)
        # S2 indices
        a=fade(t,3.2,3.9,8.6,9.3)
        if a>0:
            L,d=layer()
            ctext(d,cfg.get("indices_title","미국 3대 지수"),370,F(64),WHITE)
            for k,it in enumerate(idx[:3]):
                ak=ease((t-(3.5+k*0.45))/0.6)
                y=480+k*360+(1-ak)*50
                col=(UP if it["pct"]>=0 else DOWN) if "pct" in it else SOFT
                al=int(255*ak)
                d.rounded_rectangle((90,y,W-90,y+330),radius=40,fill=CARD+(al,),outline=CARDLN+(al,),width=3)
                d.text((150,y+28),it["name"],font=F(58),fill=SOFT+(al,))
                if "text" in it:
                    col=UP if it.get("dir","flat")=="up" else (DOWN if it.get("dir")=="down" else SOFT)
                    d.text((150,y+130),it["text"],font=F(84),fill=col+(al,))
                    d.text((150,y+250),it.get("sub",""),font=F(44,False),fill=SOFT+(al,))
                    continue
                val=f'{it["value"]:,.{it.get("dec",2)}f}'
                d.text((150,y+105),val,font=F(100),fill=WHITE+(al,))
                prog=ease((t-(3.9+k*0.45))/1.3)
                pv=abs(it["pct"])*prog
                sign=1 if it["pct"]>=0 else -1
                tri(d,172,y+268,18,sign>0,col+(al,))
                d.text((210,y+230),f'{pv:.2f}%',font=F(64),fill=col+(al,))
            im=apply(im,L,a)
        # S3 issues
        a=fade(t,8.9,9.5,14.8,15.4)
        if a>0:
            L,d=layer()
            ctext(d,"주요 이슈",370,F(64),WHITE)
            y=480
            for k,(hl,bl,hh) in enumerate(lay_out):
                ak=ease((t-(9.3+k*0.9))/0.6)
                yy=y+(1-ak)*40; al=int(255*ak)
                d.rounded_rectangle((90,yy,W-90,yy+hh),radius=40,fill=CARD+(al,),outline=CARDLN+(al,),width=3)
                d.rounded_rectangle((90,yy+30,100,yy+hh-30),radius=5,fill=SKY+(al,))
                ty=yy+40
                for ln in hl: d.text((150,ty),ln,font=F(hs),fill=WHITE+(al,)); ty+=hs+14
                ty+=8
                for ln in bl: d.text((150,ty),ln,font=F(bs,False),fill=SOFT+(al,)); ty+=bs+12
                y+=hh+40
            im=apply(im,L,a)
        # S4 schedule
        a=fade(t,15.0,15.7,16.2,16.8) if sch else 0
        if a>0:
            L,d=layer()
            ctext(d,"다가오는 주요 일정",560,F(60),WHITE)
            d.rounded_rectangle((90,680,W-90,1050),radius=40,fill=CARD,outline=CARDLN,width=3)
            ctext(d,sch["when"],740,F(76),SKY)
            lines=wrap(d,sch["what"],F(56),W-2*170)
            yy=870
            for ln in lines: ctext(d,ln,yy,F(56),WHITE); yy+=74
            im=apply(im,L,a,dy=(1-a)*30)
        # S5 sign
        a=ease((t-16.8)/0.7)
        if a>0:
            L,d=layer()
            ctext(d,"연금·보장, 전문직 맞춤 상담",560,F(52,False),SKY)
            ctext(d,"송근영",650,F(110),WHITE)
            d.rectangle((W/2-80,830,W/2+80,836),fill=SKY)
            for j,ln in enumerate(cfg.get("creds",["증권투자권유대행인","펀드투자상담사","변액보험판매관리사"])):
                ctext(d,ln,890+j*84,F(54),WHITE)
            ctext(d,"메트라이프금융서비스 | 골든트리투자자문 소속",890+len(cfg.get("creds",[1,2,3]))*84+40,F(38,False),SOFT)
            ctext(d,cfg.get("cta","상담 문의는 DM으로 남겨주세요"),890+len(cfg.get("creds",[1,2,3]))*84+130,F(46),SKY)
            im=apply(im,L,a,dy=(1-a)*20)
        rgb=im.convert("RGB")
        if frames_dir and i in marks: rgb.save(os.path.join(frames_dir,f"f_{i/FPS:.1f}.png"))
        p.stdin.write(rgb.tobytes())
    p.stdin.close(); p.wait()
if __name__=="__main__":
    cfg=json.load(open(sys.argv[1],encoding="utf-8"))
    fd=sys.argv[3] if len(sys.argv)>3 else None
    if fd: os.makedirs(fd,exist_ok=True)
    render(cfg,sys.argv[2],fd)
