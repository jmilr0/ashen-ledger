# Acts II–III — bible + drop-ready trees

Party: Catalana (Guide), Sergeant Guillem, Brother Peire (Convers), Arnau the Clerk, Master Elias (Surgeon).
No magic. Dirt, wax, mail.

Carry-in from Act I (read these flags):
`chest_carrier`, `seal_intact`, `party_is_forger`, `pilgrim_trust`, `mold_fate`, `child_burial`, `narbonne_outcome`

---

## Act II spine — Corbières priory

1. **Hill road / sheep-gate** — enter the ruin; northern captain’s pickets already smelling vineyards.
2. **Yard crowd** — “poor apostles” + locals; splinter (or a second splinter) on a false altar.
3. **Hard fork** — steal the chest / talk the crowd apart / hold the nave door while people run the sheep-gate.
4. **Loft collapse / bolt in the dark** — formation fight; Guide loft optional; smoke flag.
5. **Aftermath** — northern captain bargain; splinter fate seed for Act III.

### Locations (Art)
- Ruined priory nave (real stone, false altar, no glow)
- Yard with mud and rope barrier
- Collapsing loft (Guide Bolt perch)
- Sheep-gate exit
- Northern captain pavilion (dull mail, not parade plate)

### NPCs
| Id | Name | Role |
|---|---|---|
| captain_hugues | Captain Hugues | Northern captain; wants the ruin as a warrant to seize vines |
| apostle_berna | Berna | Crowd preacher with the box / splinter show |
| loft_scout | (ambient) | Optional Guide Point target before fight |
| vine_widow | Na Serena | Local who knows which lord paid for the show |

### Act II flags
- `act2_beat`: road | yard | fork | fight | aftermath
- `priory_path`: steal | talk | hold_door
- `splinter_status`: false_altar | stolen | second_copy | burned_seed
- `captain_deal`: none | vines_spared | vines_seized | bribed_off
- `smoke_loft`: bool
- `talked_berna`, `talked_hugues`, `talked_serena`

### Objective strings
| Beat | storyBeat |
|---|---|
| enter | Corbières priory. Splinter on a false altar — northern captain wants the ruin as a warrant. |
| after_fork_steal | Chest taken quiet. Get out the sheep-gate before the loft notices. |
| after_fork_talk | Crowd thinning. Hold the yard or let Hugues claim the stones. |
| after_fork_hold | Nave door held. Column / locals through the sheep-gate — then the loft. |
| after_fight | Priory settled. Speak Hugues or ride — Act III still needs names and the splinter’s end. |

---

## `berna` — yard preacher (crowd)

```ts
berna: [
  {
    id: 'start',
    speaker: 'Berna',
    text: 'Rome’s wax is soft. This wood walked from a saint’s hand. Kneel and the vines keep their water. Stand aside and the northern host calls you a magazine.',
    choices: [
      { text: '[Clerk] That seal’s rim name is dead. Your bull is a month wrong.', next: 'call_seal' },
      { text: '[Guide] Half these faces are hired. The other half are hungry.', next: 'crowd_read' },
      { text: 'We only came to see the box.', next: 'see_box' },
    ],
  },
  {
    id: 'call_seal',
    speaker: 'Berna',
    text: 'A clerk’s tongue. The square hears wood, not Latin. Prove it without a riot or step back.',
    choices: [
      { text: 'Talk them apart — no blades in the yard.', next: 'fork', effect: 'priory_path_talk' },
      { text: 'We take the chest when your backs turn.', next: 'fork', effect: 'priory_path_steal' },
    ],
  },
  {
    id: 'crowd_read',
    speaker: 'Berna',
    text: 'Hungry men still kneel. Hungry men also run if the loft catches fire.',
    choices: [
      { text: 'Hold the nave door. Get people out the sheep-gate.', next: 'fork', effect: 'priory_path_hold' },
      { text: 'Talk first. Steel second.', next: 'fork', effect: 'priory_path_talk' },
    ],
  },
  {
    id: 'see_box',
    speaker: 'Berna',
    text: 'Look. Don’t touch. Touching is for the apostles.',
    choices: [
      { text: '[Convers] Latch is soft. We can lift it in the smoke.', next: 'fork', effect: 'priory_path_steal' },
      { text: 'Enough looking.', next: 'fork', effect: 'priory_path_talk' },
    ],
  },
  {
    id: 'fork',
    speaker: 'Berna',
    text: 'Choose, then. The captain’s pickets are already counting vine rows.',
    choices: [{ text: '(Commit the path)', effect: 'end_priory_fork' }],
  },
]
```

