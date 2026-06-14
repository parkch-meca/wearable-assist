from PIL import Image, ImageDraw, ImageFont
import os, json, numpy as np
SRC="/tmp/cmp_render/public"
D=json.load(open("/tmp/cmp_render/frames/frame_2.700.json"))
OUTDIR="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review"
OUT=os.path.join(OUTDIR,"stoop_public_grid.png")
rows=sorted(((v['off'],v['on']) for v in D['muscles'].values()), key=lambda r:-r[0]); pk=rows[0]
RED=round(100*(pk[0]-pk[1])/pk[0])
def F(s,b=False): return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"%("Bold" if b else "Regular"),s)
def crop(p):
    im=Image.open(p).convert("RGB"); a=np.asarray(im).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>26; ys,xs=np.where(m)
    return im.crop((max(0,xs.min()-16),max(0,ys.min()-16),min(im.width,xs.max()+16),min(im.height,ys.max()+16)))
PH=620
def sc(im): return im.resize((int(im.width*PH/im.height),PH))
off=sc(crop(os.path.join(SRC,"pub_off_side.png"))); on=sc(crop(os.path.join(SRC,"pub_on_side.png")))
colw=max(off.width,on.width); PAD=20; TOP=150; BAN=130
W=2*colw+3*PAD; H=TOP+PH+PAD+BAN
BG=(36,38,44)
cv=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(cv)
d.text((PAD,16),"허리 굽혀 들 때, 허리 근육이 받는 부담", fill=(255,255,255), font=F(38,True))
d.text((PAD,66),"웨어러블 슈트를 착용하면 허리 근육 부담이 줄어듭니다.  (옆에서 본 모습)", fill=(205,210,220), font=F(20))
heads=[("off","슈트 없음",(255,110,90),off),("on","슈트 착용",(110,225,135),on)]
for ci,(ck,lab,col,im) in enumerate(heads):
    x=PAD+ci*(colw+PAD)
    d.rectangle([x,TOP-46,x+colw,TOP-6],fill=(26,28,33))
    tw=d.textlength(lab,font=F(30,True))
    d.text((x+colw//2-tw//2,TOP-44),lab,fill=col,font=F(30,True))
    cv.paste(im,(x+(colw-im.width)//2,TOP))
    d.rectangle([x,TOP,x+colw,TOP+PH],outline=(95,97,105))
# 허리 근육 annotation on both (lumbar ~ relative pos)
for ci,(ck,lab,col,im) in enumerate(heads):
    x=PAD+ci*(colw+PAD)+(colw-im.width)//2
    ax=x+int(im.width*0.34); ay=TOP+int(PH*0.24)
    oc=(255,90,60) if ck=='off' else (110,225,135)
    d.ellipse([ax-52,ay-34,ax+52,ay+34],outline=oc,width=5)
    if ci==0:
        d.text((ax-40,ay-72),"허리 근육",fill=(255,215,120),font=F(22,True))
        d.line([(ax,ay-38),(ax,ay-46)],fill=(255,215,120),width=3)
# legend
lx=PAD; ly=TOP+PH+PAD+18; lw=380; lh=34
GYR=[(0.0,0.10,0.66,0.18),(0.4,0.55,0.80,0.10),(0.58,0.96,0.86,0.10),(0.78,0.97,0.45,0.05),(1.0,0.88,0.04,0.04)]
def lut(x):
    for i in range(len(GYR)-1):
        t0,r0,g0,b0=GYR[i]; t1,r1,g1,b1=GYR[i+1]
        if x<=t1:
            f=(x-t0)/(t1-t0) if t1>t0 else 0; return (r0+(r1-r0)*f,g0+(g1-g0)*f,b0+(b1-b0)*f)
    return GYR[-1][1:]
d.text((lx,ly-28),"근육 색 = 허리가 받는 부담",fill=(225,225,230),font=F(18,True))
for i in range(lw):
    r,g,b=lut(i/lw); d.line([(lx+i,ly),(lx+i,ly+lh)],fill=(int(r*255),int(g*255),int(b*255)))
d.rectangle([lx,ly,lx+lw,ly+lh],outline=(200,200,200))
d.text((lx,ly+lh+6),"편함",fill=(110,225,135),font=F(22,True))
d.text((lx+lw-58,ly+lh+6),"힘듦",fill=(255,105,85),font=F(22,True))
# big message
mx=lx+lw+60
d.text((mx,ly-20),"슈트 착용 시", fill=(235,235,235), font=F(30,True))
d.text((mx,ly+22),f"허리 근육 부담  ↓ {RED}% 감소", fill=(120,235,150), font=F(40,True))
cv.save(OUT); print("SAVED",OUT,cv.size,"RED",RED)
