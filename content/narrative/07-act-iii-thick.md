# Act III — thickened drop (leper / lord / splinter)

Wire after Serena resolves (`learn_lord_name` | `lord_name_withheld`).
Suggested zone: reuse Act I road west of ferry, or small `act3` strip off `road_back_narbonne`.

New NPCs:
| Id | dialogueId | Hint |
|---|---|---|
| river_watch | river_watch | Willow watch / river path |
| leper | leper_house | Infirmary roof |
| lord | lord_raimon | Hill house (gate on `lord_name`) |
| lord_empty | lord_rumor | Empty hill house if no name |
| splinter | splinter_judgment | Closing wood choice |

Flags already in data: `act3_beat`, `lord_fate`, `splinter_end`, `act3_done`, plus carry-ins.

Journal titles (for Eng journal map):
- `act3_open` → “Act III — names and wood”
- `rest_leper` → “Night under unringing bells”
- `lord_*` → matching fate line
- `splinter_*` → matching end line
- `end_act3` → “Frame closed — war continues”

---

## Gate / storyBeat on Act III open

When Serena finishes OR player hits road_back after `talked_hugues`:
`act3_beat = 'river'`
storyBeat: `Act III. Names, then the splinter — altar or pine in the square.`

---

## `river_watch`

```ts
river_watch: [
  {
    id: 'start',
    speaker: 'Catalana',
    text: 'Willows again. Same watch eyes as the infirmarian will name at dawn — if we sleep there. Captains don’t like leper doors.',
    choices: [
      { text: 'Take the infirmary roof.', next: 'to_leper', effect: 'act3_to_leper' },
      { text: '[Sergeant] Push for the hill house tonight.', next: 'to_lord', effect: 'act3_to_lord' },
      { text: 'Skip roofs. Straight to the wood’s end.', effect: 'act3_to_splinter' },
    ],
  },
  {
    id: 'to_leper',
    speaker: 'Sergeant Guillem',
    text: 'Quiet approach. Elias works; the rest don’t sing.',
    choices: [{ text: '(Go)', effect: 'end' }],
  },
  {
    id: 'to_lord',
    speaker: 'Arnau the Clerk',
    text: 'If we have Raimon’s name, the rope is already on the table. If we don’t, the house may be empty.',
    choices: [{ text: '(Go)', effect: 'end' }],
  },
]
```

Effects: set `act3_beat` to `leper` | `lord` | `splinter` (and optionally reveal matching NPC).

---

## `leper_house` (thick)

```ts
leper_house: [
  {
    id: 'start',
    speaker: 'Infirmarian',
    text: 'Bells don’t ring here either. You can sleep if you don’t bring captains to the door. The Surgeon works; the rest keep quiet.',
    choices: [
      { text: '[Surgeon] Boil linen. We stay till dawn.', next: 'work' },
      { text: '[Clerk] Any courier hide here since the ferry fights?', next: 'courier' },
      { text: 'We move before dawn.', effect: 'skip_leper' },
    ],
  },
  {
    id: 'courier',
    speaker: 'Infirmarian',
    text: 'One hooded man left wax scrap in the ash. Not papal — household. Hill-road grit on the boot mud.',
    choices: [
      { text: 'That tracks to Quéribus.', next: 'work', effect: 'hint_lord_road' },
      { text: 'Burn the scrap. We sleep.', next: 'work' },
    ],
  },
  {
    id: 'work',
    speaker: 'Master Elias',
    text: 'Hold still who can. Time and linen — not miracles. Anyone still bleeding loses the next spear stand.',
    choices: [{ text: 'Dawn, then.', next: 'dawn', effect: 'rest_leper' }],
  },
  {
    id: 'dawn',
    speaker: 'Infirmarian',
    text: 'Road’s wet. Someone watched the gate from the willows. Not pilgrims. If you owe a hill lord silence, spend it carefully.',
    choices: [
      { text: 'Hill house next.', effect: 'end_leper_to_lord' },
      { text: 'We’ve had enough roofs. The splinter.', effect: 'end_leper_to_splinter' },
    ],
  },
  {
    id: 'after',
    speaker: 'Infirmarian',
    text: 'Door stays shut. Don’t bring iron back.',
    choices: [{ text: '(Leave)', effect: 'end' }],
  },
]
```

