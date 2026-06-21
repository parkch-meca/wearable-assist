import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=6):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>18; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
fig=plt.figure(figsize=(16,9.5)); gs=fig.add_gridspec(2,3,height_ratios=[1,1],width_ratios=[1,1,1.4],wspace=0.06,hspace=0.16)
fig.suptitle("50cm 테이블 박스 들기 — 테이블 간섭 고려 (squat vs stoop)",fontsize=19,fontweight='bold',y=0.99)
imgs=[("/tmp/cmp_render/interf/squat_side.png","squat 옆 — ❌ 손 21cm 부족",(0,0)),
      ("/tmp/cmp_render/interf/squat_front.png","squat 앞",(1,0)),
      ("/tmp/cmp_render/interf/stoop_side.png","stoop 옆 — ✅ 박스 파지",(0,1)),
      ("/tmp/cmp_render/interf/stoop_front.png","stoop 앞",(1,1))]
for p,t,(r,c) in imgs:
    ax=fig.add_subplot(gs[r,c]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=12,fontweight='bold',color=('#a00' if 'squat' in t else '#1a7'))
ax=fig.add_subplot(gs[:,2]); ax.axis('off')
ax.text(0,1.0,"[판단] 테이블 간섭 넣으면:",fontsize=15,fontweight='bold',va='top')
ax.text(0,0.92,"• squat = ❌ 불가\n  무릎이 앞으로 못 감(테이블이 막음)\n  → 못 내려가 손 21cm 부족\n  (CHEOL HOON님 지적대로)\n\n"
               "• stoop = ✅ 가능\n  고관절 hinge, 무릎 곧음(다리 수직)\n  다리가 테이블 뒤(침범 0cm)\n  발은 테이블 앞 접지\n  손이 테이블 너머 박스에 닿음(gap 0)\n",fontsize=12,va='top')
rows=[["자세","손-박스","다리 침범","발접지","균형","판정"],
 ["squat","21cm 부족","0(막힘)","OK","OK","❌"],
 ["stoop","0.0cm","0cm","OK","OK","✅"]]
tb=ax.table(cellText=rows,bbox=[0,0.40,1.0,0.18]); tb.auto_set_font_size(False); tb.set_fontsize(10.5)
for (rr,cc),cell in tb.get_celld().items():
    if rr==0: cell.set_facecolor('#e8e8e8'); cell.set_text_props(fontweight='bold')
    elif rr==1: cell.set_facecolor('#fbe9e7')
    else: cell.set_facecolor('#dff0df')
    cell.set_edgecolor('#aaa')
ax.text(0,0.34,"[결론] 50cm 테이블 박스 = stoop으로 가능.\n"
               "  단 squat은 테이블이 무릎을 막아 불가.\n"
               "  → 테이블 박스 들기 동영상은 'stoop(고관절 hinge)' 자세로.\n\n"
               "[이전 IK 정정] 다리 앞 뻗는 비현실 해는\n"
               "  테이블 간섭 제약 누락 탓. 간섭 넣으니 stoop만 성립.\n\n"
               "[stoop 자세] hip 43°, 무릎 곧음, 척추 굴곡(lumbar~40°)\n"
               "  = 허리 부하 큰 scenario(슈트 효과 부각). 발 테이블 앞 접지.",fontsize=11,va='top',color='#225')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/table_interference_grid.png"
fig.savefig(OUT,dpi=108,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
