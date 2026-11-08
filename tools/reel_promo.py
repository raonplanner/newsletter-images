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
def grad(c1,c2):
    t=np.linspace(0,1,H)[:,None,None]
    arr=(np.array(c1)*(1-t)+np.array(c2)*t)*np.ones((1,W,1))
    return Image.fromarray(np.clip(arr,0,255).astype("uint8")).convert("RGBA")
# 장면별 배경(색을 바꿔 단조로움을 없앤다): 인디고→보라 / 틸→그린 / 오렌지→코랄 / 로열블루→시안
BGS=[((38,28,110),(142,45,150)),((8,96,110),(22,160,120)),((235,110,40),(225,50,95)),((25,50,160),(20,150,200))]
PAL=[(255,214,10),(110,231,183),(125,211,252),(253,164,175),(255,190,120)]
NAVY=(16,32,64); YEL=(255,214,10); COR=(255,107,107)
def pill(d,cx,y,txt,font,fill,tc):
    w=d.textlength(txt,font=font); pad=44; h=font.size+34
    d.rounded_rectangle((cx-w/2-pad,y,cx+w/2+pad,y+h),radius=h//2,fill=fill)
    d.text((cx-w/2,y+6),txt,font=font,fill=tc)
def dots(im,t):
    L,d=layer()
    for k in range(9):
        x=(k*137+60*np.sin(t*0.7+k))%W; y=(k*271+40*np.cos(t*0.5+k*1.3)+t*28*(1+k%3))%(H+200)-100
        r=40+(k%4)*26
        d.ellipse((x-r,y-r,x+r,y+r),fill=(255,255,255,26 if k%2 else 18))
    im.alpha_composite(L)
def render(cfg,out,frames_dir=None):
    bgs=[grad(*c) for c in BGS]
    tmpd=tempfile.mkdtemp(); wav=os.path.join(tmpd,"bgm.wav"); make_music(wav)
    tmp=Image.new("RGB",(W,H)); td=ImageDraw.Draw(tmp)
    # 주제 장면: 제목과 항목 카드가 화면을 가득 채우도록 글자 크기를 가장 크게 자동 선택
    pts=cfg["topic_points"][:5]; TOP,BOT=470,1800
    for hs,bs in [(112,66),(104,62),(96,58),(88,54),(80,50)]:
        fh,fb=F(hs),F(bs)
        hl=wrap(td,cfg["topic_title"],fh,W-120)
        if len(hl)>2: continue
        bl=[wrap(td,b,fb,W-60-200-45) for b in pts]
        ch=[len(x)*(bs+14)+56 for x in bl]
        tot=sum(ch)+26*(len(ch)-1)
        if tot<=BOT-TOP-(len(hl)-1)*(hs+10): break
    ty0=300+len(hl)*(hs+10)+30
    if ty0<TOP: ty0=TOP
    extra=max(0,(BOT-ty0-tot)//(len(ch)+1)) if ch else 0
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",wav,
         "-shortest","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-movflags","+faststart","-c:a","aac","-b:a","128k",out]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
    marks={int(x*FPS) for x in (1.8,6.5,9.5,12.5,18.5)}
    cuts=[4.6,11.5,16.3]
    for i in range(FPS*DUR):
        t=i/FPS
        # 배경 크로스페이드
        idx=sum(1 for c in cuts if t>=c); im=bgs[idx].copy()
        for k,c in enumerate(cuts):
            if 0<=t-c<0.5 and k<3: im=Image.blend(bgs[k],bgs[k+1],ease((t-c)/0.5))
        dots(im,t)
        a=fade(t,0.0,0.6,4.0,4.6)
        if a>0:
            L,d=layer()
            ctext(d,"대전 FP",300,F(110),YEL)
            ctext(d,"직무설명회",430,F(200),WHITE)
            d.rounded_rectangle((W/2-110,720,W/2+110,734),radius=7,fill=YEL)
            ctext(d,"매주 금요일",800,F(150),YEL)
            ctext(d,"11:30~13:30",980,F(170),WHITE)
            pill(d,W/2,1260,"점심 포함",F(96),YEL,NAVY)
            im=apply(im,L,a,dy=(1-a)*40)
        a=fade(t,4.6,5.2,10.9,11.5)
        if a>0:
            L,d=layer()
            ctext(d,"대전 FP 직무설명회",190,F(52),YEL)
            y=300
            for ln in hl: ctext(d,ln,y,F(hs),WHITE); y+=hs+10
            y=ty0+extra
            for k,lines in enumerate(bl):
                ak=ease((t-(5.7+k*0.55))/0.45); h=ch[k]
                if ak>0:
                    c=PAL[k%len(PAL)]; off=int((1-ak)*120)
                    cl,cd=layer()
                    cd.rounded_rectangle((60,y,W-60,y+h),radius=36,fill=c)
                    cd.ellipse((90,y+h/2-42,174,y+h/2+42),fill=NAVY)
                    nw=cd.textlength(str(k+1),font=F(52)); cd.text((132-nw/2,y+h/2-34),str(k+1),font=F(52),fill=c)
                    ty=y+28
                    for ln in lines: cd.text((200,ty),ln,font=F(bs),fill=NAVY); ty+=bs+14
                    cl.putalpha(cl.getchannel('A').point(lambda v:int(v*ak)))
                    L.paste(cl,(off,0),cl)
                y+=h+26+extra
            im=apply(im,L,a)
        a=fade(t,11.5,12.1,15.7,16.3)
        if a>0:
            L,d=layer()
            ctext(d,"참석하시면",260,F(90),YEL)
            ctext(d,"점심 제공",460,F(210),WHITE)
            ctext(d,"+",720,F(150),YEL)
            ctext(d,"교통비",880,F(150),WHITE)
            ctext(d,"2만원",1050,F(250),YEL)
            pill(d,W/2,1420,"매주 금요일 점심",F(76),NAVY,WHITE)
            ctext(d,"대전 서구 둔산대로117번길 34 4층",1600,F(50),WHITE)
            ctext(d,"메트라이프금융서비스",1690,F(64),YEL)
            im=apply(im,L,a,dy=(1-a)*40)
        a=ease((t-16.3)/0.6)
        if a>0:
            L,d=layer()
            ctext(d,"지금 신청하세요",330,F(140),WHITE)
            d.rounded_rectangle((W/2-110,540,W/2+110,554),radius=7,fill=YEL)
            pill(d,W/2,650,"프로필 링크 · 캡션 신청 링크",F(56),NAVY,YEL)
            ctext(d,"문의",900,F(80),YEL)
            ctext(d,"010-3224-1517",1010,F(128),WHITE)
            ctext(d,"송근영",1260,F(130),YEL)
            ctext(d,"메트라이프금융서비스",1440,F(70),WHITE)
            ctext(d,"골든트리투자자문 소속",1540,F(56),WHITE)
            im=apply(im,L,a,dy=(1-a)*30)
        rgb=im.convert("RGB")
        if frames_dir and i in marks: rgb.save(os.path.join(frames_dir,f"f_{i/FPS:.1f}.png"))
        p.stdin.write(rgb.tobytes())
    p.stdin.close(); p.wait()
if __name__=="__main__":
    cfg=json.load(open(sys.argv[1],encoding="utf-8"))
    fd=sys.argv[3] if len(sys.argv)>3 else None
    if fd: os.makedirs(fd,exist_ok=True)
    render(cfg,sys.argv[2],fd)
