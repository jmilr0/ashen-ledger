# Act I dialogue trees (drop-ready)

Format matches `DialogueNode` / `DialogueChoice` in `src/game/types.ts`.
Effects are narrative flags for Engineering to wire; rename freely.

Speaker for party lines can be the active face (default **Clerk**) unless noted.

---

## `cellarer` — Fontfroide yard

```ts
cellarer: [
  {
    id: 'start',
    speaker: 'Brother Guiraut',
    text: 'Chest came after Compline. Lead seal, splinter sold as a saint’s staff, and a letter calling poor apostles to a ruined priory in the Corbières. The seal is wrong — not loudly. Wrong by a month and a name that should not sit on the rim.',
    choices: [
      { text: 'Show me the fault in the seal.', next: 'seal_fault' },
      { text: 'Who paid for the wood and the lead?', next: 'who_paid' },
      { text: 'We ride. Who carries the bag?', next: 'carrier' },
    ],
  },
  {
    id: 'seal_fault',
    speaker: 'Brother Guiraut',
    text: 'Die-cut is a hair soft on the keys. Rim name belongs to a dead chamberlain. A crowd will kneel. A careful clerk will spit.',
    choices: [
      { text: 'Then we do not break the true letter to peek.', next: 'carrier' },
      { text: 'If I must verify the wax, I will own the sin.', next: 'carrier', effect: 'warn_seal_break' },
    ],
  },
  {
    id: 'who_paid',
    speaker: 'Brother Guiraut',
    text: 'Goldsmith in the river towns. Mold may still be under his floor. Viscount’s riders will want it. So will whoever hired the hand.',
    choices: [{ text: 'Names later. Who carries the bag?', next: 'carrier' }],
  },
  {
    id: 'carrier',
    speaker: 'Brother Guiraut',
    text: 'True sealed letter for Narbonne rides with you. Break that seal to read it and you become the next forger on this road. Pick who keeps the bag dry.',
    choices: [
      { text: 'Clerk takes it. Hands that know wax.', effect: 'carrier_clerk' },
      { text: 'Sergeant. If they take the bag, they take a fight.', effect: 'carrier_sergeant' },
      { text: 'Convers. He already carries the house keys.', effect: 'carrier_convers' },
    ],
  },
]
```

Effects: `carrier_clerk` | `carrier_sergeant` | `carrier_convers` → set `chest_carrier`, advance `act1_beat` to `road`.

---

## `pilgrim_mairia` — column on the wet road

```ts
pilgrim_mairia: [
  {
    id: 'start',
    speaker: 'Mairia of Quillan',
    text: 'West to Galicia if the ferries hold. We have bread for three days if nobody steals the mule. You smell of abbey wax. Are you road-guard or tithe-men?',
    choices: [
      { text: 'Neither. We walk you as far as Narbonne.', next: 'walk_with', effect: 'pilgrim_trust_up' },
      { text: 'Ask fewer questions. Keep the column tight.', next: 'tight', effect: 'pilgrim_trust_flat' },
      { text: 'Move aside. Our letter does not wait on mules.', next: 'cold', effect: 'pilgrim_trust_down' },
    ],
  },
  {
    id: 'walk_with',
    speaker: 'Mairia of Quillan',
    text: 'Then share the mud. Men in borrowed badges have been cutting the draille paths. They wear crosses that do not match their horses.',
    choices: [{ text: 'Show me where they cut.', effect: 'end_hook_bandits' }],
  },
  {
    id: 'tight',
    speaker: 'Mairia of Quillan',
    text: 'Tight we can do. Still — if you hear iron in the scrub before the mile marker, it is not pilgrims.',
    choices: [{ text: 'Understood.', effect: 'end_hook_bandits' }],
  },
  {
    id: 'cold',
    speaker: 'Mairia of Quillan',
    text: 'Then ride past. When the badges come, do not look back for our smoke.',
    choices: [{ text: '(Leave the column)', effect: 'end_column_cold' }],
  },
]
```

---

## `bandit_captain` — borrowed badges (ambush talk-first)

