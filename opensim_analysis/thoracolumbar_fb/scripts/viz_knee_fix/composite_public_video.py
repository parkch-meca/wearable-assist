"""Composite public side video: 슈트없음 | 슈트착용, 일상어 자막 + 실시간 감소% + 범례."""
from PIL import Image, ImageDraw, ImageFont
import os, json, sys, subprocess
RENDER=sys.argv[1] if len(sys.argv)>1 else "/tmp/cmp_render/pub_vout"
COMP=sys.argv[2] if len(sys.argv)>2 else "/tmp/cmp_render/pub_vcomp"
MP4=sys.argv[3] if len(sys.argv)>3 else "/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/stoop_public_video.mp4"
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
    if t<0.3: return "준비 (서 있음)"
    if t<2.3: return "허리 굽히는 중"
    if t<3.05: return "가장 깊이 굽힘"
    if t<4.7: return "허리 펴는 중"
    return "준비 (서 있음)"
PW,PH=540,705   # from 720x940
PAD=22; TOP=120; BAN=128
W=2*PW+3*PAD; H=TOP+PH+PAD+BAN
if W%2: W+=1
if H%2: H+=1
BG=(30,32,38)
heads=[("off","슈트 없음",(255,110,90)),("on","슈트 착용",(110,225,135))]
for fi in range(N):
    m=meta[fi]; t=m['t']; red=m['peak_red']
    cv=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(cv)
    d.text((PAD,14),"허리 굽혀 들 때, 허리 근육이 받는 부담", fill=(255,255,255), font=F(32,True))
    d.text((PAD,58),f"옆에서 본 모습 · {phase(t)}", fill=(200,205,215), font=F(18))
    for ci,(ck,lab,col) in enumerate(heads):
        x=PAD+ci*(PW+PAD)
        d.rectangle([x,TOP-40,x+PW,TOP-6],fill=(22,24,29))
        tw=d.textlength(lab,font=F(26,True)); d.text((x+PW//2-tw//2,TOP-38),lab,fill=col,font=F(26,True))
        fp=os.path.join(RENDER,f"f{fi:04d}_{ck}_side.png")
        if os.path.exists(fp):
            im=Image.open(fp).convert("RGB").resize((PW,PH)); cv.paste(im,(x,TOP))
        d.rectangle([x,TOP,x+PW,TOP+PH],outline=col,width=2)
    # legend
    lx=PAD; ly=TOP+PH+PAD+12; lw=300; lh=26
    d.text((lx,ly-24),"근육 색 = 허리가 받는 부담",fill=(220,222,228),font=F(15,True))
    for i in range(lw):
        r,g,b=lut(i/lw); d.line([(lx+i,ly),(lx+i,ly+lh)],fill=(int(r*255),int(g*255),int(b*255)))
    d.rectangle([lx,ly,lx+lw,ly+lh],outline=(200,200,200))
    d.text((lx,ly+lh+4),"편함",fill=(110,225,135),font=F(18,True))
    d.text((lx+lw-48,ly+lh+4),"힘듦",fill=(255,105,85),font=F(18,True))
    # big message (real-time)
    mx=lx+lw+60
    d.text((mx,ly-16),"슈트 착용 시 허리 근육 부담", fill=(235,235,235), font=F(24,True))
    d.text((mx,ly+22),f"↓ {red:.0f}% 감소", fill=(120,235,150), font=F(46,True))
    # progress
    py=H-20
    d.rectangle([PAD,py,W-PAD,py+8],outline=(90,90,95))
    d.rectangle([PAD,py,PAD+int((W-2*PAD)*fi/max(1,N-1)),py+8],fill=(120,200,140))
    cv.save(os.path.join(COMP,f"v{fi:04d}.png"))
    if fi%30==0: print("[comp]",fi)
cmd=["ffmpeg","-y","-framerate",str(FPS),"-i",os.path.join(COMP,"v%04d.png"),
     "-c:v","libx264","-pix_fmt","yuv420p","-crf","18",MP4]
subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("PUB_COMPOSITE_DONE", MP4)
