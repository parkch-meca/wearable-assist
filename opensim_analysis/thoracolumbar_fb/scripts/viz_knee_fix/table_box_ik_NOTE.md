# 테이블 박스 도달 IK (2026-06-22)
전 자유도 IK(hip,knee,ankle,pelvis_tilt,lumbar,shoulder_elv,elv_angle,shoulder_rot,elbow)로
손을 박스 파지점에 맞추고 발 접지(per-frame pelvis_tx/ty)+균형(COM∈base) 패널티로 최적화.
결과: 테이블 50/40/30/20/10cm 모두 손-박스 gap≈0, 발매몰 0, 균형 OK.
=> 50cm 박스 들기 가능. 모델 한계 아님. 이전 105/75cm 불일치는 불완전 탐색 탓.
자연 자세(척추 중립 선호 패널티)면 깊은 squat+중립척추로 50cm 박스 파지.
