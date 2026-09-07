# The Broken Seal — BG-like UX layer (Act I)

**Owner:** Game Design  
**For:** Engineering (stub UI hooks now)  
**Canon:** still no magic / no hotbar miracles. Five fixed jobs. Formation lane DNA stays — RTwP wraps it, does not replace jobs with spells.  
**Bar:** CoS asked BG-like — party switch, journal, pause-with-orders.

---

## 1) Party switch (hub)

### Model
- `controlledId: JobId` — who the player drives on the hub.
- Other recruited, not-`outForAct` companions are **followers** (formation trail behind controlled, ~0.9 m spacing).
- Default on new game: `controlledId = 'clerk'` (talks gates / seals). If Clerk is out, fall back sergeant → convers → guide → surgeon.

### Input
| Input | Action |
|---|---|
| `1`–`5` | Select guide / sergeant / convers / clerk / surgeon (skip if outForAct) |
| Click portrait (party strip) | Same |
| `Tab` | Cycle next living companion |
| `C` / `P` | Party panel (existing) — highlight controlled |

LMB move / RMB interact / orbit unchanged; they apply to **controlled** character. Followers path-follow; collision: followers soft-slide, don’t block controlled through doorways.

### Dialogue face
- Opening line speaker for *party* choices uses `controlledId` name when the tree says `[Job]`.
- Job-gated choices (parish Clerk/Surgeon/Convers lines): **enabled only if that job is in the party and not outForAct**; if the gated job isn’t controlled, still allow the choice (BG-style: you speak as the party, the job is available). Optional later: require that job selected — **not Act I**.

### Chest carrier
- `chest_carrier` is independent of `controlledId` (who holds the bag ≠ who you walk).
- HUD: small bag icon on carrier’s portrait.

### Stub hooks
- `Game.controlledId`
- `selectCompanion(id)`
- Party strip UI under HUD
- World: follower transforms (can be simple offset chain for Act I)

---

## 2) Journal (flags → readable entries)

### Open
- Key `J` (and Journal button on HUD). Overlay like party/inventory; Esc closes.
- Not a raw flag dump — **quest entries** with title, body, status.

### Data shape
```ts
type JournalStatus = 'active' | 'done' | 'failed' | 'locked';
interface JournalEntry {
  id: string;
  title: string;
  body: string;       // player-facing prose
  status: JournalStatus;
  sort: number;
}
```

### Act I catalog (derive from flags — no duplicate source of truth)

| id | Becomes active when | Title | Body seeds from | Done / failed |
|---|---|---|---|---|
| `q_chest` | always (new game) | The Fontfroide chest | carrier + seal intact/broken + forger | `talked_cellarer` + carrier set → active “on the road”; Narbonne closer → done |
| `q_pilgrims` | `chest_carrier` set | The westbound column | `pilgrim_trust` 0–3 as “scattered / uneasy / steady / loyal” | trust 0 after ambush window → failed flavor; Narbonne close → done |
| `q_ambush` | `talked_mairia` or beat road | Borrowed badges | Point/Call out hint once | `ambush_done` → done |
| `q_parish` | `ambush_done` | The locked burial | porch / interdict | `child_burial` helped/refused/deferred → done (status note per value) |
| `q_mold` | parish resolved **or** ambush_done if parish skipped | The goldsmith’s mold | viscount / drown / keep | `mold_fate` set → done |
| `q_ferry` | `mold_fate` set | The ferry rope | Hold then Cut; sheep-gate if trust≥2 | `ferry_done` → done |
| `q_letter` | always after cellarer | Letter for Narbonne | seal / forger warning | `narbonne_outcome` → done (branch text) |

`storyBeat` remains the **one-line HUD objective**; journal holds the durable quest list.

### Writing rules
- Bodies in dirt/wax voice (Narrative can rewrite strings in `content/narrative/journal-act-i.md` later).
- Engineering may ship with Design placeholder strings in `src/game/journal.ts`.
- Never show internal flag keys in UI.

### Stub hooks
- `buildJournal(flags, party): JournalEntry[]`
- Screen `'journal'`
- Toast nothing on every flag flip — only update silent; optional once: “Journal updated” when a quest status flips to done.

---

## 3) RTwP / pause on formation combat

### Intent
BG-like: **time runs** in combat until the player pauses to issue orders; formation slots and job actions stay the verbs. Not a new magic layer.

### Modes
| Mode | Behavior |
|---|---|
| `live` | Clock runs. Allies auto-idle (hold position / face foe). Enemies act on personal timers. |
| `paused` | Clock stopped. Player queues **one action** for any ally who has no pending order (or replace order). |

### Enter / exit pause
- **Space** toggles pause (BG muscle memory).
- Auto-pause when: combat starts; an ally is downed; Surgeon sees new `bleeding`; ferry rope becomes cuttable (`sergeantHeldThisRound` or `ferryWatchCleared`); badges first exposed; player opens action menu on a portrait.
- Auto-resume optional after issuing the last empty ally’s order — **Act I: stay paused until Space** (clearer).

### Orders + formation rounds → RTwP mapping

Keep job action table from `broken-seal-systems-act-i.md`.

Each living ally has:
- `order: CombatActionId | null`
- `cooldown` / `recoverUntil` (ms)

When `live`:
- If ally has an order and recover elapsed → execute `act`-equivalent for that ally only (same rules as today’s `act`), then clear order and start recover (~1.2–1.8s by job; Sergeant Hold recover shorter).
- Enemies: each living foe has recover; on fire, same targeting as today’s enemy phase (prefer front). Wavering → skip one pulse then clear.
- Bleed ticks: every ~2.5s of live time while bleeding (not per round). 2 ticks untreated → `out_for_act` as now.
- Hold / Brace: last for a **duration** (~3s live) instead of “until round end.”
- Ferry Cut: still requires Hold active **or** `ferryWatchCleared`; victory only on `ropeCut`.

**Remove** strict sergeant→…→surgeon round gate for RTwP. Simultaneous orders are the point. Round counter can hide or become “elapsed skirmish time.”

### UI
- Portraits with HP / bleed / Hold pip / queued order icon.
- Click portrait while paused → action buttons (same labels; Tend kit / Stabilize rules unchanged).
- Single primary foe target for Act I (multi-target still stubbed).
- Banner: `PAUSED — Space to resume` / `LIVE`.

### Stub hooks (ship first, wire brains second)
1. Combat panel: Space toggle, paused flag, portrait click selects actor (already have `activeAllyId` — reuse as `selectedAllyId` under pause).
2. `combat.paused: boolean` + `setOrder(job, action)`.
3. `update(dt)` only advances when `!paused && screen==='combat'`.
4. Keep a **debug fallback**: if RTwP feels broken, `flags.combat_mode = 'rounds'` restores current round UI for one fight.

### Acceptance
- Can pause, queue Point on Guide + Call out on Clerk, resume, see both resolve without round wizard.
- Ferry still teaches Hold→Cut (or wipe→Cut).
- Surgeon never softlocks (Tend kit).
- Hub party switch + Journal open without breaking save.

### Out of scope (this drop)
- Full continuum pathing in combat
- AI scripts per job beyond idle + queued order
- Multi-enemy click targeting
- Lane grid viz / loft mesh (still stubbed)

---

## Ship order for Engineering
1. Stub party strip + `controlledId` + Journal overlay (empty/buildJournal).
2. Wire journal catalog to existing flags.
3. Combat: pause toggle + selected ally + `update(dt)` gate; then migrate execute path from rounds → orders.

Ping Game Design for a feel pass when (1)+(3) pause stub is clickable even if AI is dumb.
