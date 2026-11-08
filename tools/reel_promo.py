#!/usr/bin/env python3
"""대전 FP 직무설명회 홍보 릴스(9:16, 20초, 자체 합성 배경음악) 생성기.
사용: python3 -I reel_promo.py 입력.json 출력.mp4 [프레임확인폴더]
입력.json 형식은 reel_promo_sample.json 참고. 배경음악은 코드로 직접 합성한 곡이라 저작권 문제가 없다."""
import sys, json, subprocess, os, wave, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
W,H,FPS,DUR=1080,1920,30,20
RF="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BF="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def F(s,b=True): return ImageFont.truetype(BF if b else RF,s,index=1)
GOLD=(227,199,120); WHITE=(255,255,255); SOFT=(184,204,228); CARD=(24,60,104); CARDLN=(70,110,160)
def ease(t): t=max(0.0,min(1.0,t)); return 1-(1-t)**3
def fade(t,t0,t1,t2,t3): return ease((t-t0)/(t1-t0))*(1-ease((t-t2)/(t3-t2)))
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
def bg_image():
    c1=np.array((11,37,69)); c2=np.array((27,75,130))
    t=np.linspace(0,1,H)[:,None,None]
    arr=(c1*(1-t)+c2*t)*np.ones((1,W,1))
    arr+=np.random.default_rng(3).integers(-2,3,(H,W,1))
    im=Image.fromarray(np.clip(arr,0,255).astype("uint8"))
    d=ImageDraw.Draw(im)
    d.ellipse((760,-200,1300,340),outline=(40,80,130),width=6)
    d.ellipse((-220,1560,360,2140),outline=(40,80,130),width=6)
    return im
def layer():
    im=Image.new("RGBA",(W,H),(0,0,0,0)); return im,ImageDraw.Draw(im)
def ctext(d,txt,y,font,fill):
    w=d.textlength(txt,font=font); d.text(((W-w)/2,y),txt,font=font,fill=fill)
def apply(base,lay,a,dy=0):
    if a<=0.003: return base
    if dy:
        l2=Image.new("RGBA",(W,H),(0,0,0,0)); l2.paste(lay,(0,int(dy))); lay=l2
    if a<1:
        al=lay.getchannel("A").point(lambda v:int(v*a)); lay=lay.copy(); lay.putalpha(al)
    base.paste(lay,(0,0),lay); return base