Effects:
- `priory_path_steal|talk|hold` → set `priory_path`, `talked_berna=true`
- `end_priory_fork` → set storyBeat per path; unlock fight trigger NPC or auto-start after short move

Path → fight setup (for Design/Eng):
- **steal**: ambush when exiting sheep-gate (2 pickets); smoke optional if Convers braces latch
- **talk**: if Clerk called seal + pilgrim_trust≥2, skip fight → `hugues` talk; else yard scuffle (1–2 foes)
- **hold_door**: ferry-like win — Sergeant Hold door N rounds while Convers opens sheep-gate / Guide Bolt loft; then `start_priory_fight`

---

## `hugues` — northern captain

```ts
hugues: [
  {
    id: 'start',
    speaker: 'Captain Hugues',
    text: 'This ruin is a warrant. Heretics in the nave, vines unpaid, my men fed. Hand me a reason not to burn the sheep-gate behind you.',
    choices: [
      { text: '[Clerk] The bull is forged. Hang the goldsmith’s die, not the village.', next: 'forge_proof' },
      { text: '[Sergeant] You want a clean excuse. A massacre makes a dirty one.', next: 'clean_excuse' },
      { text: 'Take the stones. Leave the people the path.', effect: 'captain_vines_seized' },
    ],
  },
  {
    id: 'forge_proof',
    speaker: 'Captain Hugues',
    text: 'Show me lead that matches, or a mold, or a name. Paper without teeth is weather.',
    choices: [
      { text: 'We kept the mold. Match it.', next: 'mold_show', effect: 'need_mold_kept' },
      { text: 'Mold’s in the Aude. You’ll have to trust a clerk’s eye.', next: 'no_mold' },
      { text: 'Viscount has the mold. Ride his leash.', next: 'viscount_leash' },
    ],
  },
  {
    id: 'mold_show',
    speaker: 'Captain Hugues',
    text: '…Die fits the false rim. Fine. I spare the yard. I still take the priory stones for the host.',
    choices: [{ text: 'Stones, not blood.', effect: 'captain_vines_spared' }],
  },
  {
    id: 'no_mold',
    speaker: 'Captain Hugues',
    text: 'Trust is expensive. Coin or a hostage night, or I count vines my way.',
    choices: [
      { text: 'Pay him off. Column stays fed.', effect: 'captain_bribed_off' },
      { text: 'No deal. We hold what we hold.', effect: 'captain_vines_seized' },
    ],
  },
  {
    id: 'viscount_leash',
    speaker: 'Captain Hugues',
    text: 'Then the viscount and I will speak. You bought a soft rider a louder friend.',
    choices: [{ text: '(Leave him to it)', effect: 'captain_vines_spared' }],
  },
  {
    id: 'clean_excuse',
    speaker: 'Captain Hugues',
    text: 'Guillem talks like a man who has starved a castle. Very well — door held, people gone, I claim empty stone.',
    choices: [{ text: 'Empty stone. We’re done here.', effect: 'captain_vines_spared' }],
  },
]
```

Gate `need_mold_kept`: if `mold_fate!=='kept'`, divert to `no_mold` (Eng can swap start line).

---

## `serena` — vine widow (names seed)

```ts
serena: [
  {
    id: 'start',
    speaker: 'Na Serena',
    text: 'My husband sold wine to whoever paid for that lead die. The lord who signed the purse sits warm in a hill house. Name him in Narbonne and he hangs. Stay quiet and he hides you once.',
    choices: [
      { text: 'Give the name. Act III will need it.', effect: 'learn_lord_name' },
      { text: 'Keep it. We may need a roof more than a hanging.', effect: 'lord_name_withheld' },
    ],
  },
]
```

`learn_lord_name` → `lord_name=Raimon of Quéribus` (string flag), inventory note `hill_lord_name`
`lord_name_withheld` → `lord_name_known=false` (can still unlock leper-house roof in Act III)

