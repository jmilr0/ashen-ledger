# Parish + Narbonne depth (Act I stubs filled)

Wire after ambush / before mold for parish; after ferry for Narbonne agent.
Party names in code: Catalana (Guide), Sergeant Guillem, Brother Peire (Convers), Arnau the Clerk, Master Elias (Surgeon).

New flags:
- `child_burial`: helped | refused | deferred
- `narbonne_outcome`: delivered | refused_forger | letter_damaged | deferred_gate
- `talked_parish`: bool
- `talked_narbonne`: bool

---

## `priest_ramon` — parish porch (insert beat between ambush and mold)

NPC suggest: `{ id: 'parish', name: 'Father Ramon', x: ?, z: ?, dialogueId: 'priest_ramon', hint: 'Parish porch' }`
Gate: `ambush_done` true; optional soft gate if player walks past (toast only).

```ts
priest_ramon: [
  {
    id: 'start',
    speaker: 'Father Ramon',
    text: 'Bells stay down. Burial ground locked until a legate says the word. The child is in the porch. Do not ask me for a mass I cannot say.',
    choices: [
      { text: '[Clerk] Record a lay burial. Ink is not a sacrament.', next: 'lay_burial' },
      { text: '[Surgeon] Dig outside the wall before the street sours.', next: 'outside' },
      { text: '[Convers] I have a shovel. Say where.', next: 'lay_burial' },
      { text: 'We cannot linger.', next: 'refuse' },
    ],
  },
  {
    id: 'lay_burial',
    speaker: 'Father Ramon',
    text: 'Write it under my name if you must. Peire — dusk, quiet, no bell. The column is watching from the road.',
    choices: [
      { text: 'We dig at dusk.', effect: 'child_burial_helped' },
      { text: 'Mark it deferred — we return after the ferry.', effect: 'child_burial_deferred' },
    ],
  },
  {
    id: 'outside',
    speaker: 'Father Ramon',
    text: 'Outside the wall is still earth. Elias, keep the linen boiled. If the pilgrims sing, stop them.',
    choices: [{ text: 'Quiet burial. Then the river.', effect: 'child_burial_helped' }],
  },
  {
    id: 'refuse',
    speaker: 'Father Ramon',
    text: 'Then keep your sealed letters. Roads remember who passed a porch like this with dry hands.',
    choices: [
      { text: '(Leave)', effect: 'child_burial_refused' },
      { text: 'Wait — we dig. No mass.', next: 'lay_burial' },
    ],
  },
  {
    id: 'after',
    speaker: 'Father Ramon',
    text: 'The porch is empty. Go. The Aude does not wait on clerks.',
    choices: [{ text: '(Leave)', effect: 'end' }],
  },
]
```

Effect wiring:
- `child_burial_helped` → `child_burial=helped`, `pilgrim_trust+1` (cap 3), `talked_parish=true`, storyBeat → mold
- `child_burial_refused` → `child_burial=refused`, `pilgrim_trust-1` (floor 0), storyBeat → mold
- `child_burial_deferred` → `child_burial=deferred`, trust unchanged, storyBeat → mold (Act I can still close; Act II debt)

Companion bark one-shots (toast or line after effect):
- helped + Mairia present: “Mairia: They saw. The column eats quieter tonight.”
- refused: “Catalana: That porch will talk in every village to Narbonne.”

---

## `ferry_rope` — replace placeholder bark

```ts
ferry_rope: [
  {
    id: 'start',
    speaker: 'Ferryman Peire',
    text: 'Rope’s taut and watched. Far latch is theirs. You want the column across, Sergeant holds the planks while the Convers cuts — not the other way round.',
    choices: [
      { text: 'Form up — Hold, then Cut.', effect: 'start_ferry' },
      { text: '[Guide] There’s a sheep-gate downriver if trust buys silence.', next: 'alt', effect: 'ferry_alt_check' },
    ],
  },
  {
    id: 'alt',
    speaker: 'Ferryman Peire',
    text: 'Sheep-gate floods after rain. With friends in the column, maybe. Without them, you swim with the letter.',
    choices: [
      { text: 'We take the rope fight.', effect: 'start_ferry' },
      { text: 'Try the sheep-gate.', effect: 'start_ferry_sheepgate' }, // Design: same encounter, shoveWater easier if pilgrim_trust>=2
    ],
  },
]
```

---

## `narbonne_agent` — Act I closer (after ferry_done)

NPC: `{ id: 'narbonne', name: 'Narbonne Agent', dialogueId: 'narbonne_agent', hint: 'Deliver the letter' }`
Start node selected by flags (Engineering can pick start id in `startDialogue` like mold_choice after).

### Branch table
| Condition | start id |
|---|---|
| `seal_intact` && !`party_is_forger` | `clean` |
| `party_is_forger` \|\| !`seal_intact` | `forger` |
| default fallback | `clean` |

