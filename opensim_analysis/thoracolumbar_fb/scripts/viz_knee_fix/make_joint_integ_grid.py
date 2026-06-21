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
fig=plt.figure(figsize=(17,10)); gs=fig.add_gridspec(2,3,height_ratios=[1.05,1.0],hspace=0.2,wspace=0.1)
fig.suptitle("전신 관절 통합 검증 — 남은 동작(박스·걷기·나르기) 가능 여부",fontsize=20,fontweight='bold',y=0.99)
# top-left: shoulder origin + feasibility tables (text)
axt=fig.add_subplot(gs[0,:2]); axt.axis('off')
axt.text(0,1.0,"[1] 어깨 특이점 = 모델 원래 정의 (우리 수정 아님)",fontsize=14,fontweight='bold',color='#1a5',va='top')
axt.text(0,0.88,"• 어깨 좌표(shoulder_elv[0,155]·elv_angle·shoulder_rot·CustomJoint)가 ORIGINAL과 100% 동일\n"
                "  → no_coupler/forearm_v1 수정이 어깨를 건드리지 않음. forearm_v1 같은 '우리 버그' 아님.\n"
                "• 표준 Holzbaur YXY 파라미터화의 elevation gimbal — 어느 좌표로도 '서서 팔이 골반 아래' 불가\n"
                "  (전수 sweep 1377자세: 손 최저 y=-0.04=매달린 높이). 이는 사람도 동일(서서 팔만으로 바닥 못잡음=정상).",
         fontsize=11.5,va='top')
axt.text(0,0.46,"[2] 남은 동작별 필요 관절 — 통합 점검 결과",fontsize=14,fontweight='bold',color='#1a5',va='top')
rows=[["동작","필요 관절","가능?","근거"],
 ["걷기 (팔 스윙)","팔 앞뒤 스윙·보행 ROM","✅ 가능","스윙폭 0.79m (elv_angle ±35 @ elv0)"],
 ["들고 나르기","팔 앞 허리높이 안기","✅ 가능","앞-허리 reach 76자세"],
 ["박스(테이블 ~75-90cm)","팔 앞 허리높이 reach","✅ 가능","발접지+허리높이 envelope 내"],
 ["박스(바닥 0cm)","팔이 바닥 도달","⚠️ 숙여야 가능","서서 불가(정상)→상체 굴곡 필수"]]
tb=axt.table(cellText=rows,bbox=[0,0.0,1.0,0.42]); tb.auto_set_font_size(False); tb.set_fontsize(11)
for (r,c),cell in tb.get_celld().items():
    if r==0: cell.set_facecolor('#e8e8e8'); cell.set_text_props(fontweight='bold')
    elif r==4: cell.set_facecolor('#fff2cc')
    else: cell.set_facecolor('#e3f0e3')
    cell.set_edgecolor('#aaa')
# top-right: conclusion
axc=fig.add_subplot(gs[0,2]); axc.axis('off')
axc.text(0,1.0,"[3] 결론",fontsize=14,fontweight='bold',color='#a00',va='top')
axc.text(0,0.88,"■ 어깨 = 모델 한계 (우리 수정 X)\n  단 '한계'가 아니라 정상 거동:\n  사람도 서서 팔만으로 바닥 못 잡음.\n\n"
                "■ 확장성 있나? → 예.\n  걷기·나르기·테이블 lift 모두 가능.\n  바닥 lift만 상체 굴곡 필요(정상,\n  stoop/squat에서 이미 됨).\n\n"
                "■ 모델 교체 불필요.\n  박스 바닥은 숙임으로 해결되며\n  앞선 박스 문제의 본질은 발 접지\n  +동역학이었지 어깨 아님.\n\n"
                "■ viz TODO: 박스 큐브 렌더 표시\n  (방향 확정 후 디버그).",
         fontsize=11,va='top')
# bottom: 3 renders
for i,(p,t) in enumerate([("/tmp/cmp_render/box_render/jc_walk.png","걷기 — 팔 앞뒤 스윙 ✅"),
                          ("/tmp/cmp_render/box_render/jc_carry.png","나르기 — 앞으로 안기 ✅"),
                          ("/tmp/cmp_render/box_render/jc_floor.png","바닥 reach(서서) — 엉덩이까지만 ⚠️숙임필요")]):
    ax=fig.add_subplot(gs[1,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=12,fontweight='bold')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/joint_integration_grid.png"
fig.savefig(OUT,dpi=108,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
