import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np, json
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=6):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>16; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
D=json.load(open('/tmp/cmp_render/headup_frame_hi2.json')).get('diag',{})
fig=plt.figure(figsize=(16,9.6)); gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.7],wspace=0.06)
fig.suptitle("박스 옆면 손바닥 파지 — 씬 30cm 확정 · 간섭 없음(측정) · 체간 과굴곡=구조한계 (NOT-SOLVED, 정직 보고)",
             fontsize=14.5,fontweight='bold',y=0.995,color='#7a0000')
for i,(p,t) in enumerate([("/tmp/cmp_render/interf/t30hi2_front.png","앞 — 양손 박스 옆면 대칭 파지 (도달 성공)"),
                          ("/tmp/cmp_render/interf/t30hi2_side.png","옆 — 등이 거의 수평(과굴곡). 다리는 테이블 앞")]):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=10.5,fontweight='bold')
ax=fig.add_subplot(gs[0,2]); ax.axis('off')
ax.text(0,1.0,"[씬] 사용자 확정 적용 ✅",fontsize=13,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.945,"• 테이블 30cm + 박스 30cm (상단 60cm) → 파지점 45~54cm\n"
               "• 50cm 테이블(파지 65cm) → 30cm(파지 45cm)로 낮춤",fontsize=10,va='top')
ax.text(0,0.85,"[간섭] 다리-테이블 = 없음 (측정) ✅",fontsize=13,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.795,f"• 정강이 관통점 0개, 앞모서리까지 {D.get('gap_to_edge_cm',0):.0f}cm 여유\n"
               f"• 무릎 {49}cm 로 30cm 테이블 위로 통과 (차단 없음)\n"
               "• 옆면 렌더서 다리는 파란 테이블 '앞쪽'에 명확히 분리\n"
               "• 단, 발끝이 테이블 앞모서리에 빠듯 → 반투명 렌더선 오독 소지",fontsize=10,va='top')
ax.text(0,0.635,"[도달] 손바닥 박스 옆면 = 성공 ✅",fontsize=13,fontweight='bold',color='#225',va='top')
ax.text(0,0.58,f"• palm 오차 {D.get('palm_err_cm',0):.1f}cm, 손끝 {D.get('tip_err_cm',0):.1f}cm (밀착 수준)\n"
               "• 손바닥면이 박스 옆면(-Z) 향함, 위감싸기·손날 아님",fontsize=10,va='top')
ax.text(0,0.48,"[문제] 체간 과굴곡 = 구조 한계 ❌",fontsize=13,fontweight='bold',color='#a00',va='top')
ax.text(0,0.40,f"• 독립검증 3회 모두 NOT-SOLVED: 등 시각 70~80° (거의 수평)\n"
               "• 원인(기하): 자연 semi-stoop서 어깨-파지점 거리 ~66cm >\n"
               "  팔 길이 ~56cm → 팔이 ~10cm 짧음\n"
               "• 모델에 견갑(scapula) protraction 자유도 없음 → 어깨를\n"
               "  앞·아래로 못 내밈 → 체간+골반 극단 굴곡으로만 보상\n"
               "• 파지높이 45·54cm 두 경우 모두 동일 벽 (재확인)",fontsize=10,va='top',color='#333')
ax.text(0,0.185,"[결론] 정직 보고",fontsize=12.5,fontweight='bold',color='#7a0000',va='top')
ax.text(0,0.13,"30/30 옆손바닥 파지는 도달·간섭은 OK나, 자연 체간각으론\n"
               "달성 불가(구조 한계, ebf92d5 재확인). 같은 증상 2회 → IK 반복 중단.\n"
               "자동 SO 미실행. 다음 방향은 사용자 결정 대기.",fontsize=10,va='top',color='#333')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/box_table30_grasp_grid.png"
fig.savefig(OUT,dpi=110,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
