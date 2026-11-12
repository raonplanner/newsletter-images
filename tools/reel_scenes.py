#!/usr/bin/env python3
"""장면형 릴스(1080x1920, 장면당 2.5초, 4~6장면=10~15초, 합성 배경음악). reel_promo.py 의 그리기 함수를 재사용.
사용: python3 -I tools/reel_scenes.py 입력.json 출력.mp4 [프레임확인폴더]
입력: {"calm":false(사망보장 글은 true=차분한 음악),"label":"약 14자",
 "scenes":[
  {"style":"q","lines":["직접적인 질문(약 14자x2줄)"]},                      # 1장면
  {"style":"card","head":"핵심(약 12자)","lines":["설명 2~4줄(약 18자/줄)"]},  # 2~4장면 (글자 5~6줄 이내)
  {"style":"indices","head":"11/12(목) 미국 마감","rows":[["다우",52297.09,-0.36],...],"foot":"한 줄"},
  {"style":"close","line":"이렇게 준비하는 게 좋아요(정리 한 줄)","sub":"(선택)","note":"(선택 면책)","extra":"(선택 pill)"}]}
장면 4~6개, 장면당 2.5초."""
import sys, json, subprocess, os, importlib.util, tempfile
here=os.path.dirname(os.path.abspath(__file__))
sp=importlib.util.spec_from_file_location("rp",os.path.join(here,"reel_promo.py")); rp=importlib.util.module_from_spec(sp); sp.loader.exec_module(rp)
g=rp.__dict__
W,H,FPS,F,ease,wrap,layer,ctext,apply,grad,pill,logo_on,PAL,NAVY,YEL,WHITE,Image,ImageDraw=[g[k] for k in "W H FPS F ease wrap layer ctext apply grad pill logo_on PAL NAVY YEL WHITE Image ImageDraw".split()]
SEC=2.5
BGS=[((38,28,110),(142,45,150)),((8,96,110),(22,160,120)),((25,50,160),(20,150,200)),((45,27,78),(91,58,140)),((20,50,95),(40,95,150))]
CALM=[((11,37,69),(27,75,130)),((20,50,95),(40,95,150)),((15,61,62),(31,122,122))]
UP=(255,120,120); DOWN=(130,180,255)
clean=lambda x:"".join(c for c in x if ord(c)<0x2000 or 0x3000<=ord(c)<0xD7B0 or c in "·—→%,.()").strip()
def fit(td,text,sizes,maxw,maxlines):
    for s in sizes:
        f=F(s); ln=wrap(td,text,f,maxw)
        if len(ln)<=maxlines: return s,ln
    return sizes[-1],wrap(td,text,F(sizes[-1]),maxw)
