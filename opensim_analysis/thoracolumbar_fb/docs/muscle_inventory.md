# Muscle Inventory — MaleFullBodyModel_v2.0_OS4_moco_stoop.osim

**Date**: 2026-04-24
**Total muscles**: 620

## Distribution by prefix (all muscles in model)

| Prefix | Count | Anatomical group | Notes |
|---|---:|---|---|
| ExtIC | 76 | External intercostal | Rib-to-rib |
| IntIC | 76 | Internal intercostal | Rib-to-rib |
| E (E0–E?) | **92** | **External oblique** (EO) | Heavy fiber split across ribs 5–12 |
| MF | 50 | Multifidus (thoraco-lumbar) | Fiber elements |
| multifidus | 46 | Multifidus (cervico-thoracic) | e.g. multifidus_L4_T12, multifidus_T11_T7 |
| LTpT | 42 | Longissimus thoracis pars thoracis | T1–T12 × R/L + extras |
| QL | 36 | Quadratus lumborum | Fiber elements (post/mid/ant × level) |
| LD | 28 | Latissimus dorsi | Not in Phase 1a |
| trap | 28 | Trapezius | Not in Phase 1a |
| IL | 24 | Iliocostalis (lumborum + thoracis) | L1–L4 + R5–R12 bilateral |
| Ps | 22 | **Psoas** (not requested) | Present but outside scope |
| SerrAnt | 20 | Serratus anterior | Not in Phase 1a |
| E (E0–E?) | (see above) | | |
| splen | 12 | Splenius | Cervical |
| glut | 12 | Gluteus | Not in Phase 1a |
| IO | 12 | **Internal oblique** | IO1–IO6 × R/L |
| LTpL | 10 | Longissimus thoracis pars lumborum | L1–L5 × R/L |
| TR | 10 | Trapezius-related | |
| deepmult | 8 | Deep multifidus (cervical) | T1–T2 ↔ C5–C7 |
| supmult | 6 | Superficial multifidus (cervical) | T1–T2 ↔ C4–C6 |
| rect | 4 | rect_abd_{r,l} + rect_fem_{r,l} | Rectus abdominis = 2 |
| Other (splen, DELT, PECM, SUPSP, INFSP, etc.) | ~30 | Upper extremity + head | Not in Phase 1a |

## Phase 1a target categories — detailed

### 1. Erector Spinae (76 total)

| Muscle group | Naming | Count | Comment |
|---|---|---:|---|
| Iliocostalis (IL) | IL_L{1..4}_{r,l} (lumbar) + IL_R{5..12}_{r,l} (rib attachments) | **24** | Each level one fiber per side — already concise |
| Longissimus thoracis pars thoracis (LTpT) | LTpT_T{1..12}_{r,l} + extras | **42** | ThoracolumbarFB splits each thoracic level into ~1.75 fibers on avg |
| Longissimus thoracis pars lumborum (LTpL) | LTpL_L{1..5}_{r,l} | **10** | Clean, one per level per side |

### 2. Deep stabilizers (146 total)

| Group | Count | Notes |
|---|---:|---|
| MF (thoraco-lumbar multifidus) | 50 | Fiber-level split |
| multifidus_* (cervico-thoracic) | 46 | Range multifidus_L4_T12 … multifidus_T11_T7 |
| deepmult + supmult (cervical) | 14 | Small cervical stabilizers |
| QL (quadratus lumborum) | 36 | Fiber-level split (post/mid/ant × level × side) |

### 3. Abdominal (106 total; user rule "1-2 fibers per side" applies)

| Muscle | Count | Naming | User rule |
|---|---:|---|---|
| Rectus abdominis (RA) | 2 | rect_abd_r, rect_abd_l | include all |
| External oblique (EO) | 92 | E{0..}_R{5..12}_{r,l} | **pick 1-2 per side** → ~4 |
| Internal oblique (IO) | 12 | IO{1..6}_{r,l} | **pick 1-2 per side** → ~4 |

### 4. Not in Phase 1a (reference only)

- Psoas (Ps, 22): hip flexor, relevant if lumbar-femur interaction modeled (future scope)
- Latissimus dorsi (LD, 28): back/shoulder, reach/overhead
- ExtIC + IntIC (152 total): intercostals, respiration — not load-bearing in stoop
- Upper-extremity muscles (DELT, PECM, SUPSP, INFSP, trap, SerrAnt, scalenus etc.)
- Lower-extremity (glut, quad, vas, bifem, tib, soleus, iliacus etc.)

---

## Phase 1a selection — candidate sets

| Set | Definition | Count | Tradeoff |
|---|---|---:|---|
| **A** (literal spec) | IL + LTpT + LTpL + all MF groups + all QL + (rect_abd + 4 EO + 4 IO) | **232** | Maximum completeness; MocoTrack convergence slow |
| **B** (anatomical level) | IL 24 + LTpT 24 (one per level) + LTpL 10 + MF 16 + multifidus 16 + QL 6 + rect_abd 2 + 4 EO + 4 IO | **~106** | Balanced, near ±50% threshold of "~70" estimate |
| **C** (strict "~70") | IL 24 + LTpT 12 + LTpL 10 + MF 12 + QL 4 + rect_abd 2 + 4 EO + 4 IO | **~72** | Matches user estimate; requires aggressive fiber subsampling |

**User decision required** — which set? (B recommended as balanced default.)
