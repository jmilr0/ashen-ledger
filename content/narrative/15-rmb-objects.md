# RMB objects — talk / loot / inspect (basic RPG)

People still use dialogue trees (13/14). Objects use short inspect + optional loot/take.
Engineering: RMB on prop → context (Inspect / Loot / Leave). No magic; dirt-and-mail only.

Suggested prop ids (match Art silhouettes when ready): `obj_chest`, `obj_crate`, `obj_herb_pouch`, plus existing story props.

---

## Shared pattern

```ts
type ObjNode = {
  id: string;
  speaker: string; // often '(Inspect)' or object name
  text: string;
  choices?: { text: string; next?: string; effect?: string }[];
};
```

Effects:
- `loot_<id>` — add item once; set `looted_<id>`
- `inspect_<id>` — optional journal crumb once
- `end` — close

If already `looted_*`, Inspect-only “empty / taken” line.

---

## Story / road objects

### `obj_fontfroide_chest` (plot — usually already given; inspect OK)
```ts
obj_fontfroide_chest: [
  {
    id: 'start',
    speaker: 'Relic Chest',
    text: 'Oak, waxed linen, lead seal on the false bull inside. The true letter rides in your bag — don’t confuse them.',
    choices: [
      { text: 'Inspect the latch.', next: 'latch' },
      { text: '(Leave)', effect: 'end' },
    ],
  },
  {
    id: 'latch',
    speaker: 'Relic Chest',
    text: 'Soft hinge. Peire could open it quiet — opening the *true* seal is still a sin you own.',
    choices: [{ text: '(Step back)', effect: 'inspect_fontfroide_chest' }],
  },
]
```

### `obj_mile_marker`
```ts
obj_mile_marker: [
  {
    id: 'start',
    speaker: 'Mile Marker',
    text: 'Wet limestone. Scrapes where badges leaned. North toward the abbey, south toward ferry mud.',
    choices: [
      { text: 'Check the base.', next: 'base' },
      { text: '(Leave)', effect: 'end' },
    ],
  },
  {
    id: 'base',
    speaker: 'Mile Marker',
    text: 'A broken strap — Hospital die wrong for the leather. Catalana was right about borrowed stamps.',
    choices: [
      { text: 'Take the strap scrap.', effect: 'loot_badge_scrap' },
      { text: 'Leave it.', effect: 'inspect_mile_marker' },
    ],
  },
]
```
`loot_badge_scrap` → item `{ id: 'badge_scrap', name: 'Torn Badge Strap', description: 'Wrong die for the leather. Proof of borrowed colors.', qty: 1 }` once.

### `obj_burial_gate`
```ts
obj_burial_gate: [
  {
    id: 'start',
    speaker: 'Burial Gate',
    text: 'Locked under interdict weather. Iron cold. The porch still remembers dry hands.',
    choices: [
      { text: 'Inspect the lock.', next: 'lock' },
      { text: '(Leave)', effect: 'end' },
    ],
  },
  {
    id: 'lock',
    speaker: 'Burial Gate',
    text: 'Parish iron, not a puzzle. Shovels matter more than picks here.',
    choices: [{ text: '(Leave)', effect: 'inspect_burial_gate' }],
  },
]
```

### `obj_mold_cavity`
```ts
obj_mold_cavity: [
  {
    id: 'start',
    speaker: 'Floor Cavity',
    text: 'Goldsmith’s under-board hollow. River-slick. The die lived here before the Aude or the viscount took it.',
    choices: [
      { text: 'Feel for scraps.', next: 'scraps' },
      { text: '(Leave)', effect: 'end' },
    ],
  },
  {
    id: 'scraps',
    speaker: 'Floor Cavity',
    text: 'Lead filings and a burnt scrap of chancery practice. Arnau can read the hand.',
    choices: [
      { text: 'Take the scrap.', effect: 'loot_chancery_scrap' },
      { text: 'Leave it.', effect: 'inspect_mold_cavity' },
    ],
  },
]
```
Item: `{ id: 'chancery_scrap', name: 'Practice Hand Scrap', description: 'Burnt drill of a papal rim. Useful at Narbonne if the mold is gone.', qty: 1 }`

### `obj_ferry_rope` (inspect only — fight stays on NPC/rope interact)
```ts
obj_ferry_rope: [
  {
    id: 'start',
    speaker: 'Ferry Rope',
    text: 'Taut hemp. Far latch watched. Cut under Sergeant Hold — not before.',
    choices: [{ text: '(Step to the crossing)', effect: 'end' }],
  },
]
```

### `obj_false_altar`
```ts
obj_false_altar: [
  {
    id: 'start',
    speaker: 'False Altar',
    text: 'Real stone under a show. Splinter groove worn by knees, not miracles.',
    choices: [
      { text: 'Search the cloth.', next: 'cloth' },
      { text: '(Leave)', effect: 'end' },
    ],
  },
  {
    id: 'cloth',
    speaker: 'False Altar',
    text: 'Copper coin and a pilgrim pin. Berna’s crowd leaves litter like faith.',
    choices: [
      { text: 'Take them.', effect: 'loot_altar_pocket' },
      { text: 'Leave them.', effect: 'inspect_false_altar' },
    ],
  },
]
```
Item stack or two small items: `pilgrim_pin`, `copper_coin`.

