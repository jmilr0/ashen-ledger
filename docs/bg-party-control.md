# BG party control — leader pick + follow

**Owner:** Game Design · **For:** Engineering (CoS order 1) · Art walk cycles (order 2)  
**User:** Party doesn’t walk forward / glides; need select leader, others follow that person, closer to BG.

## Problem to kill
1. Click-to-move pawn always looks like Clerk (`PATH.player` / clerk.glb) even when `controlledId` is Sergeant etc.
2. Followers may still feel detached from “who I picked.”
3. No foot walk cycle → reads as glide.

## 1) Leader is the pawn (hard rule)

| Input | Result |
|---|---|
| `1`–`5` / Tab / strip / “Set hub face” | `controlledId = that job` |
| LMB ground | **Only the leader** pathfinds / click-moves |
| Others | Soft-slot follow **that leader’s** transform |

On select:
1. Swap **playerMesh** to that job’s character GLB (sergeant.glb, guide.glb, …) — not always clerk.
2. Hide that job’s follower mesh; show previous leader as follower again.
3. Snap formation slots relative to new leader (existing FORMATION_SLOTS in leader space from v2).
4. Camera / interact / bag rules unchanged (bag pip ≠ face still OK).

**Acceptance:** Press `2` (Sergeant) → big pawn is Guillem; click ahead → Guillem walks there facing the click; Catalana/Peire/Arnau/Elias fan in loose slots behind **him**.

## 2) Formation (keep v2 slots)

Slots stay job-relative in **leader** space (already in `locomotion-formation-v2.md`):

| Job | Offset (fwd, right) m |
|---|---|
| Sergeant | (−1.4, −0.7) |
| Convers | (−1.4, +0.7) |
| Guide | (−2.6, −1.1) |
| Clerk | (−2.6, +1.1) |
| Surgeon | (−2.8, 0) |

When job **is** leader: that slot unused (they’re the pawn). Others chase their slots. Doorway compress OK.

## 3) Facing (keep intent yaw)

Leader: click intent yaw + wall-slide override from v2.  
Followers: face own move when speed ≥ eps; else lag to leader yaw.

## 4) Walk cycles (with Art — can stub)

**Engineering hooks now:**
- `moving = horizontalSpeed >= FACE_MOVE_EPS` (0.15 m/s)
- Expose on leader + each visible follower: `isMoving`, `moveSpeed`, `facingYaw`
- Prefer Art clip `walk` / `idle` on character GLBs when present; else keep glide but **bob or stride placeholder** so it doesn’t read frozen (optional simple sine foot bob until Art drops).

**Art (order 2):** walk + idle on party GLBs (clerk/sergeant/convers/guide/surgeon). Loop walk while `isMoving`; crossfade to idle on stop. No root motion required first cut — in-place cycle + code translation is fine (BG-adjacent).

## Out of scope this cut
Hub expand, new combat, multi-select pathing for all five independently. One leader only.

## Acceptance
- [ ] 1–5 changes who the click-to-move body is (mesh + name).
- [ ] Others follow that body in a wide squad, not a clerk-led conga with a fake face.
- [ ] Click facing still works on the leader.
- [ ] Walk cycle or stub bob when moving; idle when stopped.