```ts
narbonne_agent: [
  {
    id: 'clean',
    speaker: 'Agent (Narbonne)',
    text: 'Wax unbroken. Good. Names first — goldsmith’s already river-meat. Who paid the die, and who copied the chancery hand?',
    choices: [
      { text: 'Mold drowned. Trail ends in the Aude.', next: 'ask_mold_drowned' },
      { text: 'Mold to the viscount. He rides soft.', next: 'ask_mold_given' },
      { text: 'We kept the mold. Proof for your table.', next: 'ask_mold_kept' },
    ],
  },
  {
    id: 'forger',
    speaker: 'Agent (Narbonne)',
    text: 'That seal has been open. You smell like every clerk who thought peeking was clever. Speak carefully — or the gate keeps the letter and not you.',
    choices: [
      { text: 'We broke it to verify the hand. Here is what we read.', next: 'forger_confess' },
      { text: 'The bag was forced on the road. The words are still true.', next: 'forger_lie' },
      { text: '[Clerk] Refuse the hand-off. We ride past if the legate has gone north.', effect: 'narbonne_deferred_gate' },
    ],
  },
  {
    id: 'ask_mold_drowned',
    speaker: 'Agent (Narbonne)',
    text: 'Then nobody mints from that die again. Pilgrims?',
    choices: [{ text: 'Report the column.', next: 'pilgrims' }],
  },
  {
    id: 'ask_mold_given',
    speaker: 'Agent (Narbonne)',
    text: 'Viscount has a leash. He will use it. You bought a friend who collects.',
    choices: [{ text: 'Report the column.', next: 'pilgrims' }],
  },
  {
    id: 'ask_mold_kept',
    speaker: 'Agent (Narbonne)',
    text: 'Put it on the table. If the die matches the false rim, Arnau, you just bought us a hanging — theirs or yours.',
    choices: [{ text: 'Hand over the mold and the letter.', next: 'pilgrims', effect: 'mold_to_agent' }],
  },
  {
    id: 'forger_confess',
    speaker: 'Agent (Narbonne)',
    text: 'Honesty keeps you breathing. The letter is stained. I can still ride the names north if the pilgrims are off the killing ground.',
    choices: [{ text: 'Report the column.', next: 'pilgrims', effect: 'narbonne_letter_damaged' }],
  },
  {
    id: 'forger_lie',
    speaker: 'Agent (Narbonne)',
    text: 'Bandits who open papal wax and leave the courier standing? Try again.',
    choices: [
      { text: 'Fine — we peeked.', next: 'forger_confess' },
      { text: 'Then keep your gate. We move the column anyway.', effect: 'narbonne_refused_forger' },
    ],
  },
  {
    id: 'pilgrims',
    speaker: 'Agent (Narbonne)',
    text: 'The west road is a magazine if a box leads them. Where is Mairia’s column?',
    choices: [
      { text: 'With us — off the killing ground.', next: 'close_good', effect: 'narbonne_delivered' },
      { text: 'Scattered. We chose the bag over the mule.', next: 'close_cold', effect: 'narbonne_delivered' },
    ],
  },
  {
    id: 'close_good',
    speaker: 'Agent (Narbonne)',
    text: 'Act I ends here: letter in, pilgrims breathing, priory still waiting in the Corbières. Do not open another seal for sport.',
    choices: [{ text: '(End Act I frame)', effect: 'end_act1' }],
  },
  {
    id: 'close_cold',
    speaker: 'Agent (Narbonne)',
    text: 'Letter in. Road hostile. You will feel that in the hills. Priory next — if you still have five walking.',
    choices: [{ text: '(End Act I frame)', effect: 'end_act1' }],
  },
]
```

Effect wiring:
- `narbonne_delivered` → `narbonne_outcome=delivered`, `talked_narbonne=true`
- `narbonne_letter_damaged` → `narbonne_outcome=letter_damaged`
- `narbonne_refused_forger` → `narbonne_outcome=refused_forger`
- `narbonne_deferred_gate` → `narbonne_outcome=deferred_gate`
- `mold_to_agent` → remove inventory `seal_mold` if present
- `end_act1` → storyBeat: use lines below; `act1_beat=narbonne_gate`

Pilgrim line auto-pick if you want zero player choice:
- `pilgrim_trust >= 2` → force `close_good` text
- `pilgrim_trust == 0` → force `close_cold`
- else offer both

### storyBeat after Act I
| Outcome | storyBeat |
|---|---|
| delivered + trust≥2 | Letter delivered. Pilgrims clear of the magazine road. Corbières priory waits (Act II). |
| delivered + trust≤1 | Letter delivered. Road behind you is hostile. Corbières priory waits. |
| letter_damaged | Letter stained but names ride. You are known as a peeker. Priory waits. |
| refused_forger | Gate kept you out. Column moved anyway. Act I ends ugly — priory still ahead. |
| deferred_gate | You rode past Narbonne. The legate may already be north. Priory is the only road left. |

---

## Optional: peek the true letter (inventory / camp action)

Only if Design/Eng expose it. One node:

```ts
peek_letter: [
  {
    id: 'start',
    speaker: 'Arnau the Clerk',
    text: 'Break this wax and every careful gate will smell it. The words inside will not fight for you.',
    choices: [
      { text: 'Break it. We need the names now.', effect: 'break_true_seal' },
      { text: 'Leave it sealed.', effect: 'end' },
    ],
  },
]
```

`break_true_seal` → `seal_intact=false`, `party_is_forger=true`, toast: “You are the next forger on this road.”