def draw_scene(sc,k,n,cfg,td):
    L,d=layer(); st=sc["style"]
    if st=="q":
        logo_on(L,110,700)
        pill(d,W/2,430,clean(cfg.get("label","")),F(72),YEL,NAVY)
        txt=" ".join(sc["lines"]); s,ln=fit(td,txt,[124,112,100,90],W-140,3); y=640
        for l in ln: ctext(d,l,y,F(s),WHITE); y+=s+30
        d.rounded_rectangle((W/2-110,y+30,W/2+110,y+44),radius=7,fill=YEL)
        ctext(d,"송근영 FP",1560,F(76),YEL); ctext(d,"메트라이프금융서비스",1670,F(56),WHITE)
    elif st=="card":
        pill(d,W/2,260,f"POINT {sc.get('_no',k)}",F(64),YEL,NAVY)
        s,hl=fit(td,sc["head"],[120,108,96,86],W-140,2); y=420
        for l in hl: ctext(d,l,y,F(s),YEL); y+=s+24
        body=[]
        for t in sc["lines"]: body+=wrap(td,clean(t),F(80),W-260)
        body=body[:6]; h=len(body)*(80+30)+90; y0=max(y+60,(y+60+1640-h)//2)
        c=PAL[k%len(PAL)]
        d.rounded_rectangle((60,y0,W-60,y0+h),radius=44,fill=c)
        ty=y0+45
        for l in body: d.text((110,ty),l,font=F(80),fill=NAVY); ty+=110
        ctext(d,f"{sc.get('_no',k)} / {sc.get('_tot',n-2)}",1700,F(50),WHITE)
    elif st=="indices":
        ctext(d,clean(sc["head"]),300,F(86),YEL); y=470
        for name,val,pct in sc["rows"]:
            d.rounded_rectangle((60,y,W-60,y+330),radius=44,fill=(24,44,70))
            d.text((110,y+36),name,font=F(60),fill=WHITE)
            c=UP if pct>0 else DOWN; sg="▲" if pct>0 else "▼"
            vs=f"{val:,.2f}"; w=d.textlength(vs,font=F(110)); d.text((W-120-w,y+30),vs,font=F(110),fill=WHITE)
            ps=f"{sg} {abs(pct):.2f}%"; w=d.textlength(ps,font=F(100)); d.text((W-120-w,y+175),ps,font=F(100),fill=c)
            y+=370
        if sc.get("foot"): ctext(d,clean(sc["foot"]),1620,F(54),WHITE)
    else:  # close
        s,ln=fit(td,clean(sc["line"]),[112,100,90,80],W-140,3); y=300
        for l in ln: ctext(d,l,y,F(s),YEL); y+=s+30
        d.rounded_rectangle((W/2-110,y+20,W/2+110,y+34),radius=7,fill=WHITE); y+=110
        if sc.get("sub"):
            for l in wrap(td,clean(sc["sub"]),F(66),W-160)[:3]: ctext(d,l,y,F(66),WHITE); y+=88
            y+=20
        pill(d,W/2,max(y+30,860),"궁금하면 DM · 프로필 링크 상담신청",F(54),NAVY,YEL)
        if sc.get("extra"): pill(d,W/2,max(y+30,860)+150,clean(sc["extra"]),F(50),WHITE,NAVY)
        ctext(d,"송근영",1180,F(120),YEL); ctext(d,"메트라이프금융서비스",1330,F(76),WHITE)
        if sc.get("note"): ctext(d,clean(sc["note"]),1470,F(40),WHITE)
        logo_on(L,1600,640)
    return L
def render(cfg,out,fd=None):
    sc=cfg["scenes"]; n=len(sc); assert 4<=n<=6, "장면은 4~6개"
    dur=n*SEC; rp.DUR=int(dur+0.99)
    wav=os.path.join(tempfile.mkdtemp(),"bgm.wav"); (rp.make_music_calm if cfg.get("calm") else rp.make_music)(wav)
    pal=CALM if cfg.get("calm") else BGS; bgs=[grad(*pal[i%len(pal)]) for i in range(n)]
    td=ImageDraw.Draw(Image.new("RGB",(W,H))); cards=[x for x in sc if x["style"]=="card"]
    for j,x in enumerate(cards): x["_no"]=j+1; x["_tot"]=len(cards)
    Ls=[draw_scene(s,i,n,cfg,td) for i,s in enumerate(sc)]  # i=0 q; card k=i
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",wav,"-shortest",
         "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-movflags","+faststart","-c:a","aac","-b:a","128k",out]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
    for i in range(int(dur*FPS)):
        t=i/FPS; k=min(n-1,int(t/SEC)); lt=t-k*SEC
        im=bgs[k].copy()
        a=ease(lt/0.35)*(1 if k==n-1 else 1-ease((lt-(SEC-0.3))/0.3))
        im=apply(im,Ls[k],a,dy=(1-ease(lt/0.35))*40)
        rgb=im.convert("RGB")
        if fd and abs(lt-1.4)<1/FPS/2+1e-6: rgb.save(os.path.join(fd,f"s{k+1}.png"))
        p.stdin.write(rgb.tobytes())
    p.stdin.close(); p.wait()
if __name__=="__main__":
    cfg=json.load(open(sys.argv[1],encoding="utf-8")); fd=sys.argv[3] if len(sys.argv)>3 else None
    if fd: os.makedirs(fd,exist_ok=True)
    render(cfg,sys.argv[2],fd)
