import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=6):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>16; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
fig=plt.figure(figsize=(15,9)); gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.5],wspace=0.07)
fig.suptitle("좌우 대칭 미러링 — 비대칭·akimbo 해결(성과) + 체간 stoop 잔여 (정직 보고)",fontsize=16,fontweight='bold',y=0.99)
for i,(p,t) in enumerate([("/tmp/cmp_render/interf/mirror_front.png","앞(FRONT) — 양팔 좌우 대칭,\nakimbo 없음, 양손 박스 (해결!)"),
                          ("/tmp/cmp_render/interf/mirror_side.png","옆(SIDE) — 체간 stoop\n(머리가 박스까지: 잔여 1개)")]):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=11,fontweight='bold')
ax=fig.add_subplot(gs[0,2]); ax.axis('off')
ax.text(0,1.0,"[성과] 미러링이 사용자 지적 해결",fontsize=14,fontweight='bold',color='#1a7',va='top')
ax.text(0,0.92,"잘 되는 오른팔 관절각을 좌우 거울 대칭(미러 부호 실측=전부 +1)으로\n왼팔에 복사. auto-IK 양팔 독립 → 비대칭 문제 해소.",fontsize=11,va='top')
rows=[["검증 항목(독립, 그림만)","판정"],
 ["좌우 대칭","✅ 양팔 거울 대칭"],
 ["아킴보(팔꿈치 벌어짐)","✅ 없음"],
 ["손등 접촉","✅ 아님(손바닥 향함)"],
 ["손-박스 관통","✅ 없음"],
 ["발 전체 접지","✅"],
 ["박스 테이블 위 / 50cm","✅ / ✅"]]
tb=ax.table(cellText=rows,bbox=[0,0.55,1.0,0.32]); tb.auto_set_font_size(False); tb.set_fontsize(10.5)
for (r,c),cell in tb.get_celld().items():
    if r==0: cell.set_facecolor('#e8e8e8'); cell.set_text_props(fontweight='bold')
    else: cell.set_facecolor('#dff0df')
    cell.set_edgecolor('#aaa')
ax.text(0,0.50,"→ 사용자 지적('오른쪽을 왼쪽 대칭으로')이 정확했고, 미러링으로 비대칭·akimbo·손등 모두 해결.",fontsize=11,fontweight='bold',color='#225',va='top')
ax.text(0,0.40,"[잔여 1개 — 검증자 유일 FAIL 사유]",fontsize=13,fontweight='bold',color='#a00',va='top')
ax.text(0,0.32,"• side뷰 상체가 깊게 숙여 머리가 박스 높이까지 내려옴.\n"
               "• 원인: 50cm(무릎높이) 테이블 박스를 잡으려면 깊이 굽혀야 하고,\n  척추 전굴(lumbar)로 머리가 떨어짐.\n"
               "• straight-spine hip-hinge(머리 들기) 자동 시도는 손이 얼굴로 가 실패.",fontsize=10.5,va='top',color='#333')
ax.text(0,0.15,"[정량 영향 0] 손목 메모리 해제만, .osim locked=true 불변.",fontsize=10.5,va='top',color='#225')
ax.text(0,0.07,"[결정 요청] (가)이 stoop을 낮은 테이블 들기의 자연 자세로 수용 →모션/동영상\n"
               "        (나)머리 들기 필요 →체간 수동 조정(자동 실패, 신중 튜닝 필요)",fontsize=10.8,fontweight='bold',va='top',color='#7a0000')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/box_grasp_mirror_report.png"
fig.savefig(OUT,dpi=110,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
