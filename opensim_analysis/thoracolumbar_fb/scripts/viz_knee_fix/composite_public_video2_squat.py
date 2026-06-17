"""Public side video v2: 슈트없음 | 슈트착용 좌우 + 허리 확대 인셋(ES centroid 추적, 고정창)."""
from PIL import Image, ImageDraw, ImageFont
import os, json, sys, subprocess, numpy as np
RENDER=sys.argv[1] if len(sys.argv)>1 else "/tmp/cmp_render/squatbw_vout"
COMP=sys.argv[2] if len(sys.argv)>2 else "/tmp/cmp_render/squat_vcomp"
MP4=sys.argv[3] if len(sys.argv)>3 else "/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/squat_public_video.mp4"
FPS=24
os.makedirs(COMP,exist_ok=True)
meta=json.load(open(os.path.join(RENDER,"meta.json"))); N=len(meta)
def F(s,b=False): return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"%("Bold" if b else "Regular"),s)
GYR=[(0.0,0.10,0.66,0.18),(0.4,0.55,0.80,0.10),(0.58,0.96,0.86,0.10),(0.78,0.97,0.45,0.05),(1.0,0.88,0.04,0.04)]
def lut(x):
    for i in range(len(GYR)-1):
        t0,r0,g0,b0=GYR[i]; t1,r1,g1,b1=GYR[i+1]
        if x<=t1:
            f=(x-t0)/(t1-t0) if t1>t0 else 0; return (r0+(r1-r0)*f,g0+(g1-g0)*f,b0+(b1-b0)*f)
    return GYR[-1][1:]
def phase(t):
    if t<0.5: return "준비 (서 있음)"
    if t<2.0: return "내려가는 중"
    if t<3.05: return "가장 깊이 (앉음)"
    if t<4.5: return "올라오는 중"
    return "준비 (서 있음)"
WIN=300  # fixed zoom window (panel px)
def es_window(im):
    a=np.asarray(im.convert("RGB")).astype(int)
    sat=a.max(2)-a.min(2)
    ys,xs=np.where(sat>45)
    if len(xs)<20: cx,cy=im.width//2,im.height//3
    else: cx,cy=int(xs.mean()),int(ys.mean())
    half=WIN//2
    x0=max(0,min(im.width-WIN,cx-half)); y0=max(0,min(im.height-WIN,cy-half))
    return im.crop((x0,y0,x0+WIN,y0+WIN))

PW,PH=470,610  # full panel display (from 720x940)
INS=230        # inset display size
PAD=20; TOP=120; BAN=124
W=2*PW+3*PAD; H=TOP+PH+PAD+BAN
if W%2: W+=1
if H%2: H+=1
BG=(30,32,38)
heads=[("off","슈트 없음",(255,110,90)),("on","슈트 착용",(110,225,135))]
for fi in range(N):
    m=meta[fi]; t=m['t']; red=m['peak_red']
    cv=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(cv)
    d.text((PAD,14),"쪼그려 앉을 때(squat), 허리 근육이 받는 부담", fill=(255,255,255), font=F(32,True))
    d.text((PAD,58),f"옆에서 본 모습 · {phase(t)}   (오른쪽 위 = 허리 근육 확대)", fill=(200,205,215), font=F(17))
    for ci,(ck,lab,col) in enumerate(heads):
        x=PAD+ci*(PW+PAD)
        d.rectangle([x,TOP-40,x+PW,TOP-6],fill=(22,24,29))
        tw=d.textlength(lab,font=F(26,True)); d.text((x+PW//2-tw//2,TOP-38),lab,fill=col,font=F(26,True))
        fp=os.path.join(RENDER,f"f{fi:04d}_{ck}_side.png")
        if os.path.exists(fp):
            src=Image.open(fp)
            im=src.convert("RGB").resize((PW,PH)); cv.paste(im,(x,TOP))
            ins=es_window(src).resize((INS,INS))
            ix=x+PW-INS-8; iy=TOP+8
            cv.paste(ins,(ix,iy)); d.rectangle([ix,iy,ix+INS,iy+INS],outline=col,width=3)
            d.text((ix+5,iy+INS-22),"허리 근육 확대",fill=(255,255,255),font=F(13,True))
        d.rectangle([x,TOP,x+PW,TOP+PH],outline=col,width=2)
    lx=PAD; ly=TOP+PH+PAD+10; lw=300; lh=26
    d.text((lx,ly-24),"근육 색 = 허리가 받는 부담",fill=(220,222,228),font=F(15,True))
    for i in range(lw):
        r,g,b=lut(i/lw); d.line([(lx+i,ly),(lx+i,ly+lh)],fill=(int(r*255),int(g*255),int(b*255)))
    d.rectangle([lx,ly,lx+lw,ly+lh],outline=(200,200,200))
    d.text((lx,ly+lh+4),"편함",fill=(110,225,135),font=F(18,True)); d.text((lx+lw-48,ly+lh+4),"힘듦",fill=(255,105,85),font=F(18,True))
    mx=lx+lw+56
    d.text((mx,ly-16),"슈트 착용 시 허리 근육 부담", fill=(235,235,235), font=F(23,True))
    d.text((mx,ly+22),f"↓ {red:.0f}% 감소", fill=(120,235,150), font=F(44,True))
    py=H-18; d.rectangle([PAD,py,W-PAD,py+8],outline=(90,90,95))
    d.rectangle([PAD,py,PAD+int((W-2*PAD)*fi/max(1,N-1)),py+8],fill=(120,200,140))
    cv.save(os.path.join(COMP,f"v{fi:04d}.png"))
    if fi%30==0: print("[comp]",fi)
subprocess.run(["ffmpeg","-y","-framerate",str(FPS),"-i",os.path.join(COMP,"v%04d.png"),
     "-c:v","libx264","-pix_fmt","yuv420p","-crf","18",MP4], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("PUB2_COMPOSITE_DONE", MP4)
