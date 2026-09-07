import type { DialogueNode, Item, PartyMember } from './types';

export const PLAYER_START = { x: 0, z: 3 };

/** Default formation L→R facing: guide · sergeant · convers · clerk · surgeon */
export function createDefaultParty(): PartyMember[] {
  return [
    {
      id: 'guide',
      name: 'Catalana',
      role: 'Guide',
      stats: { hp: 18, maxHp: 18, atk: 6, def: 2 },
      recruited: true,
    },
    {
      id: 'sergeant',
      name: 'Sergeant Guillem',
      role: 'Sergeant',
      stats: { hp: 28, maxHp: 28, atk: 8, def: 5 },
      recruited: true,
    },
    {
      id: 'convers',
      name: 'Brother Peire',
      role: 'Convers',
      stats: { hp: 22, maxHp: 22, atk: 5, def: 3 },
      recruited: true,
    },
    {
      id: 'clerk',
      name: 'Arnau the Clerk',
      role: 'Clerk',
      stats: { hp: 16, maxHp: 16, atk: 3, def: 2 },
      recruited: true,
    },
    {
      id: 'surgeon',
      name: 'Master Elias',
      role: 'Surgeon',
      stats: { hp: 14, maxHp: 14, atk: 2, def: 2 },
      recruited: true,
    },
  ];
}

export function createDefaultInventory(): Item[] {
  return [
    {
      id: 'true_letter',
      name: 'True Sealed Letter',
      description: 'For the Narbonne agent. Break the seal to peek and you become the next forger.',
      qty: 1,
    },
    {
      id: 'splinter',
      name: 'Relic Splinter',
      description: 'Sold as a saint’s staff — likely pine or stolen timber.',
      qty: 1,
    },
    {
      id: 'false_seal',
      name: 'Near-True Lead Seal',
      description: 'Almost a living pope’s die — wrong month / rim name. Fools a crowd.',
      qty: 1,
    },
    {
      id: 'bandages',
      name: 'Boiled Linen',
      description: 'Between-scene wrap. Surgeon prefers Stabilize in a fight.',
      qty: 2,
    },
  ];
}

export const DEFAULT_FLAGS: Record<string, boolean | string | number> = {
  chest_carrier: '',
  seal_intact: true,
  pilgrim_trust: 2,
  mold_fate: '',
  party_is_forger: false,
  act1_beat: 'start',
  ambush_done: false,
  ferry_done: false,
  talked_cellarer: false,
  talked_mairia: false,
  has_loft_ambush: false,
  warn_seal_break: false,
};

export const DIALOGUES: Record<string, DialogueNode[]> = {
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
    {
      id: 'after',
      speaker: 'Brother Guiraut',
      text: 'The bag is spoken for. Walk the pilgrim road. Do not break the true seal.',
      choices: [
        { text: 'Peek the true letter anyway.', effect: 'break_true_seal' },
        { text: '(Leave)', effect: 'end' },
      ],
    },
  ],
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
    {
      id: 'after',
      speaker: 'Mairia of Quillan',
      text: 'The mile marker still smells of iron. Clear the badges, or the ferry will feel it.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  bandit_captain: [
    {
      id: 'start',
      speaker: 'Badge-Sergeant',
      text: 'Hospital work. Toll for the poor on the road. Open the chest and we count the charity.',
      choices: [
        { text: '[Clerk] Your badge is last year’s stamp. Wrong die.', next: 'call_bluff' },
        { text: '[Sergeant] Formation. Spears up. No one opens that chest.', effect: 'start_ambush' },
        { text: '[Guide] Take the side path. Leave them the empty road.', effect: 'slip_draille' },
      ],
    },
    {
      id: 'call_bluff',
      speaker: 'Badge-Sergeant',
      text: '…Mud on the road makes stamps soft. Or you are clever. Clever men bleed the same.',
      choices: [
        { text: 'Walk away. We keep the chest.', effect: 'bandits_withdraw' },
        { text: 'Then come take it.', effect: 'start_ambush' },
      ],
    },
  ],
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
    {
      id: 'after',
      speaker: 'Viscount’s Rider',
      text: 'The mold is settled. The ferry waits.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  ferry_rope: [
    {
      id: 'start',
      speaker: 'Ferry Rope',
      text: '[PLACEHOLDER] Rope taut across the Aude watch. River men hold the far latch. Formation: Sergeant Holds while Convers Cuts.',
      choices: [
        { text: 'Form up — cut under Hold.', effect: 'start_ferry' },
        { text: 'Not yet.', effect: 'end' },
      ],
    },
  ],
};

export const NPCS = [
  {
    id: 'cellarer',
    name: 'Brother Guiraut',
    color: 0x6a6a58,
    x: -3.2,
    z: -1.2,
    dialogueId: 'cellarer',
    hint: 'Talk to the cellarer',
  },
  {
    id: 'mairia',
    name: 'Mairia of Quillan',
    color: 0x6a5038,
    x: 2.2,
    z: 2.0,
    dialogueId: 'pilgrim_mairia',
    hint: 'Talk to Mairia',
  },
  {
    id: 'bandits',
    name: 'Badge Bandits',
    color: 0x3a3028,
    x: 3.2,
    z: -3.8,
    dialogueId: 'bandit_captain',
    hint: 'Confront badge bandits',
    combat: true,
  },
  {
    id: 'mold',
    name: 'Viscount’s Rider',
    color: 0x4a4858,
    x: -2.0,
    z: -3.5,
    dialogueId: 'mold_choice',
    hint: 'Mold choice',
  },
  {
    id: 'ferry',
    name: 'Ferry Rope',
    color: 0x4a4030,
    x: 0.5,
    z: -5.0,
    dialogueId: 'ferry_rope',
    hint: 'Ferry crossing',
    combat: true,
  },
] as const;