### `obj_splinter_plinth` (Act III close — inspect; judgment stays dialogue NPC)
```ts
obj_splinter_plinth: [
  {
    id: 'start',
    speaker: 'Stone Plinth',
    text: 'Quiet stone waiting for a decision: altar, pine in the square, or bag.',
    choices: [{ text: '(Find the judgment)', effect: 'end' }],
  },
]
```

---

## Generic densifiers (Art loot silhouettes)

### `obj_crate`
```ts
obj_crate: [
  {
    id: 'start',
    speaker: 'Road Crate',
    text: 'Wet oak. Rope handles. Smells of onions and river.',
    choices: [
      { text: 'Pry it.', next: 'pry' },
      { text: '(Leave)', effect: 'end' },
    ],
  },
  {
    id: 'pry',
    speaker: 'Road Crate',
    text: 'Dried fish and a heel of bread. Travel food, not treasure.',
    choices: [
      { text: 'Take the rations.', effect: 'loot_crate_rations' },
      { text: 'Leave it.', effect: 'end' },
    ],
  },
]
```
Item: `{ id: 'travel_rations', name: 'Travel Rations', description: 'Dried fish and bread. Keeps a column quiet for a day.', qty: 1 }`  
Once per crate instance id (`loot_crate_a`, etc.).

### `obj_herb_pouch`
```ts
obj_herb_pouch: [
  {
    id: 'start',
    speaker: 'Herb Pouch',
    text: 'Bitter greens Elias trusts more than prayers.',
    choices: [
      { text: 'Take it for the Surgeon.', effect: 'loot_herb_pouch' },
      { text: '(Leave)', effect: 'end' },
    ],
  },
]
```
Item: `{ id: 'bitter_herbs', name: 'Bitter Herbs', description: 'For linen boils and stomachs. Not a miracle.', qty: 1 }`  
Optional: if Surgeon present, toast Elias bark “Better than guessing.”

### `obj_wayside_chest` (small loot chest — not the relic)
```ts
obj_wayside_chest: [
  {
    id: 'start',
    speaker: 'Wayside Chest',
    text: 'Cheap lock. Someone’s emergency coin.',
    choices: [
      { text: '[Convers] Soft latch — open it.', next: 'open' },
      { text: 'Inspect only.', next: 'look' },
      { text: '(Leave)', effect: 'end' },
    ],
  },
  {
    id: 'look',
    speaker: 'Wayside Chest',
    text: 'Scratch marks. Opened before. Maybe still something.',
    choices: [
      { text: 'Open it.', next: 'open' },
      { text: '(Leave)', effect: 'end' },
    ],
  },
  {
    id: 'open',
    speaker: 'Wayside Chest',
    text: 'A few deniers and a blunt knife.',
    choices: [{ text: 'Take them.', effect: 'loot_wayside_chest' }],
  },
]
```

### `obj_leper_linen`
```ts
obj_leper_linen: [
  {
    id: 'start',
    speaker: 'Boiled Linen',
    text: 'Still warm. Infirmary stock — Rest uses this, not a spell.',
    choices: [
      { text: 'Take a wrap for the kit.', effect: 'loot_boiled_linen' },
      { text: '(Leave for Rest)', effect: 'end' },
    ],
  },
]
```
Adds to existing `bandages` / boiled linen qty +1 once per beat flag if you want anti-farm.

---

## People vs objects (UI copy)

| Target | RMB default |
|---|---|
| NPC / party | Talk |
| Lootable prop | Inspect (menu: Loot if available) |
| Plot interact (ferry rope fight) | Engage / Talk as now |

Help panel add one line (optional): **RMB** people to talk · objects to inspect/loot.

---

## Journal crumbs (once)
| Effect | Journal |
|---|---|
| `loot_badge_scrap` | “Torn strap at the mile marker — borrowed colors.” |
| `loot_chancery_scrap` | “Practice hand from the goldsmith’s hollow.” |
| `loot_altar_pocket` | “Altar litter — pin and copper, not holiness.” |

---

## Align with `docs/stats-equip-sheet.md` (shared consumables)

Party shared pool (not per-slot equip):
| Loot effect | Item id | Sheet bucket |
|---|---|---|
| `loot_crate_rations` | `travel_rations` | shared consumable (Use / optional Rest food later) |
| `loot_herb_pouch` | `bitter_herbs` | shared consumable (Surgeon kit flavor; Use = small heal or Rest aid) |
| `loot_boiled_linen` | `bandages` (existing boiled linen) | shared consumable — **same id as starting kit**, qty+1 |
| `loot_altar_pocket` copper | `copper_coin` | shared junk / coin (not equip) |
| `loot_wayside_chest` | `copper_coin` + optional `blunt_knife` | coin shared; knife → **hand** unique if equipped |

Quest / inspect scraps (pack flavor, not hand/body):
| Loot effect | Item id | Notes |
|---|---|---|
| `loot_badge_scrap` | `badge_scrap` | journal proof; no ATK/DEF |
| `loot_chancery_scrap` | `chancery_scrap` | journal proof for Narbonne |
| `loot_altar_pocket` pin | `pilgrim_pin` | junk / journal |

Once-flags stay `looted_<objInstance>`; consumable ids stack in shared inventory. Do **not** put salves/linen/herbs/rations into `hand`/`body` — sheet rule: unique gear in slots, consumables shared.