```ts
bandit_captain: [
  {
    id: 'start',
    speaker: 'Badge-Sergeant',
    text: 'Hospital work. Toll for the poor on the road. Open the chest and we count the charity.',
    choices: [
      { text: '[Clerk] Your badge is last year’s stamp. Wrong die.', next: 'call_bluff' },
      { text: '[Sergeant] Formation. Spears up. No one opens that chest.', next: 'fight', effect: 'start_alley_fight' },
      { text: '[Guide] Take the side path. Leave them the empty road.', next: 'slip', effect: 'slip_draille' },
      { text: 'Pay in coin, not relics.', next: 'bribe', effect: 'pay_toll' },
    ],
  },
  {
    id: 'call_bluff',
    speaker: 'Badge-Sergeant',
    text: '…Mud on the road makes stamps soft. Or you are clever. Clever men bleed the same.',
    choices: [
      { text: 'Walk away. We keep the chest.', effect: 'bandits_withdraw' },
      { text: 'Then come take it.', effect: 'start_alley_fight' },
    ],
  },
]
```

---

## `priest_ramon` — unburied child

```ts
priest_ramon: [
  {
    id: 'start',
    speaker: 'Father Ramon',
    text: 'Bells stay down. Burial ground is locked until a legate says otherwise. The child waits in the porch. Do not ask me for a mass I cannot say.',
    choices: [
      { text: '[Clerk] Record a lay burial. Ink is not a sacrament.', next: 'lay_burial', effect: 'child_burial_helped' },
      { text: '[Surgeon] The body will sour the street. Dig outside the wall.', next: 'outside', effect: 'child_burial_helped' },
      { text: 'We cannot linger. God keeps His own time.', next: 'refuse', effect: 'child_burial_refused' },
    ],
  },
  {
    id: 'lay_burial',
    speaker: 'Father Ramon',
    text: 'Write it. If they hang me for the page, hang me for the page. Bring the Convers for the shovel.',
    choices: [{ text: 'We dig at dusk.', effect: 'end_burial' }],
  },
  {
    id: 'outside',
    speaker: 'Father Ramon',
    text: 'Outside the wall is still earth. Do it quiet. The column is watching.',
    choices: [{ text: 'Quiet it is.', effect: 'end_burial' }],
  },
  {
    id: 'refuse',
    speaker: 'Father Ramon',
    text: 'Then keep your sealed letters. The road will remember who passed a porch like this.',
    choices: [{ text: '(Leave)', effect: 'end' }],
  },
]
```

---

## `goldsmith_house` — mold under the floor (inspection, then choice)

Inspection bark (no full tree needed): Convers finds the mold cavity; Sergeant notes the river-slick; Clerk reads the die against the false seal.

## `mold_choice` — viscount’s rider

```ts
mold_choice: [
  {
    id: 'start',
    speaker: 'Viscount’s Rider',
    text: 'Goldsmith’s already fish-food. The mold is the crime that walks. Hand it up and the viscount names you friends of order. Drown it and nobody names anybody.',
    choices: [
      { text: 'Give him the mold.', effect: 'mold_given_viscount' },
      { text: 'We drown it. No more seals from this die.', effect: 'mold_drowned' },
      { text: '[Clerk] We keep it as proof for Narbonne.', effect: 'mold_kept' },
    ],
  },
]
```

Aftermath lines (one-shots for UI / companion bark):
- `mold_given_viscount`: “He rides soft. Someone else still paid for the first seal.”
- `mold_drowned`: “Lead goes cold in the Aude. The letter in your bag is still warm.”
- `mold_kept`: “Proof that can hang you as easily as them. Keep the bag dry.”

---

## Objective / storyBeat strings (replace Merrowgate copy)

| Beat | storyBeat |
|---|---|
| start | Fontfroide. Take the chest. Do not break the true seal. |
| after_carrier | Walk the pilgrim road toward Narbonne. Keep the column fed and the bag dry. |
| after_bandits | Bandits cleared or slipped. Next: the parish with the locked burial ground. |
| after_parish | Goldsmith’s house by the river — find the mold. |
| after_mold | Mold settled. Reach the ferry before the roads tighten. |
| ferry | Cross toward Narbonne with the letter intact. |

---

## Party voice notes (short)
- **Clerk** — precise, legal, dry humor; never mystical.
- **Sergeant** — watch rotations, food, who stands where.
- **Convers** — keys, grain, quiet violence.
- **Guide** — which house lies, which path still takes strangers.
- **Surgeon** — bodies, time, boiled wine; prayer as atmosphere only.
