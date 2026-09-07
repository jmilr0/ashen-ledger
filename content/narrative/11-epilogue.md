# Ending / epilogue (after `end_act3`)

Show as a short scroll or multi-card epilogue → return to title / Continue disabled.
Tone: dirt and consequence. You do not win the war.

## Structure
1. **Splinter card** (required) — from `splinter_end`
2. **Names card** (required) — from `lord_fate` + `narbonne_outcome` / mold
3. **Road card** (required) — from `pilgrim_trust` + `child_burial` + `captain_deal`
4. **Party card** (optional one-liner) — who is `out_for_act` / forger
5. **Close line** (always)

---

## 1 — Splinter

| `splinter_end` | Title | Body |
|---|---|---|
| `altar` | Quiet stone | The wood sits where no market sees it. Someone may still kneel — but not because your bag walked the square. |
| `broken_public` | Pine in the square | They heard it snap. Some cursed you. Some stopped trusting boxes for a week. That is as much truth as a road gets. |
| `kept_bag` | Still in the bag | The splinter travels with you. So does every captain who can smell wax. You chose to remain a chest. |

If quiet snap used Convers path, append: “Peire broke it without a sermon.”

---

## 2 — Names

Pick first matching row:

| Condition | Title | Body |
|---|---|---|
| `lord_fate==hidden` | A silence owed | Raimon of Quéribus keeps his hill — and you keep your mouths shut. Hide is a debt; debts walk both ways. |
| `lord_fate==named_hanged` | Rope on paper | The name reached ears that hang. The hill house empties. You sleep colder and call it justice or necessity. |
| `lord_fate==unnamed_fled` | Cold ash | No name held. Tracks north, then nothing. The die’s payer dissolves into weather. |
| else + `mold_fate==kept` && delivered letter | Die on the table | The mold matched enough. Narbonne has teeth; whose neck it closes on is no longer only yours. |
| else + `mold_fate==drowned` | Lead in the Aude | The die is cold river-metal. Cleaner conscience. Fewer proofs. |
| else + `mold_fate==given_viscount` | Soft rider | The viscount holds the mold. You bought a friend who collects. |
| `party_is_forger` \|\| !`seal_intact` | Broken wax | Gates remember peekers. Your letter arrived stained, or not at all — either way, clerks will sniff you twice. |

---

## 3 — Road

Compose 2–3 sentences from bits (join with spaces):

**Pilgrims**
- trust ≥2: “Mairia’s column ate your mud and lived.”
- trust ==1: “The column thinned but still walked west.”
- trust ==0: “You chose the bag over the mule. The road behind you is hostile mouths.”

**Parish**
- helped: “A child went into quiet earth without bells.”
- refused: “A porch still talks about dry hands.”
- deferred: “A shovel was promised and not finished.”
- unset: omit

**Hugues**
- vines_spared: “Hugues took empty stone, not a massacre warrant.”
- vines_seized: “Vines will feed northern horses. You bought time, not mercy.”
- bribed_off: “Coin bought a quieter captain for a while.”
- unset: omit

Title: `The road`

---

## 4 — Party (omit if all healthy and seal intact)

| Condition | Line |
|---|---|
| any `out_for_act` | “Not all five walk out whole. Elias’s linen has limits.” |
| `party_is_forger` | “Arnau’s fingers still smell of broken wax.” |
| `chest_carrier==convers` && act3_done | “Peire carried keys and a bag and did not drop either.” |
| default omit | — |

Title: `Five jobs`

---

## 5 — Close (always)

> Winter does not end because five people named a forgery. Northern banners still move. Local counts still play for time. You move pilgrims off one killing ground, put a die out of easy reach, and decide what a stick of wood was worth.
>
> The war goes on. Your boots are still wet.

Button: `Return to title`

---

## Controls help (flavor blurb for Eng help overlay)

Keep mechanical list Design/Eng-owned. Optional flavor header:

**The Broken Seal** — Five jobs. No miracles. Seals, pilgrims, and a road that remembers.

Short tips Eng can foot:
- “Rest is Elias and linen — once per beat, not a spell.”
- “Hold then Cut. Don’t sprint the rope.”
- “Journal (J) lies; the road doesn’t.”
