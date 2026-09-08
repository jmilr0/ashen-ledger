# Interactive cast — party RMB + road NPCs (BG feel)

For Engineering after locomotion: RMB on party portraits/followers and roadside people opens talk, not scenery.
No new systems flags required beyond optional `talked_<id>` once-markers.

Party ids: `guide` Catalana · `sergeant` Guillem · `convers` Peire · `clerk` Arnau · `surgeon` Elias

---

## Party talk (repeatable; rotate `after` if re-clicked)

### `party_guide`
```ts
party_guide: [
  {
    id: 'start',
    speaker: 'Catalana',
    text: 'Draille’s soft after rain. Badges like borrowed stamps, houses that still take strangers, loft angles — ask before you charge the nave.',
    choices: [
      { text: 'Any cut off the road?', next: 'cut' },
      { text: 'What do you make of the column?', next: 'column' },
      { text: '(Leave her to scout)', effect: 'end' },
    ],
  },
  {
    id: 'cut',
    speaker: 'Catalana',
    text: 'Sheep-paths behind the mile marker, and a willow ditch before the ferry. Both beat dying on the crown of the road.',
    choices: [{ text: 'Show me when it matters.', effect: 'end' }],
  },
  {
    id: 'column',
    speaker: 'Catalana',
    text: 'Hungry mouths are witnesses. Lose them and every village hears we chose a bag over a mule.',
    choices: [{ text: 'Understood.', effect: 'end' }],
  },
]
```

### `party_sergeant`
```ts
party_sergeant: [
  {
    id: 'start',
    speaker: 'Sergeant Guillem',
    text: 'Formation first. I Hold doors and ropes; you don’t sprint Cut. Watch rotations — if someone’s bleeding, Elias works before I shove another spear.',
    choices: [
      { text: 'How do you want us lined?', next: 'line' },
      { text: 'The bag.', next: 'bag' },
      { text: '(Back to the road)', effect: 'end' },
    ],
  },
  {
    id: 'line',
    speaker: 'Sergeant Guillem',
    text: 'Me front. Convers on latches. Guide loft if there’s a loft. Clerk behind my shoulder. Surgeon last — he’s not a blade.',
    choices: [{ text: 'Locked.', effect: 'end' }],
  },
  {
    id: 'bag',
    speaker: 'Sergeant Guillem',
    text: 'Whoever carries it doesn’t drop it for cleverness. Broken wax makes us the next forgers on this road.',
    choices: [{ text: 'Bag stays dry.', effect: 'end' }],
  },
]
```

### `party_convers`
```ts
party_convers: [
  {
    id: 'start',
    speaker: 'Brother Peire',
    text: 'Keys, grain, soft latches. I cut rope under Hold — not before. If you need a quiet snap of pine later, my hands are already dirty from barn work.',
    choices: [
      { text: 'Abbey life miss you?', next: 'abbey' },
      { text: 'Any lock ahead worry you?', next: 'lock' },
      { text: '(Leave him)', effect: 'end' },
    ],
  },
  {
    id: 'abbey',
    speaker: 'Brother Peire',
    text: 'Fontfroide still has oats. This road has captains. I know which one starves you slower.',
    choices: [{ text: 'Fair.', effect: 'end' }],
  },
  {
    id: 'lock',
    speaker: 'Brother Peire',
    text: 'Goldsmith floorboards, nave bars, sheep-gates — all softer than they look if nobody’s watching the hinge.',
    choices: [{ text: 'I’ll call you to the hinge.', effect: 'end' }],
  },
]
```

