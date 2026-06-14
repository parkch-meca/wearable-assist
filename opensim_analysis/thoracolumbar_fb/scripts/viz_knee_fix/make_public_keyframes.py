from PIL import Image, ImageDraw, ImageFont
import os, json, numpy as np
RENDER="/tmp/cmp_render/pub_vout"
meta=json.load(open(os.path.join(RENDER,"meta.json"))); N=len(meta)
OUTDIR="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review"
OUT=os.path.join(OUTDIR,"stoop_public_keyframes_grid.png")
def F(s,b=False): return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"%("Bold" if b else "Regular"),s)
def crop(p):
    im=Image.open(p).convert("RGB"); a=np.asarray(im).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>26; ys,xs=np.where(m)
    return im.crop((max(0,xs.min()-8),max(0,ys.min()-8),min(im.width,xs.max()+8),min(im.height,ys.max()+8)))
targets=[(0.0,"준비"),(1.25,"굽히는 중"),(2.75,"가장 깊이"),(3.75,"펴는 중"),(5.0,"복귀")]
def near(t): return min(range(N),key=lambda i:abs(meta[i]['t']-t))
idxs=[(near(t),lab) for t,lab in targets]
PH=300
cropped={}
for idx,_ in idxs:
    for c in ['off','on']:
        im=crop(os.path.join(RENDER,f"f{idx:04d}_{c}_side.png"))
        cropped[(idx,c)]=im.resize((int(im.width*PH/im.height),PH))
colw=max(im.width for im in cropped.values()); PAD=12; TOP=96
W=5*colw+6*PAD; H=TOP+2*PH+3*PAD+44
BG=(30,32,38); cv=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(cv)
d.text((PAD,10),"일반인용 stoop 동영상 키프레임 — 슈트 없음(위) vs 슈트 착용(아래)", fill=(255,255,255), font=F(22,True))
d.text((PAD,44),"허리 굽힐수록 '슈트 없음' 허리가 빨개짐(힘듦). '슈트 착용'은 덜 빨개짐(초록 유지) = 부담↓. 초록=편함, 빨강=힘듦.", fill=(255,180,90), font=F(13))
labrow=[("off","슈트 없음",(255,110,90)),("on","슈트 착용",(110,225,135))]
for ci,(idx,lab) in enumerate(idxs):
    x=PAD+ci*(colw+PAD); m=meta[idx]
    d.text((x+6,TOP-22),f"{lab}  ↓{m['peak_red']:.0f}%",fill=(255,255,0),font=F(14,True))
    for ri,(ck,clab,col) in enumerate(labrow):
        y=TOP+ri*(PH+PAD); im=cropped[(idx,ck)]
        cv.paste(im,(x+(colw-im.width)//2,y))
        d.rectangle([x,y,x+colw,y+PH],outline=col,width=2)
        if ci==0: d.text((x+4,y+4),clab,fill=col,font=F(13,True))
cv.save(OUT); print("SAVED",OUT,cv.size)