Wiring:
- `rest_leper` → clear `bleeding` on living party; toast bark from 05; `talked_leper=true`
- `skip_leper` → `act3_beat=lord` or splinter without heal
- `hint_lord_road` → optional journal; if `lord_name` empty, still allow `lord_rumor` with warmer text
- `end_leper_to_lord` → `act3_beat=lord`
- `end_leper_to_splinter` → `act3_beat=splinter`

Branch flavor if `child_burial==='helped'`: add choice on start:
`{ text: 'We buried a child without bells already.', next: 'work' }`
Infirmarian reply node optional — keep thin if space.

If `party_is_forger`: Infirmarian start append internally (Eng can swap text):
“You smell of broken wax. Sleep anyway — sickness doesn’t read seals.”

---

## `lord_raimon` (thick) — only if `lord_name` set (e.g. Raimon of Quéribus)

```ts
lord_raimon: [
  {
    id: 'start',
    speaker: 'Raimon of Quéribus',
    text: 'You have my name. That is already a rope. I hid a courier once. I can hide five — if the splinter does not walk through my market.',
    choices: [
      { text: 'Hide us. We never write your name into any letter.', next: 'hide' },
      { text: 'We already sent your name toward Narbonne.', next: 'named' },
      { text: '[Clerk] Walk away. No hide, no hanging from our hand.', next: 'walk' },
      { text: '[Sergeant] Pay in grain for the column. Silence costs food.', next: 'grain' },
    ],
  },
  {
    id: 'hide',
    speaker: 'Raimon of Quéribus',
    text: 'Cellar until the host’s dust settles. If Berna’s wood appears in my square, the deal burns with it.',
    choices: [
      { text: 'Splinter will not walk your market.', effect: 'lord_hidden' },
      { text: 'We can’t promise the wood’s end yet.', next: 'hide_risk' },
    ],
  },
  {
    id: 'hide_risk',
    speaker: 'Raimon of Quéribus',
    text: 'Then you get one night, not a season. Leave before Compline tomorrow.',
    choices: [{ text: 'One night.', effect: 'lord_hidden' }],
  },
  {
    id: 'named',
    speaker: 'Raimon of Quéribus',
    text: 'Then I am already dead on paper. Get out before my men decide you are the rope.',
    choices: [
      { text: 'We go.', effect: 'lord_named_hanged' },
      { text: '[Guide] Sheep-path out. Now.', effect: 'lord_named_hanged' },
    ],
  },
  {
    id: 'walk',
    speaker: 'Raimon of Quéribus',
    text: 'Clever cowardice. I ride north before someone less polite arrives.',
    choices: [{ text: '(Leave him to the road)', effect: 'lord_unnamed_fled' }],
  },
  {
    id: 'grain',
    speaker: 'Raimon of Quéribus',
    text: 'Grain for silence. Take it. If Narbonne already has my name, you’ve robbed a corpse.',
    choices: [
      { text: 'Silence and grain. We never wrote you.', effect: 'lord_hidden', /* also grant item hill_grain */ },
      { text: 'Name’s already gone. Keep your grain.', effect: 'lord_named_hanged' },
    ],
  },
  {
    id: 'after',
    speaker: 'Raimon of Quéribus',
    text: 'Door’s done with you. Mind the wood.',
    choices: [{ text: '(Leave)', effect: 'end' }],
  },
]
```

Extra gate: if `narbonne_outcome` in `delivered|letter_damaged` AND player picks hide after having learned name — Raimon can distrust:
Eng optional: if `learn_lord_name` was taken AND `talked_narbonne`, inject node `named_risk` before hide success.

Effects → set `lord_fate`, `act3_beat=splinter`, storyBeat `Lord settled. Decide the wood before the road closes.`, barks from 05.

---

## `lord_rumor` — if `lord_name` empty / withheld

```ts
lord_rumor: [
  {
    id: 'start',
    speaker: 'Empty Hill House',
    text: 'Shutters out. Ash cold. Someone rode north before you — or never meant to be found.',
    choices: [
      { text: '[Guide] Tracks toward the willows, then gone.', effect: 'lord_unnamed_fled' },
      { text: 'Nothing here. The splinter waits.', effect: 'lord_unnamed_fled' },
    ],
  },
]
```

