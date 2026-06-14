from PIL import Image, ImageDraw, ImageFont
import os, json, numpy as np
SRC="/tmp/cmp_render/public"  # per-pose framed Hold (t=2.70), AMIN0.10 VMAX0.32
D=json.load(open("/tmp/cmp_render/frames/frame_2.700.json"))
rows=sorted(((v['off'],v['on']) for v in D['muscles'].values()),key=lambda r:-r[0]); pk=rows[0]
RED=round(100*(pk[0]-pk[1])/pk[0])
OUTDIR="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review"
OUT=os.path.join(OUTDIR,"stoop_hold_compare_grid.png")
def F(s,b=False): return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"%("Bold" if b else "Regular"),s)
def crop(p):
    im=Image.open(p).convert("RGB"); a=np.asarray(im).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>26; ys,xs=np.where(m)
    return im.crop((max(0,xs.min()-14),max(0,ys.min()-14),min(im.width,xs.max()+14),min(im.height,ys.max()+14)))
PH=600
def sc(im): return im.resize((int(im.width*PH/im.height),PH))
off=sc(crop(os.path.join(SRC,"pub_off_side.png"))); on=sc(crop(os.path.join(SRC,"pub_on_side.png")))
colw=max(off.width,on.width); PAD=22; TOP=150; BAN=120
W=2*colw+3*PAD; H=TOP+PH+PAD+BAN; BG=(34,36,42)
cv=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(cv)
d.text((PAD,16),"가장 깊이 굽힌 순간 — 허리 근육 부담 비교 (좌우)", fill=(255,255,255), font=F(36,True))
d.text((PAD,64),"같은 자세, 슈트만 다름. 왼쪽 허리는 빨강(힘듦), 오른쪽은 초록 쪽(편함).", fill=(205,210,220), font=F(20))
def zoom_es(p):
    im=Image.open(p).convert("RGB"); a=np.asarray(im).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>26; ys,xs=np.where(m); x0,y0,x1,y1=xs.min(),ys.min(),xs.max(),ys.max()
    w=x1-x0; h=y1-y0
    return im.crop((x0, y0, x0+int(w*0.62), y0+int(h*0.5)))
zoff=zoom_es(os.path.join(SRC,"pub_off_side.png")); zon=zoom_es(os.path.join(SRC,"pub_on_side.png"))
heads=[("off","슈트 없음",(255,110,90),off,zoff),("on","슈트 착용",(110,225,135),on,zon)]
ZH=170
for ci,(ck,lab,col,im,zm) in enumerate(heads):
    x=PAD+ci*(colw+PAD)
    d.rectangle([x,TOP-46,x+colw,TOP-6],fill=(24,26,31))
    tw=d.textlength(lab,font=F(30,True)); d.text((x+colw//2-tw//2,TOP-44),lab,fill=col,font=F(30,True))
    cv.paste(im,(x+(colw-im.width)//2,TOP)); d.rectangle([x,TOP,x+colw,TOP+PH],outline=col,width=3)
    # zoom inset top-right of panel
    zw=int(zm.width*ZH/zm.height); zi=zm.resize((zw,ZH))
    zx=x+colw-zw-8; zy=TOP+8
    cv.paste(zi,(zx,zy)); d.rectangle([zx,zy,zx+zw,zy+ZH],outline=col,width=3)
    d.text((zx+4,zy+ZH-22),"허리 근육 확대",fill=(255,255,255),font=F(14,True))
# legend
lx=PAD; ly=TOP+PH+PAD+18; lw=360; lh=32
GYR=[(0.0,0.10,0.66,0.18),(0.4,0.55,0.80,0.10),(0.58,0.96,0.86,0.10),(0.78,0.97,0.45,0.05),(1.0,0.88,0.04,0.04)]
def lut(x):
    for i in range(len(GYR)-1):
        t0,r0,g0,b0=GYR[i]; t1,r1,g1,b1=GYR[i+1]
        if x<=t1:
            f=(x-t0)/(t1-t0) if t1>t0 else 0; return (r0+(r1-r0)*f,g0+(g1-g0)*f,b0+(b1-b0)*f)
    return GYR[-1][1:]
d.text((lx,ly-26),"근육 색 = 허리가 받는 부담",fill=(225,225,230),font=F(18,True))
for i in range(lw):
    r,g,b=lut(i/lw); d.line([(lx+i,ly),(lx+i,ly+lh)],fill=(int(r*255),int(g*255),int(b*255)))
d.rectangle([lx,ly,lx+lw,ly+lh],outline=(200,200,200))
d.text((lx,ly+lh+6),"편함",fill=(110,225,135),font=F(22,True)); d.text((lx+lw-58,ly+lh+6),"힘듦",fill=(255,105,85),font=F(22,True))
mx=lx+lw+60
d.text((mx,ly-20),"슈트 착용 시", fill=(235,235,235), font=F(28,True))
d.text((mx,ly+24),f"허리 근육 부담  ↓ {RED}% 감소", fill=(120,235,150), font=F(40,True))
cv.save(OUT); print("SAVED",OUT,cv.size,"RED",RED)
