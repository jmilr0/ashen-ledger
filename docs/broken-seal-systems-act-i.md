# The Broken Seal — Systems (Act I)

**Owner:** Game Design  
**For:** Engineering / Art / Narrative  
**Canon:** no magic, no hotbar miracles, five fixed jobs. Merrowgate combat docs are retired.

## Five jobs (party = always these five)

| Id | Role | Hub / dialogue | Combat job | Soft fail if down |
|---|---|---|---|---|
| `clerk` | The Clerk | Seal inspect, forge check, gate talk, Latin/Occitan checks | Rear: read enemy badges / call hold; staff poke only | Cannot verify seal or talk gates |
| `sergeant` | The Sergeant | Watch, intimidate, castle/road sense | Front rank: spear / mail soak; sets formation facing | No front rank — alley fights get messy |
| `convers` | The Convers | Locks, wagons, supplies, keys | Mid: club, shove, burn/cut rope interactables | Lose lock/wagon actions |
| `guide` | The Guide | Stealth routes, village lies, *draille* | Flank / loft: crossbow when elevated; flee-path | No loft shot / bad ambush reads |
| `surgeon` | The Surgeon | Triage talk only | Rear: no damage skill — after fight or mid-fight **Stabilize** (see below) | Bleeds stay; companions can be out for Act |

Party order for UI / default formation (left→right facing north):  
`guide` · `sergeant` · `convers` · `clerk` · `surgeon`  
(Front contact = sergeant + convers; rear = clerk + surgeon; guide may leave formation for loft/flank.)

## Formation combat (slice)

Replace Attack/Unmake/Defend fantasy loop.

### Layout
- **Lane:** 3 tiles deep × 2–3 wide (alley / ferry / porch). Not a full grid CRPG — enough that “front” vs “loft” matters.
- **Player slots:** front-left, front-right, rear-left, rear-right, optional loft (Guide only when scene flag `has_loft`).
- **Enemy:** 1–3 foes in opposite front; optional loft crossbow.

### Round order
1. Player assigns **one action per standing companion** (any order, or fixed sergeant→convers→guide→clerk→surgeon — Engineering pick one and stick).
2. Enemy phase (each living foe once).
3. If anyone has `bleeding`, Surgeon may have spent their action to Stabilize; unresolved bleeds tick at round end.

### Actions by job (Act I)

| Job | Actions |
|---|---|
| Sergeant | **Hold line** (+def to front rank this round), **Thrust** (melee front), **Shove** (push foe out of doorway / into water if flag) |
| Convers | **Club**, **Cut rope** / **Kick latch** (scene interact when flagged), **Brace wagon** (+1 front def this round; clears like Hold) |
| Guide | **Bolt** (needs loft or flank clear), **Slip** (leave formation → loft if available), **Point** (reveal borrowed badges — Clerk can then Call out) |
| Clerk | **Call out** (if badges exposed: one foe wavers / skips attack), **Staff** (weak melee), **Show seal** (risk: if `seal_intact` and scene allows, pilgrims or foes hesitate — once per fight) |
| Surgeon | **Stabilize** (clear `bleeding` on one ally; uses the turn — if nobody bleeding, still spends turn: *no one needs the iron*), **Drag** (pull downed ally to rear) |

No MP. No holy damage. “Skill” = job + position + scene flag.

### Injury
- HP per person (small numbers). At 0 → `downed` (not dead).
- Some enemy hits apply `bleeding`. Without Stabilize before 2 round-end ticks → companion `out_for_act` (unavailable rest of Act I map; story can still reference them).
- Rest / boiled wine between scenes: Surgeon present → clear bleeds + partial HP; else HP only.

### Act I encounters (wire these)
1. **Borrowed-badge ambush** (road) — 2 bandits front; Guide can Point badges; Clerk Call out; optional loft later.
2. **Ferry rope** — Convers **Cut rope** is the **only** win (`ropeCut`); wiping River Watch opens/stresses Cut (no Hold needed) but does not end the fight. Sergeant Holds while column crosses.
3. **Priory deferred to Act II** — do not build yet.

