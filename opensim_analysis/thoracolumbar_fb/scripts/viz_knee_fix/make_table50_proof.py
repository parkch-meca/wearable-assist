import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=8):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>20; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
fig=plt.figure(figsize=(16,9)); gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.45],wspace=0.06)
fig.suptitle("50cm 테이블 + 30cm 박스 들기 — 가능 (근거: 전 자유도 IK)",fontsize=19,fontweight='bold',y=0.99)
for i,(p,t) in enumerate([("/tmp/cmp_render/table50n/table_side.png","옆(SIDE) — 박스 파지 순간"),
                          ("/tmp/cmp_render/table50n/table_front.png","앞(FRONT)")]):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=13,fontweight='bold')
ax=fig.add_subplot(gs[0,2]); ax.axis('off')
ax.text(0,1.0,"[판단] 50cm 테이블 박스 들기 = 가능 ✅",fontsize=15,fontweight='bold',color='#1a7',va='top')
ax.text(0,0.90,"전 자유도 IK(발접지+균형+유효관절범위) 결과:",fontsize=12,va='top')
rows=[["테이블","손-박스 gap","발 매몰","균형","판정"],
 ["50cm","0.1cm","0cm","OK","✅ 가능"],
 ["40cm","0.0cm","0cm","OK","✅ 가능"],
 ["30cm","0.0cm","0cm","OK","✅ 가능"],
 ["20cm","0.0cm","0cm","OK","✅ 가능"],
 ["10cm","0.0cm","0cm","OK","✅ 가능"]]
tb=ax.table(cellText=rows,bbox=[0,0.50,1.0,0.36]); tb.auto_set_font_size(False); tb.set_fontsize(10.5)
for (r,c),cell in tb.get_celld().items():
    if r==0: cell.set_facecolor('#e8e8e8'); cell.set_text_props(fontweight='bold')
    elif r==1: cell.set_facecolor('#dff0df')
    cell.set_edgecolor('#aaa')
ax.text(0,0.43,"[1] 손 최저 도달(발접지+균형) = 사실상 바닥까지\n"
               "   풀바디 자세(무릎+고관절+팔)면 10cm 박스(파지 25cm)도 gap0.\n"
               "   → 테이블 하한 ≈ 바닥. 50cm는 여유롭게 가능.",fontsize=11,va='top',color='#225')
ax.text(0,0.24,"[모순 해소] 이전 105cm/75cm/'엉덩이'는 제 자세·팔 탐색이\n"
               "   불완전했던 탓(팔만 elevation, 단순 coupling). 전 자유도 IK로\n"
               "   풀면 50cm 닿음. → 모델 이상 아님(CHEOL HOON님 지적 맞음).",fontsize=11,va='top',color='#a00')
ax.text(0,0.05,"[자세] 깊은 squat + 중립 척추(lumbar -2°) + 발 접지 + 손 박스 접촉\n"
               "   = 이상적 lifting form. 박스(갈색)·테이블(회색) 렌더 표시됨.",fontsize=11,va='top')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/table50_box_proof_grid.png"
fig.savefig(OUT,dpi=110,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
