# Act III gate — softlock fix (Serena not required)

## Problem
Act III river currently waits on Serena. Players who finish Hugues and skip/miss her can’t open Act III without backtracking luck.

## Fix (no new flags)

Unlock Act III river when **any** of:
1. `talked_serena` (existing — learn or withhold), OR
2. `talked_hugues` && `captain_deal` set (any of vines_spared | vines_seized | bribed_off), OR
3. `priory_path` set && priory fight resolved (`act2_beat` in aftermath/fight-done — use whatever Eng already sets post-fight)

Prefer (1), else (2), else (3).

## Once-toast when opening without Serena
- Via Hugues only: Catalana — “No widow’s name. Hill house may be ash. Wood still waits.”
- Via fight-only: Guillem — “Captain’s still talking or he’s not. We don’t need her to end the wood.”

## Serena still available
If they return later, her tree runs as now; `lord_name` can still populate before lord NPC. If Act III already past river, don’t softlock her — just `after` node.

## Journal
If Act III opens without Serena, use 08’s “Cold ash” body (no `lord_name`) until she is spoken to.
