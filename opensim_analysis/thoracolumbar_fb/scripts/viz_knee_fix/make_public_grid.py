from PIL import Image, ImageDraw, ImageFont
import os, json, numpy as np
SRC="/tmp/cmp_render/public"
D=json.load(open("/tmp/cmp_render/frames/frame_2.700.json"))
OUTDIR="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review"
OUT=os.path.join(OUTDIR,"stoop_public_grid.png")
# peak reduction
rows=sorted(((v['off'],v['on']) for v in D['muscles'].values()), key=lambda r:-r[0])
pk=rows[0]; RED=round(100*(pk[0]-pk[1])/pk[0])
def F(s,b=False): return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"%("Bold" if b else "Regular"),s)
def crop(p):
    im=Image.open(p).convert("RGB"); a=np.asarray(im).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>26; ys,xs=np.where(m)
    return im.crop((max(0,xs.min()-14),max(0,ys.min()-14),min(im.width,xs.max()+14),min(im.height,ys.max()+14)))
PH=560
def sc(im): w=int(im.width*PH/im.height); return im.resize((w,PH))
P={(c,v):sc(crop(os.path.join(SRC,f"pub_{c}_{v}.png"))) for c in ['off','on'] for v in ['side','back']}
colw=max(p.width for p in P.values()); PAD=18; TOP=140
BAN=120   # bottom banner
W=2*colw+3*PAD; H=TOP+2*PH+3*PAD+BAN
BG=(38,40,46)
cv=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(cv)
# title
d.text((PAD,16),"허리 굽혀 들 때, 허리 근육이 받는 부담", fill=(255,255,255), font=F(34,True))
d.text((PAD,62),"웨어러블 슈트를 착용하면 허리 근육 부담이 줄어듭니다.", fill=(200,205,215), font=F(19))
# column headers
heads=[("off","슈트 없음",(255,120,90)),("on","슈트 착용",(120,220,140))]
for ci,(ck,lab,col) in enumerate(heads):
    x=PAD+ci*(colw+PAD)
    d.rectangle([x,TOP-44,x+colw,TOP-6],fill=(28,30,35))
    d.text((x+colw//2-60,TOP-40),lab,fill=col,font=F(26,True))
# panels
for ci,(ck,_,_) in enumerate(heads):
    x=PAD+ci*(colw+PAD)
    for ri,v in enumerate(['side','back']):
        y=TOP+ri*(PH+PAD); im=P[(ck,v)]
        cv.paste(im,(x+(colw-im.width)//2,y))
        d.rectangle([x,y,x+colw,y+PH],outline=(90,92,100))
# annotate "허리 근육" on OFF side panel (upper-mid where lumbar ES sits)
ax=PAD+int(colw*0.30); ay=TOP+int(PH*0.30)
d.ellipse([ax-46,ay-30,ax+46,ay+30],outline=(255,80,60),width=4)
d.text((ax-70,ay-62),"허리 근육",fill=(255,210,120),font=F(20,True))
# same circle on ON side
ax2=PAD+int(colw*0.30);
d.ellipse([ax2-46,ay-30,ax2+46,ay+30],outline=(120,220,140),width=3)
# legend (green->red bar) with plain words
lx=PAD; ly=TOP+2*PH+2*PAD+8; lw=360; lh=30
GYR=[(0.0,0.10,0.66,0.18),(0.4,0.55,0.80,0.10),(0.58,0.96,0.86,0.10),(0.78,0.97,0.45,0.05),(1.0,0.88,0.04,0.04)]
def lut(x):
    for i in range(len(GYR)-1):
        t0,r0,g0,b0=GYR[i]; t1,r1,g1,b1=GYR[i+1]
        if x<=t1:
            f=(x-t0)/(t1-t0) if t1>t0 else 0; return (r0+(r1-r0)*f,g0+(g1-g0)*f,b0+(b1-b0)*f)
    return GYR[-1][1:]
for i in range(lw):
    r,g,b=lut(i/lw); d.line([(lx+i,ly),(lx+i,ly+lh)],fill=(int(r*255),int(g*255),int(b*255)))
d.rectangle([lx,ly,lx+lw,ly+lh],outline=(200,200,200))
d.text((lx,ly+lh+4),"편함",fill=(120,220,140),font=F(20,True))
d.text((lx+lw-54,ly+lh+4),"힘듦",fill=(255,110,90),font=F(20,True))
d.text((lx,ly-26),"근육 색 = 허리가 받는 부담",fill=(220,220,225),font=F(16,True))
# big bottom message
mx=lx+lw+50
d.text((mx,ly-4),f"슈트 착용 시", fill=(235,235,235), font=F(26,True))
d.text((mx,ly+34),f"허리 근육 부담  ↓ {RED}% 감소", fill=(120,230,150), font=F(34,True))
cv.save(OUT); print("SAVED",OUT,cv.size,"RED",RED)