---

## Act III spine — names, letter end-state, splinter

Act I already touched Narbonne. Act III is the **closing pass**:

1. **River watch / leper house night** — optional roof if Serena withheld or trust high.
2. **Lord Raimon’s hall** (or rumor if unnamed) — hide vs hang tension.
3. **Splinter judgment** — altar return vs public break as pine.
4. **Closing journal** — you do not win the war; you move pilgrims, name the forgery, choose the wood’s end.

### Act III flags
- `act3_beat`: river | leper | lord | splinter | close
- `lord_fate`: hidden | named_hanged | unnamed_fled
- `splinter_end`: altar | broken_public | kept_bag
- `act3_done`: bool

### Objective strings
| Beat | storyBeat |
|---|---|
| open | Act III. Names, then the splinter — altar or pine in the square. |
| after_lord | Lord settled. Decide the wood before the road closes. |
| close | Campaign frame closed. War continues. Your five still walk. |

---

## `leper_house` — night roof

```ts
leper_house: [
  {
    id: 'start',
    speaker: 'Infirmarian',
    text: 'Bells don’t ring here either. You can sleep if you don’t bring captains to the door. The Surgeon works; the rest keep quiet.',
    choices: [
      { text: '[Surgeon] Boil linen. We stay till dawn.', effect: 'rest_leper', next: 'dawn' },
      { text: 'We move before dawn.', effect: 'end' },
    ],
  },
  {
    id: 'dawn',
    speaker: 'Infirmarian',
    text: 'Road’s wet. Someone watched the gate from the willows. Not pilgrims.',
    choices: [{ text: 'Noted.', effect: 'end_leper' }],
  },
]
```

`rest_leper` → clear minor `bleeding` on living party (Design: between-scene heal); set `act3_beat=lord`

---

## `lord_raimon` — hill house (only if `lord_name` set)

```ts
lord_raimon: [
  {
    id: 'start',
    speaker: 'Raimon of Quéribus',
    text: 'You have my name. That is already a rope. I hid a courier once. I can hide five — if the splinter does not walk through my market.',
    choices: [
      { text: 'Hide us. We never write your name.', effect: 'lord_hidden' },
      { text: 'We already sent your name toward Narbonne.', effect: 'lord_named_hanged' },
      { text: 'Walk away. No hide, no hanging from us.', effect: 'lord_unnamed_fled' },
    ],
  },
]
```

If `lord_name` unset, use stub toast NPC `lord_rumor`: “Hill house empty. Someone rode north before you.”

---

## `splinter_judgment` — closing choice

```ts
splinter_judgment: [
  {
    id: 'start',
    speaker: 'Arnau the Clerk',
    text: 'Wood or politics. Put it back on an altar and someone else will kneel. Break it in the square as pine and the crowd learns what wax was worth. Keep it and you become the next chest.',
    choices: [
      { text: 'Return it to a quiet altar. No market walk.', effect: 'splinter_altar' },
      { text: 'Break it public. Call it pine.', effect: 'splinter_broken_public' },
      { text: 'Keep it in the bag. We are not done with roads.', effect: 'splinter_kept_bag' },
    ],
  },
  {
    id: 'close',
    speaker: 'Sergeant Guillem',
    text: 'War’s still south and north. We named what we could. Formation — we walk.',
    choices: [{ text: '(End campaign frame)', effect: 'end_act3' }],
  },
]
```

After any splinter effect → auto-advance to `close` node (or separate `end_act3`).

Closing storyBeat by splinter_end:
- altar: “Splinter quiet on stone. Forgery named where it would take. The war goes on.”
- broken_public: “Pine in the square. Crowds will remember the sound. The war goes on.”
- kept_bag: “Wood still in the bag. So does the risk. The war goes on.”

---

## Combat encounters (Act II) — for Design

| Id | Setup | Win |
|---|---|---|
| `priory_yard` | 2–3 foes if talk fails / steal caught | Rout or door Hold timer |
| `priory_loft` | smoke_loft; Guide Bolt from loft; 1 crossbow | Survive N rounds / cut rope barrier |

Retire any fantasy leftover copy. Job actions same as Act I.
