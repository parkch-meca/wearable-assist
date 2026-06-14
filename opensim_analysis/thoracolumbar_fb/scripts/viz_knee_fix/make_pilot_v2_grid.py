from PIL import Image, ImageDraw, ImageFont
import os, json, numpy as np
D=json.load(open("/tmp/cmp_render/frames/frame_2.500.json"))
SRC="/tmp/cmp_render/pilot_v2"
OUTDIR="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review"
OUT=os.path.join(OUTDIR,"stoop_pilot_v2_grid.png")
VMAX=max(v['off'] for v in D['muscles'].values()); AMIN=0.03; GAMMA=0.85
INF=[(0.00,0.001,0.000,0.014),(0.13,0.122,0.047,0.281),(0.25,0.282,0.062,0.408),
     (0.38,0.451,0.122,0.412),(0.50,0.612,0.182,0.353),(0.63,0.767,0.275,0.250),
     (0.75,0.894,0.412,0.145),(0.88,0.969,0.620,0.130),(1.00,0.988,0.998,0.645)]
def inferno(x):
    x=max(0.,min(1.,x))
    for i in range(len(INF)-1):
        t0,r0,g0,b0=INF[i]; t1,r1,g1,b1=INF[i+1]
        if x<=t1:
            f=(x-t0)/(t1-t0) if t1>t0 else 0
            return (r0+(r1-r0)*f,g0+(g1-g0)*f,b0+(b1-b0)*f)
    return INF[-1][1:]
def font(sz,b=False):
    return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"%("Bold" if b else "Regular"),sz)

def autocrop(im, pad=18):
    a=np.asarray(im.convert("RGB")).astype(int)
    bg=np.array([int(0.11**(1/2.2)*255)]*3)  # approx; use corner pixel instead
    bgpix=a[2,2]
    diff=np.abs(a-bgpix).sum(2)
    mask=diff>22
    ys,xs=np.where(mask)
    if len(xs)<10: return im
    x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max()
    x0=max(0,x0-pad); y0=max(0,y0-pad); x1=min(im.width,x1+pad); y1=min(im.height,y1+pad)
    return im.crop((x0,y0,x1,y1))

# load + crop the 4 renders to common-ish size
panels={}
for cond in ['off','on']:
    for vn in ['side','back']:
        im=Image.open(os.path.join(SRC,f"pilot_{cond}_{vn}.png"))
        panels[(cond,vn)]=autocrop(im)

# layout: 2 rows (side, back) x 2 cols (OFF, ON); scale each crop to fixed height
PH=470;
def scaled(im):
    w=int(im.width*PH/im.height); return im.resize((w,PH))
sc_panels={k:scaled(v) for k,v in panels.items()}
colw=max(max(sc_panels[('off',v)].width, sc_panels[('on',v)].width) for v in ['side','back'])
PAD=14; LEFT=70; CBAR=130
W=LEFT+2*colw+3*PAD+CBAR
TOP=140
H=TOP+2*PH+3*PAD+150
cv=Image.new("RGB",(W,H),(255,255,255)); d=ImageDraw.Draw(cv)
d.text((PAD,10),"Stoop PILOT v2 — ES 활성도 색상 (inferno, 작동범위 정규화) OFF vs ON", fill=(0,0,0), font=font(22,True))
d.text((PAD,44),"t=2.5s Hold peak · per-muscle 자기 활성도 · 정규화 %.2f→%.2f (작동 ES) · 뼈/구조 동일(검증 완료) · .osim 불변"%(AMIN,VMAX),
       fill=(60,60,60), font=font(13))
off_mean=np.mean([v['off'] for v in D['muscles'].values()]); on_mean=np.mean([v['on'] for v in D['muscles'].values()])
d.text((PAD,66),"주력 ES = iliocostalis(IL_R10/11/12). IL_R11: OFF 0.31 → ON 0.22 (29%↓). 아래 OFF가 ON보다 더 밝은 주황/노랑.",
       fill=(120,0,0), font=font(14,True))
cols=[("off","Suit OFF (0 N·m)"),("on","Suit ON (24 N·m / 200 N)")]
rows=[("side","SIDE"),("back","BACK")]
for ci,(ck,clab) in enumerate(cols):
    x=LEFT+PAD+ci*(colw+PAD)
    d.text((x+colw//2-80,TOP-26),clab,fill=(0,0,0),font=font(15,True))
for ri,(rk,rlab) in enumerate(rows):
    y=TOP+ri*(PH+PAD)
    d.text((6,y+PH//2),rlab,fill=(0,0,0),font=font(15,True))
    for ci,(ck,clab) in enumerate(cols):
        x=LEFT+PAD+ci*(colw+PAD)
        im=sc_panels[(ck,rk)]
        cv.paste(im,(x+(colw-im.width)//2,y))
        d.rectangle([x,y,x+colw,y+PH],outline=(150,150,150))
# colorbar
cbx=LEFT+2*colw+3*PAD; cby=TOP; cbw=34; cbh=2*PH+PAD
for i in range(cbh):
    n=1-i/cbh; r,g,b=inferno(n)
    d.line([(cbx,cby+i),(cbx+cbw,cby+i)],fill=(int(r*255),int(g*255),int(b*255)))
d.rectangle([cbx,cby,cbx+cbw,cby+cbh],outline=(80,80,80))
d.text((cbx-2,cby-24),"ES activation",fill=(0,0,0),font=font(12,True))
d.text((cbx+cbw+4,cby-4),f"{VMAX:.2f}",fill=(0,0,0),font=font(12))
d.text((cbx+cbw+4,cby+cbh-12),f"{AMIN:.2f}",fill=(0,0,0),font=font(12))
# top muscle table
rows2=[(nm,D['muscles'][nm]['off'],D['muscles'][nm]['on']) for nm in D['muscles']]
rows2.sort(key=lambda r:-r[1]); rows2=rows2[:6]
ty=TOP+2*PH+2*PAD+8
d.text((PAD,ty-2),"주력 ES 근육 활성도 (OFF → ON):",fill=(0,0,0),font=font(13,True))
for i,(nm,o,n) in enumerate(rows2):
    d.text((PAD+i*235, ty+22), f"{nm}:  {o:.2f} → {n:.2f}  ({100*(o-n)/o:.0f}%↓)", fill=(150,30,0), font=font(12,True))
d.text((PAD,ty+50),"검증: ⭐ OFF가 ON보다 명확히 더 뜨거운 색인가? (작동 iliocostalis 영역에서 OFF 주황~노랑 vs ON 빨강~자홍)",
       fill=(0,0,0),font=font(13,True))
cv.save(OUT); print("SAVED",OUT,cv.size)