If `hint_lord_road` from leper: swap text to
“Boot grit matches the infirmary ash. He’s ahead of you on the north track — not waiting.”

---

## `splinter_judgment` (thick)

Start line variants (Eng pick by flags):

| Condition | Opening accent |
|---|---|
| `captain_deal==vines_seized` | “Hugues already counts vines. The wood’s the last magazine left in our bag.” |
| `pilgrim_trust==0` | “No column left to shock. Break it for the empty road, or don’t.” |
| `party_is_forger` | “We’re already peekers. Keeping the wood makes us the next chest.” |
| default | Arnau line below |

```ts
splinter_judgment: [
  {
    id: 'start',
    speaker: 'Arnau the Clerk',
    text: 'Wood or politics. Put it back on an altar and someone else will kneel. Break it in the square as pine and the crowd learns what wax was worth. Keep it and you become the next chest.',
    choices: [
      { text: 'Return it to a quiet altar. No market walk.', next: 'altar' },
      { text: 'Break it public. Call it pine.', next: 'break' },
      { text: 'Keep it in the bag. We are not done with roads.', next: 'keep' },
      { text: '[Convers] Let Peire snap it here — no crowd, no altar.', next: 'break_quiet' },
    ],
  },
  {
    id: 'altar',
    speaker: 'Brother Peire',
    text: 'Quiet stone. I’ll set it where no market sees. Don’t ask which house.',
    choices: [{ text: 'Set it.', next: 'close', effect: 'splinter_altar' }],
  },
  {
    id: 'break',
    speaker: 'Catalana',
    text: 'Square’s wet enough. They’ll hear pine. Some will hate us. Some will stop kneeling at boxes.',
    choices: [{ text: 'Break it.', next: 'close', effect: 'splinter_broken_public' }],
  },
  {
    id: 'break_quiet',
    speaker: 'Brother Peire',
    text: 'No sermon. Just wood. Same truth, fewer ears.',
    choices: [{ text: 'Snap it.', next: 'close', effect: 'splinter_broken_public' }],
  },
  {
    id: 'keep',
    speaker: 'Sergeant Guillem',
    text: 'Then we stay the next chest. Formation stays up. I’m not dying for a secret pine.',
    choices: [{ text: 'Bag stays. We walk.', next: 'close', effect: 'splinter_kept_bag' }],
  },
  {
    id: 'close',
    speaker: 'Sergeant Guillem',
    text: 'War’s still south and north. We named what we could. Formation — we walk.',
    choices: [{ text: '(End campaign frame)', effect: 'end_act3' }],
  },
  {
    id: 'after',
    speaker: 'Sergeant Guillem',
    text: 'Frame’s closed. Keep your boots dry.',
    choices: [{ text: '(Leave)', effect: 'end' }],
  },
]
```

`end_act3` → `act3_done=true`, `act3_beat=close`, remove or keep `splinter` item per end, storyBeat:

| splinter_end | storyBeat |
|---|---|
| altar | Splinter quiet on stone. Forgery named where it would take. The war goes on. |
| broken_public | Pine in the square. Crowds will remember the sound. The war goes on. |
| kept_bag | Wood still in the bag. So does the risk. The war goes on. |

If `lord_fate==hidden` && `splinter_broken_public`: toast — Raimon still safe; market never saw the show.
If `lord_fate==hidden` && `splinter_kept_bag`: toast — “Hill silence and a bagged relic. Someone will notice.”

---

## Suggested map order
1. Reveal `river_watch` after Serena / Hugues done.
2. Leper optional.
3. Lord or rumor.
4. Splinter always last; block with toast if `act3_beat` not past lord/rumor unless player chose `act3_to_splinter` at river.

## Companion barks
Reuse `05-companion-barks.md` Act III rows; add:
| Trigger | Speaker | Line |
|---|---|---|
| `hint_lord_road` | guide | “Hill grit. He’s ahead, not waiting.” |
| `skip_leper` | surgeon | “Then the bleeds stay. Don’t ask me for miracles on the march.” |
| `break_quiet` | convers | “No crowd. Just pine.” |