## Seal system

Flags (align with Narrative):
- `chest_carrier`: `clerk` | `sergeant` | `convers` (Guide/Surgeon cannot carry Act I — hands full / not trusted with bag)
- `seal_intact`: bool — peeking the true letter sets false + `party_is_forger`
- True letter is inventory item `true_letter`; fake council letter stays in chest fiction

Rules:
- **Inspect fake seal** (Clerk, free at Fontfroide / goldsmith): reveals fault; no flag break.
- **Break true seal to peek:** sets `seal_intact=false`, `party_is_forger=true`. Narbonne agent scene gets harder; some gates refuse Clerk talk.
- **Show seal in combat / square:** only if `seal_intact`; once per scene; does not damage — buys a round or pilgrim calm.

## Pilgrim column

- `pilgrim_trust` 0–3 (Narrative trees already touch this).
- Column is a **moving hub prop**: mouths to feed, witnesses, soft cover.
- If trust hits 0 after ambush/parish neglect → column scatters; road maps spawn extra hostile checks; Act I ferry starts stressed.
- Protect action: Sergeant Hold / Convers Brace during ambush raises trust; ignoring Mairia’s ask lowers it.

## Mold choice (systems hook)

`mold_fate`: `given_viscount` | `drowned` | `kept`
- given → safer road short-term, viscount debt later
- drowned → no proof, cleaner conscience, harder naming in Act III
- kept → inventory `seal_mold`; risk of search; enables Clerk forge-proof at Narbonne

## Art — formation footprints

Collision / click targets (orbit cam):
- **Characters:** capsule ~0.6 m **diameter**, ~1.7–1.8 m tall — **tight** shells (do not oversize the person mesh; alley two-abreast must fit). Props may use ~1.2× mesh vs collision later; characters stay lean.
- **Props players brace/cut:** interact volume can be **~1.2× mesh** (ferry rope, wagon latch) so RMB/E is forgiving.
- **Blocking walls / porch / ferry edge:** tight to visible mesh so shove-into-water and doorway Hold read correctly.
- Party silhouette spacing: ~0.9 m center-to-center in formation so five read as a squad, not a blob.

## Engineering touch (retarget)

- Retire Blot-Wraith / Unmake Line / MP fantasy UI.
- Party data = five jobs above; dialogue face default Clerk.
- Wire Narrative effects: `chest_carrier`, `seal_intact`, `pilgrim_trust`, `mold_fate`, plus `party_is_forger`, `bleeding`/`out_for_act`.
- Keep: click-move, wall-slide, orbit cam, RMB interact.

## Acceptance (Act I slice)

- Ambush plays as formation jobs, not one Attack button for the whole party.
- Guide loft/bolt or Point→Clerk Call out is a visible alternate line.
- Breaking the true seal is possible and permanently worsens a later beat.
- Pilgrim trust can be lost and the ferry feels it.
- Surgeon Stabilize is the only “heal,” and it costs a turn / between-scene time (always available so the surgeon turn cannot softlock).

---

## Act II–III combat (addendum)

Same job verbs as Act I. New encounters:

| Id | Pattern | Win |
|---|---|---|
| `hold_door` | Ferry-like: Sergeant **Hold** on nave door; Convers sheep-gate / Kick latch; Guide Bolt if loft | Hold sustained N pulses (RTwP: ~6–8s live with Hold up) **or** rounds mode: Hold on Sergeant’s action for 2 full enemy phases while Convers opens gate → then `priory_yard` or flee |
| `priory_yard` | 2–3 foes; talk-fail / steal-caught | Rout (kill/waver) **or** transition from successful hold_door |
| `priory_loft` | `smoke_loft`; optional Guide loft; 1 crossbow | Survive timer / cut loft rope barrier (Convers); Bolt pressure from loft |

Flags: `priory_path` steal|talk|hold_door; carry Act I mold/seal/trust into Hugues / Serena / Act III. No new magic.