def make_music(path):
    """밝고 경쾌한 팝 느낌(112bpm, C-G-Am-F), 통통 튀는 플럭 멜로디+가벼운 킥/하이햇. 직접 합성(저작권 없음). 20초, 끝에서 페이드아웃."""
    sr=44100; n=sr*DUR; t=np.arange(n)/sr; bpm=112; beat=60.0/bpm
    out=np.zeros(n)
    def add(start,sig,g):
        i=int(start*sr); j=min(n,i+len(sig))
        if i<n: out[i:j]+=g*sig[:j-i]
    def pluck(f,dur=0.32):
        x=np.arange(int(dur*sr))/sr
        return np.exp(-x*9)*(np.sin(2*np.pi*f*x)+0.35*np.sin(2*np.pi*2*f*x)+0.12*np.sin(2*np.pi*3*f*x))
    def kick():
        x=np.arange(int(0.18*sr))/sr
        return np.exp(-x*22)*np.sin(2*np.pi*(120*np.exp(-x*18)+45)*x)
    rng=np.random.default_rng(7)
    def hat():
        x=np.arange(int(0.05*sr))/sr
        return np.exp(-x*70)*rng.standard_normal(len(x))
    chords=[(261.63,329.63,392.0),(196.0,246.94,392.0),(220.0,261.63,329.63),(174.61,220.0,261.63)]
    mel=[[2,1,2,0,1,2,1,0],[1,2,1,0,2,1,0,1],[1,0,1,2,1,0,2,1],[0,1,2,1,0,2,1,2]]
    steps=int(DUR/(beat/2))
    for k in range(steps):
        tm=k*beat/2; bar=(k//8)%4; ch=chords[bar]
        f=ch[mel[bar][k%8]]*2
        add(tm,pluck(f),0.20)
        if k%2==0: add(tm,pluck(ch[0]/2,0.4),0.16)
        if k%4==0: add(tm,kick(),0.30)
        if k%2==1: add(tm,hat(),0.05)
    add(0,np.zeros(1),0)
    out*=np.minimum(1,t/0.4)*np.minimum(1,(DUR-t)/1.5)
    out=out/np.max(np.abs(out))*0.5
    st=np.stack([out,out],1)
    with wave.open(path,"w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st*32767).astype("<i2").tobytes())
def render(cfg,out,frames_dir=None):
    bg=bg_image()
    tmpd=tempfile.mkdtemp(); wav=os.path.join(tmpd,"bgm.wav"); make_music(wav)
    tmp=Image.new("RGB",(W,H)); td=ImageDraw.Draw(tmp)
    # 주제 카드 레이아웃(글자 크기 자동 축소)
    for hs,bs in [(72,46),(64,42),(56,38),(50,34)]:
        fh,fb=F(hs),F(bs,False)
        hl=wrap(td,cfg["topic_title"],fh,W-2*(120+50))
        bl=[wrap(td,b,fb,W-2*(120+50)-40) for b in cfg["topic_points"][:5]]
        tot=len(hl)*(hs+16)+sum(len(x)*(bs+12)+22 for x in bl)+120
        if tot<=1050: break
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",wav,
         "-shortest","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-movflags","+faststart","-c:a","aac","-b:a","128k",out]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
    marks={int(x*FPS) for x in (1.8,6.5,12.5,18.5)}
    for i in range(FPS*DUR):
        t=i/FPS; im=bg.copy().convert("RGBA")
        a=fade(t,0.0,0.7,4.2,5.0)
        if a>0:
            L,d=layer()
            ctext(d,"대전 FP",560,F(76,False),GOLD)
            ctext(d,"직무설명회",650,F(150),WHITE)
            d.rectangle((W/2-80,880,W/2+80,886),fill=GOLD)
            ctext(d,"매주 금요일",950,F(84),GOLD)
            ctext(d,"11:30 ~ 13:30",1060,F(100),WHITE)
            ctext(d,"점심 포함",1200,F(52,False),SOFT)
            im=apply(im,L,a,dy=(1-a)*30)
        a=fade(t,4.6,5.3,10.6,11.3)
        if a>0:
            L,d=layer()
            ctext(d,"대전 FP 직무설명회",290,F(40),GOLD)
            y0=400; al=255
            d.rounded_rectangle((90,y0,W-90,y0+tot),radius=40,fill=CARD,outline=CARDLN,width=3)
            d.rounded_rectangle((90,y0+30,100,y0+tot-30),radius=5,fill=GOLD)
            ty=y0+50
            for ln in hl: d.text((140,ty),ln,font=F(hs),fill=WHITE); ty+=hs+16
            ty+=14
            for k,lines in enumerate(bl):
                ak=ease((t-(5.9+k*0.5))/0.5)
                col=SOFT+(int(255*ak),)
                for j,ln in enumerate(lines):
                    pre="· " if j==0 else "   "
                    d.text((140,ty),pre+ln,font=F(bs,False),fill=col); ty+=bs+12
                ty+=22
            im=apply(im,L,a)
        a=fade(t,10.9,11.6,15.6,16.3)
        if a>0:
            L,d=layer()
            ctext(d,"참석하시면",380,F(56,False),GOLD)
            d.rounded_rectangle((90,480,W-90,1000),radius=40,fill=CARD,outline=CARDLN,width=3)
            ctext(d,"점심 제공",540,F(96),WHITE)
            ctext(d,"+",670,F(70),GOLD)
            ctext(d,"교통비 2만원",770,F(96),WHITE)
            ctext(d,"대전 서구 둔산대로117번길 34 4층",1090,F(44),SOFT)
            ctext(d,"메트라이프금융서비스",1170,F(52),GOLD)
            im=apply(im,L,a,dy=(1-a)*30)
        a=ease((t-16.0)/0.7)
        if a>0:
            L,d=layer()
            ctext(d,"지금 신청하세요",520,F(96),WHITE)
            d.rectangle((W/2-80,700,W/2+80,706),fill=GOLD)
            ctext(d,"프로필 링크 · 캡션의 신청 링크",770,F(48,False),SOFT)
            ctext(d,"010-3224-1517",880,F(100),GOLD)
            ctext(d,"송근영",1060,F(84),WHITE)
            ctext(d,"메트라이프금융서비스 | 골든트리투자자문 소속",1170,F(36,False),SOFT)
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
