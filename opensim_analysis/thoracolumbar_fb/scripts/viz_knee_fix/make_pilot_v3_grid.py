from PIL import Image, ImageDraw, ImageFont
import os, json, numpy as np
D=json.load(open("/tmp/cmp_render/frames/frame_2.500.json"))
SRC="/tmp/cmp_render/pilot_v3"
OUTDIR="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review"
OUT=os.path.join(OUTDIR,"stoop_pilot_v3_grid.png")
VMAX=max(v['off'] for v in D['muscles'].values()); AMIN=0.03
VDIFF=max(0.05,max(v['off']-v['on'] for v in D['muscles'].values()))
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
def font(sz,b=False):
    return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"%("Bold" if b else "Regular"),sz)
def autocrop(im, pad=16):
    a=np.asarray(im.convert("RGB")).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>20; ys,xs=np.where(m)
    if len(xs)<10: return im
    return im.crop((max(0,xs.min()-pad),max(0,ys.min()-pad),min(im.width,xs.max()+pad),min(im.height,ys.max()+pad)))

PH=440
panels={}
for cond in ['off','on','diff']:
    for vn in ['side','back']:
        im=autocrop(Image.open(os.path.join(SRC,f"pilot_{cond}_{vn}.png")))
        w=int(im.width*PH/im.height); panels[(cond,vn)]=im.resize((w,PH))
colw=max(p.width for p in panels.values())
PAD=14; LEFT=64; CBAR=150
W=LEFT+3*colw+4*PAD+CBAR
TOP=150; H=TOP+2*PH+3*PAD+150
cv=Image.new("RGB",(W,H),(255,255,255)); d=ImageDraw.Draw(cv)
d.text((PAD,10),"Stoop PILOT v3 — 슈트 효과 차이 패널 (OFF / ON / OFF−ON)", fill=(0,0,0), font=font(24,True))
d.text((PAD,46),"t=2.5s Hold peak · 근육별 자기 활성도 · 뼈 반투명 · 구조/.osim 불변. 패널3 = 슈트가 줄인 활성도(OFF−ON)를 직접 색으로.",
       fill=(60,60,60), font=font(13))
d.text((PAD,70),"⭐ 패널3에서 빛나는 부위 = 슈트가 근육 부담을 줄인 양. 다리=어두움(효과 0), 척추기립근=밝게(최대 감소).",
       fill=(120,0,0), font=font(15,True))
cols=[("off","Suit OFF (0 N·m)"),("on","Suit ON (24 N·m)"),("diff","차이 OFF − ON  =  슈트 효과 ⭐")]
rows=[("side","SIDE"),("back","BACK")]
for ci,(ck,clab) in enumerate(cols):
    x=LEFT+PAD+ci*(colw+PAD)
    fc=(150,30,0) if ck=='diff' else (0,0,0)
    d.text((x+10,TOP-26),clab,fill=fc,font=font(15,True))
for ri,(rk,rlab) in enumerate(rows):
    y=TOP+ri*(PH+PAD)
    d.text((6,y+PH//2),rlab,fill=(0,0,0),font=font(15,True))
    for ci,(ck,_) in enumerate(cols):
        x=LEFT+PAD+ci*(colw+PAD); im=panels[(ck,rk)]
        cv.paste(im,(x+(colw-im.width)//2,y))
        oc=(180,60,0) if ck=='diff' else (150,150,150)
        d.rectangle([x,y,x+colw,y+PH],outline=oc,width=2 if ck=='diff' else 1)
# two colorbars
cbx=LEFT+3*colw+4*PAD; cbw=30
def bar(y0,h,A,vmax,vmin,title):
    for i in range(h):
        n=1-i/h; r,g,b=lut(A,n)
        d.line([(cbx,y0+i),(cbx+cbw,y0+i)],fill=(int(r*255),int(g*255),int(b*255)))
    d.rectangle([cbx,y0,cbx+cbw,y0+h],outline=(80,80,80))
    d.text((cbx-2,y0-22),title,fill=(0,0,0),font=font(11,True))
    d.text((cbx+cbw+4,y0-4),f"{vmax:.2f}",fill=(0,0,0),font=font(11))
    d.text((cbx+cbw+4,y0+h-12),f"{vmin:.2f}",fill=(0,0,0),font=font(11))
bar(TOP, PH-10, INF, VMAX, AMIN, "활성도 (OFF/ON)")
bar(TOP+PH+PAD+12, PH-10, HOT, VDIFF, 0.0, "감소량 OFF−ON")
# top muscle table
rows2=[(nm,D['muscles'][nm]['off'],D['muscles'][nm]['on']) for nm in D['muscles']]
rows2.sort(key=lambda r:-(r[1]-r[2])); rows2=rows2[:6]
ty=TOP+2*PH+2*PAD+6
d.text((PAD,ty),"슈트 효과 큰 ES 근육 (OFF → ON, 감소량):",fill=(0,0,0),font=font(13,True))
for i,(nm,o,n) in enumerate(rows2):
    d.text((PAD+(i%3)*330, ty+24+(i//3)*22), f"{nm}:  {o:.2f}→{n:.2f}  (−{o-n:.2f}, {100*(o-n)/o:.0f}%)", fill=(150,30,0), font=font(12,True))
d.text((PAD,ty+74),"검증: ⭐ 차이 패널에서 슈트 효과(줄인 양)가 명확히 빛나는가? '이게 슈트가 근육 부담을 줄인 양'이라 할 수준인가?",
       fill=(0,0,0),font=font(13,True))
cv.save(OUT); print("SAVED",OUT,cv.size)
