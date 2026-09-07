# The Broken Seal — Narrative bible (Act I)

## Canon locks
- Winter 1208 → spring 1210. Occitania. Dirt, wax, mail, bad roads.
- No spells, no glowing artifacts, no holy damage. Knowledge and seals do the work magic used to do.
- Fixed squad of five: Clerk, Sergeant, Convers, Guide, Surgeon. Speak as jobs, not fantasy classes.
- Merrowgate / Ashen Ledger / blot-wraiths are retired for this build.

## Plot items (Act I)
| Item | Truth | Player risk |
|---|---|---|
| Relic chest (Fontfroide) | Holds splinter + near-true lead seal + council letter | Opening / breaking the real seal makes *you* the next forger |
| Splinter | Sold as saint’s staff; likely pine or stolen timber | Walked through markets = political battery, not a miracle |
| Lead seal | Almost matches a living pope — wrong month / die / rim name | Good enough to fool a crowd, not a careful clerk |
| True sealed letter | Must reach Narbonne agent before roads close | Peek = break trust; lose it = act fails soft |

## Act I spine — Fontfroide → Narbonne
1. **Fontfroide cloister yard** — receive the chest; brief from the cellarer; choose who carries the seal-bag.
2. **Pilgrim column on the wet road** — walk with westbound pilgrims; bandits in borrowed badges.
3. **Parish of the unburied child** — bells thin / burial locked under interdict weather; pressure, not a sermon.
4. **Goldsmith’s house by the Aude** — body already in the river; mold under the floorboards.
5. **Hard choice: the mold** — give it to the viscount’s man, or drown it.
6. **Ferry / river watch** — get column + letter toward Narbonne gate.

## Locations for Art (Act I kit)
- Cloister yard: wet limestone, oak wagon, waxed linen cover on the chest
- Mile of mud road + mile marker
- Ferry rope / flat boat
- Goldsmith stall (floorboards, cold forge, mold cavity)
- Parish porch with locked burial ground gate
- One party silhouette (five figures, dull mail / staff / club / satchel)

## Named NPCs (Act I)
| Id | Name | Role |
|---|---|---|
| cellarer | Brother Guiraut | Fontfroide cellarer who hands you the chest |
| pilgrim_mairia | Mairia of Quillan | Column speaker; mouths to feed |
| bandit_captain | “Sergeant” of the badges | Bandit wearing borrowed Hospitaller marks |
| priest_ramon | Father Ramon | Parish priest who will not bury the child |
| mold_choice | Viscount’s rider | Wants the goldsmith’s mold |
| ferryman | Ferryman Peire | River crossing; later side-road hook |

## Flags Engineering should mirror
- `chest_carrier`: clerk | sergeant | convers
- `seal_intact`: boolean (breaking to peek sets false + `party_is_forger`)
- `pilgrim_trust`: 0–3
- `mold_fate`: given_viscount | drowned | kept
- `child_burial`: helped | refused | deferred
- `act1_beat`: fontfroide | road | parish | goldsmith | mold | ferry | narbonne_gate

## Act I closer (added)
- After ferry: **Narbonne agent** — delivery branches on `seal_intact` / `party_is_forger`, `mold_fate`, `pilgrim_trust`.
- Parish beat (Father Ramon) sits between ambush and mold; see `03-parish-narbonne.md`.
