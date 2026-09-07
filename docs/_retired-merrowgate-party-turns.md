# RETIRED — Merrowgate / Blot-Wraith. See broken-seal-systems-act-i.md
# Spec: Party turns (Blot-Wraith combat)

**Owner:** Game Design  
**For:** Engineering  
**Slice:** Vertical slice only — one fight, two allies max  
**Out of scope:** MP costs, Canal Salve in combat, debt-stance fight mutation, positions/tiles, multi-enemy targeting

## Goal

Combat should feel like a party fight, not a single-attacker menu. Living allies each take an action in order, then the enemy acts once.

## Round order

1. **Ally phase (fixed party order):** for each living ally in order `rowan` → `mirelle`, run one player action for that ally.
2. **Enemy phase:** living Blot-Wraith acts once.
3. Repeat until victory (no living enemies) or defeat (no living allies).

Skip dead allies. If an ally dies mid-round (future effects), skip them when their slot would come up. If all allies die during enemy phase, end immediately.

## Active actor

Track `activeAllyId` (party member id) while `turn === 'player'`.

- Start of combat / start of ally phase: set to first living ally in order.
- After that ally finishes an action: advance to next living ally in order.
- After last living ally acts: set `turn = 'enemy'`, run enemy phase, then if fight continues set `turn = 'player'` and `activeAllyId` to first living ally again.

UI must show whose turn it is (name + “your move”).

## Actions (per active ally)

| Action | Who | Behavior |
|--------|-----|----------|
| **Attack** | Any | Damage = `max(1, atk - def + floor(rand*3))` vs Blot-Wraith. Log: `{name} strikes for {d}.` |
| **Defend** | Any | Set `defending = true` on that combatant (+2 def while true). Log: `{name} braces.` Clear `defending` at the **start of that same ally’s next action** (so it covers the rest of this round’s ally actions + this enemy phase). |
| **Unmake Line** | **Mirelle only** | Same formula with `atk + 3`. Log: `{name} unmakes a ledger-line — {d} damage…`. Hide/disable this button when active ally is not Mirelle. |

Do **not** let Rowan cast Unmake Line. Do **not** auto-pick Mirelle when someone else is active.

## Enemy phase

- One action from the living Wraith.
- Target: random living ally (equal weight). Log names both attacker and target.
- Apply damage with current def (including Defend bonus if still active).
- Then return to ally phase if anyone lives.

## UI (combat panel)

Minimum:

1. Enemy chip(s) with HP (unchanged).
2. Ally chips: name, HP, highlight active, show “Bracing” if defending.
3. Log (last ~4 lines).
4. Buttons: Attack, Defend, Unmake Line (Mirelle-only), Continue when over.

Disable actions when `turn !== 'player'` or fight over. After each action, redraw so the next ally’s highlight/buttons update before the next click.

## Touch points (current code)

- `src/game/combat.ts` — `CombatSession`: replace single `turn: 'player'|'enemy'` flow that always uses `living('allies')[0]` with active-ally queue + Defend flag lifetime as above. `playerAttack` / `playerSkill` / `playerDefend` should operate on **active** ally, then advance.
- `src/game/Game.ts` — `drawCombat`: show active name; gate Unmake Line; keep Attack wired to wraith id for now.
- `src/game/types.ts` — optional: `defending?: boolean` on `Combatant`.

## Acceptance

- With Mirelle recruited, a full round is: Rowan action → Mirelle action → Wraith action → repeat.
- If Mirelle is dead/down, rounds are Rowan → Wraith only.
- Unmake Line never appears on Rowan’s turn.
- Defend on Rowan reduces Wraith damage to Rowan that same round; bonus is gone when Rowan acts again.
- Victory/defeat and post-fight spoils (`debtStance` loot) unchanged.
- No new systems beyond turn ownership / Defend timing / Mirelle-gated skill.

## Feel note for QA

If it still feels like “click three buttons then wait,” the order is wrong. If you hear two distinct ally verbs before the ink lash, the slice landed.