### `party_clerk`
```ts
party_clerk: [
  {
    id: 'start',
    speaker: 'Arnau the Clerk',
    text: 'Seals, rim names, chancery hands. I Call out lies on badges and I do not peek the true letter unless you order a sin we both own.',
    choices: [
      { text: 'Remind me what was wrong with their bull.', next: 'bull' },
      { text: 'Narbonne.', next: 'narb' },
      { text: '(Leave the ink alone)', effect: 'end' },
    ],
  },
  {
    id: 'bull',
    speaker: 'Arnau the Clerk',
    text: 'Die soft on the keys. Rim name belongs to a dead chamberlain. Crowd kneels; careful clerks spit.',
    choices: [{ text: 'Keep spitting.', effect: 'end' }],
  },
  {
    id: 'narb',
    speaker: 'Arnau the Clerk',
    text: 'Agent wants names and unbroken wax. Mold kept, drowned, or given — each writes a different rope.',
    choices: [{ text: 'We’ll choose cleanly.', effect: 'end' }],
  },
]
```
Flag swap: if `party_is_forger` / !`seal_intact`, replace start text with:
“Wax is already broken on us. Gates will smell it. Walk soft and don’t offer to Show seal in a fight.”

### `party_surgeon`
```ts
party_surgeon: [
  {
    id: 'start',
    speaker: 'Master Elias',
    text: 'I’m not a blade. Stabilize in the press; Rest between roofs — linen and time, once a beat. Prayer is weather, not a button.',
    choices: [
      { text: 'Who’s worst right now?', next: 'triage' },
      { text: 'What poisons should we fear?', next: 'poison' },
      { text: '(Let him pack linen)', effect: 'end' },
    ],
  },
  {
    id: 'triage',
    speaker: 'Master Elias',
    text: 'Whoever’s marked bleeding drops next if I don’t touch them. Out-for-act means they walk the mule, not the spear line.',
    choices: [{ text: 'I’ll call Rest at the next roof.', effect: 'end' }],
  },
  {
    id: 'poison',
    speaker: 'Master Elias',
    text: 'Well water after a host camps, and anything a goldsmith leaves in a cup. Boil what you can. Don’t kiss relics.',
    choices: [{ text: 'Noted.', effect: 'end' }],
  },
]
```

---

## Road / hub NPCs (open map densifiers)

Place along Act I contiguous road + Corbières approach. Short trees; optional `talked_*`.

### `wayside_monk`
```ts
wayside_monk: [
  {
    id: 'start',
    speaker: 'Wayside Monk',
    text: 'Cross is older than this war. I don’t bless captains. I count who still buries their dead.',
    choices: [
      { text: 'Seen borrowed badges?', next: 'badges' },
      { text: 'Any word of Fontfroide’s chest?', next: 'chest' },
      { text: '(Pass on)', effect: 'end' },
    ],
  },
  {
    id: 'badges',
    speaker: 'Wayside Monk',
    text: 'Men with Hospital marks and farmer horses. Catalana would smell them before I finished the Ave.',
    choices: [{ text: 'Obliged.', effect: 'end' }],
  },
  {
    id: 'chest',
    speaker: 'Wayside Monk',
    text: 'Abbey wax on the road is never holy for long. Keep your seal bag closed.',
    choices: [{ text: 'We intend to.', effect: 'end' }],
  },
]
```

### `cart_widow`
```ts
cart_widow: [
  {
    id: 'start',
    speaker: 'Cart Widow',
    text: 'Axle’s cracked and the host eats axles. Don’t ask me for the pilgrim road’s kindness — ask if you’ve got a Convers who can brace wood.',
    choices: [
      { text: '[Convers] I can brace it. No coin.', next: 'brace', effect: 'road_help_cart' },
      { text: 'We can’t linger.', effect: 'end' },
    ],
  },
  {
    id: 'brace',
    speaker: 'Cart Widow',
    text: 'Then the next village owes you bread, not me. Go before the badges smell a stopped cart.',
    choices: [{ text: '(Leave)', effect: 'end' }],
  },
]
```
`road_help_cart` → optional `pilgrim_trust+1` once (Design/Eng).

