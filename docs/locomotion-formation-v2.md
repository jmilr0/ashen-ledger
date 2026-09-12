# Locomotion + formation v2 (kill conga)

**Owner:** Game Design · **For:** Engineering  
**Context:** User — conga-line follow, don’t face click direction. CoS paused hub expand. Ship this before stats/equip UI.

## 1) Face click / move yaw

**Intent:** Body faces where you’re going (click destination / move), not camera, not random wall-slide forever.

### Rules
1. On `moveToWorld(click)`: set `desiredYaw = atan2(click.x - pos.x, click.z - pos.z)` immediately as **intent**.
2. While moving: blend toward **intent yaw** with same damper as v1 (`TURN_RATE=12`, cap ~540°/s). Prefer intent over pure collision-slide velocity when `|shortestArc(intent, velocityYaw)| < 90°`.
3. If wall-slide only (velocity nearly perpendicular to intent for >0.25 s): face **slide velocity** so you don’t moonwalk; when free again, return to intent.
4. Speed < `FACE_MOVE_EPS` (0.15 m/s): **hold** yaw — no spin-on-arrive, no twitch to face the marker after stop.
5. Optional cheap stop-turn: if new click needs >90° and you’re stopped, yaw in place at ~360°/s for up to 0.35 s before stepping.

**Acceptance:** Click ahead-left → character turns toward that point while walking there. Stop on marker → no final spin. Slide along wall → faces along wall briefly, then re-aims when clear.

## 2) Loose formation (not 0.9 m conga)

**Kill:** single-file chain `anchor → next → next` at 0.9 m (reads as conga).

### Soft slots (BG-ish blob)
Relative to **controlled** facing (forward = move/intent yaw):

| Slot | Job default | Offset (forward, right) meters |
|---|---|---|
| 0 | Sergeant | (−1.4, −0.7) |
| 1 | Convers | (−1.4, +0.7) |
| 2 | Guide | (−2.6, −1.1) |
| 3 | Clerk | (−2.6, +1.1) |
| 4 | Surgeon | (−2.8, 0.0) |

- Spread **~2–3 wide**, depth 2 ranks — not a snake.
- `FOLLOW_SPACING` chain **retired** for hub follow.
- Chase: soft lerp / exp(−5…6·dt) toward **own slot** in leader space (recomputed each frame from controlled pos+yaw).
- Soft-slide collision per follower; if blocked, freeze that slot (no rubber-band).
- Yaw: each follower faces **own move delta** when speed ≥ eps; else lag toward controlled yaw (existing FOLLOW_YAW_LAG).
- On party switch: snap slots OK; damp yaw.
- Doorways ≥1.2 m: slots may temporarily compress toward trail (scale offsets ×0.55 when any follower softSlide fails twice) then expand — don’t cork.

**Acceptance:** Party reads as a wide squad behind you, not a single-file conga. Curve around parish without skating through walls. Switch 1–5: formation re-centers on new leader in <0.5 s facing settle.

## Out of scope this cut
Open-map expand (paused). Stats/equip sheet (next note). RMB objects (next after sheet or parallel if cheap).
