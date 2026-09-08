# Locomotion feel — BG-like (hub)

**Owner:** Game Design · **For:** Engineering (CoS order 1)  
**Canon:** Broken Seal story, no BG IP. Click-to-move stays.

Tune targets for first cut — iterate after clickable.

## 1) Face velocity yaw (controlled)

**Problem now:** `rotation.y = atan2(dx, dz)` snaps every frame → skate/twitch on micro path corrections.

**Feel:**
- Derive desired yaw from **horizontal move delta this frame** (resolved collision step), not raw path vector when step is tiny.
- If moved horizontal speed < **0.15 m/s**, keep current yaw (no jitter at arrive / against wall).
- Otherwise smooth toward desired yaw:
  - Turn rate cap ≈ **540°/s** (`~9.4 rad/s`) while walking
  - Or exp damp: `yaw += shortestArc(desired - yaw) * (1 - exp(-12 * dt))`
- Arrive: clear pathTarget; **do not** spin to face last click if already within 0.08 m.

Click-to-move marker unchanged.

## 2) Follower soft follow (no skate / cork)

**Keep:** ~0.9 m chain spacing, soft-slide collision, off-lane carts/fences, doorways ≥1.2 m.

**Feel fixes:**
- **Yaw:** followers use same smooth yaw as leader (or lag leader yaw by ~0.05–0.1 s), **not** instant `mesh.rotation.y = facing`.
- **Chase:** current exp(-9·dt) is fine for position; if they skate sideways around corners, lower to **exp(-6·dt)** and increase FOLLOW_SPACING slightly to **1.0 m** only if corking returns.
- **Cork:** never push a follower into a collider that blocks the controlled character’s next step — if softSlide fails, freeze that slot this frame (don’t rubber-band through wall).
- On party switch (`setControlled` snap): snap positions OK; still **smooth yaw** next frames.

## 3) Optional stop-turn (ship behind a tiny flag or always-on if cheap)

When pathTarget cleared (arrive or cancel) **and** player issued a new click within **0.35 s** that requires >90° turn: allow in-place yaw toward new target at **360°/s** before stepping (BG “plant and turn”).

If not cheap for first cut: **skip** — velocity yaw alone is enough. Revisit if turns look moonwalk.

## Acceptance (first cut)
1. Walk a curve — body yaws smoothly, no frame-snap.
2. Stop at marker — no final spin twitch.
3. Four followers trail without skating through walls or corking doorways.
4. 1–5 switch doesn’t leave bodies facing wrong for >0.5 s.

## Out of scope this cut
Bigger open map, combat RTwP, new verbs. Locomotion hub only.