### `ferry_idler` (near ferry, not the fight trigger)
```ts
ferry_idler: [
  {
    id: 'start',
    speaker: 'Idle Boatman',
    text: 'Rope fight’s for men with sergeants. I just know the Aude takes whatever you drop — mold, bodies, bad seals.',
    choices: [
      { text: 'Any watch on the far latch?', next: 'watch' },
      { text: '(Leave)', effect: 'end' },
    ],
  },
  {
    id: 'watch',
    speaker: 'Idle Boatman',
    text: 'Always. Cut under Hold or swim with your letter.',
    choices: [{ text: 'We’ll Hold.', effect: 'end' }],
  },
]
```

### `vine_boy` (Corbières approach)
```ts
vine_boy: [
  {
    id: 'start',
    speaker: 'Vine Boy',
    text: 'Northern men count rows like they’re already paid. Berna’s box makes old women kneel. I just want the sheep-gate left open.',
    choices: [
      { text: 'Where’s the loft?', next: 'loft' },
      { text: 'Who paid for the show?', next: 'pay' },
      { text: '(Move on)', effect: 'end' },
    ],
  },
  {
    id: 'loft',
    speaker: 'Vine Boy',
    text: 'Above the false altar. Crossbow likes that cough of smoke.',
    choices: [{ text: 'Catalana’s problem.', effect: 'end' }],
  },
  {
    id: 'pay',
    speaker: 'Vine Boy',
    text: 'Ask Na Serena. She sold wine to the purse. I only carry baskets.',
    choices: [{ text: 'We will.', effect: 'end' }],
  },
]
```

### `leper_bell` (Act III, near infirmary — ambient, not the Rest NPC)
```ts
leper_bell: [
  {
    id: 'start',
    speaker: 'Gate Ringer',
    text: 'No parish bells. We ring wood so captains don’t pretend they didn’t see the door. Sleep if Elias is with you. Don’t bring iron inside.',
    choices: [{ text: 'Understood.', effect: 'end' }],
  },
]
```

### `market_crier` (Narbonne edge)
```ts
market_crier: [
  {
    id: 'start',
    speaker: 'Market Crier',
    text: 'Interdict weather — thin market, locked ground, rumors thicker than bread. Hooded clerks buy silence with unbroken wax.',
    choices: [
      { text: 'Seen a legate ride?', next: 'legate' },
      { text: '(Pass)', effect: 'end' },
    ],
  },
  {
    id: 'legate',
    speaker: 'Market Crier',
    text: 'North, or so the ferrymen swear. Your agent will know if the letter still matters.',
    choices: [{ text: 'We’ll ask him.', effect: 'end' }],
  },
]
```

---

## Wiring notes for Engineering
- RMB on follower mesh / portrait → `party_<jobId>` (not the bag pip).
- Road NPCs: same NPC table as Guiraut; capsules ~0.6 m; no combat flag unless specified.
- Re-talk: jump to a one-line `after` or replay `start` — either fine.
- Open-map merge: sprinkle wayside_monk + cart_widow on Act I stretch; vine_boy on Corbières road; market_crier near Narbonne; ferry_idler beside ferry (separate from ferry_rope fight).

## Optional journal crumbs
| Effect / talk | Journal |
|---|---|
| `road_help_cart` | “Braced a widow’s axle. Bread may follow.” |
| first `party_*` talk | omit (too noisy) |

---

## Placement on Act I open extents (`docs/open-map-extents-act1.md`)

Shoulders only (|x| 1.2–4 or hub pockets). Capsules ~0.6 m.

| NPC | Near hub anchor | Suggest (x, z) |
|---|---|---|
| `wayside_monk` | Mile marker / column (0, +22) | (−2.2, +24) |
| `cart_widow` | Mile marker / column | (+2.4, +20) |
| `ferry_idler` | Ferry (0, −32) — not the rope fight | (−2.5, −30) |
| `market_crier` | Narbonne gate (+5, −44) | (+3.5, −42) |
| `vine_boy` | Corbières turnoff (−4, −28) until Act II expand | (−3.2, −26) |
| `leper_bell` | Act III only (hold until that hub expands) | — |

Party RMB: no world anchor — follower mesh / portrait.
