"""Composite 6 panels/frame -> 3col(OFF|ON|DIFF) x 2row(side,back) video frames + colorbars + subtitle."""
from PIL import Image, ImageDraw, ImageFont
import os, json, sys, glob, subprocess

RENDER=sys.argv[1] if len(sys.argv)>1 else "/tmp/cmp_render/vout"
COMP=sys.argv[2] if len(sys.argv)>2 else "/tmp/cmp_render/vcomp"
MP4=sys.argv[3] if len(sys.argv)>3 else "/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/stoop_suit_effect.mp4"
FPS=24
os.makedirs(COMP,exist_ok=True)
meta=json.load(open(os.path.join(RENDER,"meta.json")))
N=len(meta)
VMAX=0.319; AMIN=0.03; VDIFF=0.09
INF=[(0.00,0.001,0.000,0.014),(0.13,0.122,0.047,0.281),(0.25,0.282,0.062,0.408),
     (0.38,0.451,0.122,0.412),(0.50,0.612,0.182,0.353),(0.63,0.767,0.275,0.250),
     (0.75,0.894,0.412,0.145),(0.88,0.969,0.620,0.130),(1.00,0.988,0.998,0.645)]
HOT=[(0.00,0.02,0.0,0.0),(0.30,0.62,0.04,0.0),(0.55,0.95,0.32,0.02),(0.80,1.0,0.78,0.12),(1.00,1.0,1.0,0.92)]
def lut(A,x):
    x=max(0.,min(1.,x))
    for i in range(len(A)-1):
        t0,r0,g0,b0=A[i]; t1,r1,g1,b1=A[i+1]
        if x<=t1:
            f=(x-t0)/(t1-t0) if t1>t0 else 0
            return (r0+(r1-r0)*f,g0+(g1-g0)*f,b0+(b1-b0)*f)
    return A[-1][1:]
def F(s,b=False): return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"%("Bold" if b else "Regular"),s)

PW,PH=380,512
PAD=10; TOP=78; CBAR=150
cols=[("off","Suit 0 N·m"),("on","Suit 24 N·m"),("diff","Suit effect (OFF − ON)")]
rows=["side","back"]
W=3*PW+4*PAD+CBAR
H=TOP+2*PH+3*PAD+78
if W%2: W+=1
if H%2: H+=1
BG=(20,22,26)

def phase(t):
    if t<0.3: return "직립 (Upright)"
    if t<2.3: return "하강 (Descending)"
    if t<3.05: return "Hold (최대 굴곡)"
    if t<4.7: return "상승 (Ascending)"
    return "직립 (Upright)"

def cbar(d,x,y,h,A,vmax,vmin,title):
    w=30
    for i in range(h):
        n=1-i/h; r,g,b=lut(A,n); d.line([(x,y+i),(x+w,y+i)],fill=(int(r*255),int(g*255),int(b*255)))
    d.rectangle([x,y,x+w,y+h],outline=(140,140,140))
    d.text((x-4,y-20),title,fill=(235,235,235),font=F(12,True))
    d.text((x+w+4,y-4),f"{vmax:.2f}",fill=(220,220,220),font=F(11))
    d.text((x+w+4,y+h-12),f"{vmin:.2f}",fill=(220,220,220),font=F(11))

for fi in range(N):
    m=meta[fi]; t=m['t']
    cv=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(cv)
    d.text((PAD,8),"SMA 슈트 stoop 들기 — 척추기립근(ES) 활성도 & 슈트 효과", fill=(255,255,255), font=F(22,True))
    d.text((PAD,44),f"ThoracolumbarFB · stoop_synthetic_v5 · t={t:4.2f}s · {phase(t)}", fill=(180,180,185), font=F(14))
    for ci,(ck,clab) in enumerate(cols):
        x=PAD+ci*(PW+PAD)
        fc=(255,180,90) if ck=='diff' else (235,235,235)
        d.text((x+10,TOP-22),clab,fill=fc,font=F(15,True))
        for ri,rk in enumerate(rows):
            y=TOP+ri*(PH+PAD)
            fp=os.path.join(RENDER,f"f{fi:04d}_{ck}_{rk}.png")
            if os.path.exists(fp):
                im=Image.open(fp).convert("RGB").resize((PW,PH)); cv.paste(im,(x,y))
            oc=(220,120,30) if ck=='diff' else (90,90,95)
            d.rectangle([x,y,x+PW,y+PH],outline=oc,width=2 if ck=='diff' else 1)
            if ci==0: d.text((x+6,y+6),rk.upper(),fill=(200,200,205),font=F(12,True))
    # colorbars
    cbx=3*PW+4*PAD
    cbar(d,cbx,TOP+6,PH-30,INF,VMAX,AMIN,"활성도")
    cbar(d,cbx,TOP+PH+PAD+6,PH-30,HOT,VDIFF,0.0,"감소량(효과)")
    # subtitle bottom
    sy=TOP+2*PH+2*PAD+8
    d.text((PAD,sy),f"ES peak:  OFF {m['peak_off']:.2f}  →  ON {m['peak_on']:.2f}", fill=(235,235,235), font=F(17,True))
    red=m['peak_red']
    d.text((PAD+430,sy),f"슈트 효과 (ES peak 감소):  −{red:.0f}%", fill=(255,170,80), font=F(18,True))
    # progress bar
    d.rectangle([PAD,sy+34,W-PAD,sy+40],outline=(90,90,95))
    d.rectangle([PAD,sy+34,PAD+int((W-2*PAD)*fi/max(1,N-1)),sy+40],fill=(220,120,30))
    cv.save(os.path.join(COMP,f"v{fi:04d}.png"))
    if fi%20==0: print("[comp]",fi)

# ffmpeg
cmd=["ffmpeg","-y","-framerate",str(FPS),"-i",os.path.join(COMP,"v%04d.png"),
     "-c:v","libx264","-pix_fmt","yuv420p","-crf","18",MP4]
print("ffmpeg ->",MP4)
subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("COMPOSITE_DONE", MP4)
