import type { DialogueNode, Item, PartyMember } from './types';

export const PLAYER_START = { x: 0, z: 2 };

export function createDefaultParty(): PartyMember[] {
  return [
    {
      id: 'rowan',
      name: 'Rowan Vale',
      role: 'Debt-marked investigator',
      stats: { hp: 28, maxHp: 28, mp: 10, maxMp: 10, atk: 7, def: 3 },
      recruited: true,
    },
    {
      id: 'mirelle',
      name: 'Mirelle Quill',
      role: 'Forgery clerk',
      stats: { hp: 18, maxHp: 18, mp: 16, maxMp: 16, atk: 5, def: 2 },
      recruited: false,
    },
  ];
}

export function createDefaultInventory(): Item[] {
  return [
    { id: 'inkknife', name: 'Inkknife', description: 'A thin blade that cuts parchment and skin alike.', qty: 1 },
    { id: 'salve', name: 'Canal Salve', description: 'Bitter paste. Restores a little vitality.', qty: 2 },
    { id: 'drowned_list', name: "Creditor's List", description: 'Water-stained. Your name is collateral.', qty: 1 },
  ];
}

/** Branching dialogue: confess debt vs deny — unlocks combat path / companion trust */
export const DIALOGUES: Record<string, DialogueNode[]> = {
  mirelle: [
    {
      id: 'start',
      speaker: 'Mirelle Quill',
      text: 'You smell of canal silt and panic. That drowned creditor washed up with a ledger page naming your party as collateral. Speak carefully — ink remembers.',
      choices: [
        { text: 'I never signed. Someone forged our names.', next: 'forge' },
        { text: 'The debt is real. Help me rewrite it before it wakes.', next: 'confess' },
        { text: 'Leave me alone.', next: 'leave' },
      ],
    },
    {
      id: 'forge',
      speaker: 'Mirelle Quill',
      text: 'Forgery is my trade. If the Ashen Ledger accepted a false hand, the curse still binds — but the true debtor may yet bleed for it. Meet me at the quay vault when you are ready to fight whatever ink spawns.',
      choices: [{ text: 'I will. Stand with me.', next: 'recruit_forge', effect: 'recruit_forge' }],
    },
    {
      id: 'confess',
      speaker: 'Mirelle Quill',
      text: 'Honesty in Merrowgate is a rare toxin. Rewrite means risk: burn a true line and the Ledger may birth a Warden to collect. I will stand with you — if you face it.',
      choices: [{ text: 'Then we face it together.', next: 'recruit_confess', effect: 'recruit_confess' }],
    },
    {
      id: 'recruit_forge',
      speaker: 'Mirelle Quill',
      text: 'Good. My pen is yours. A blot-wraith is already thickening near the east arch — clear it, and we earn the right to touch the Ledger.',
      choices: [{ text: '(Continue)', effect: 'end_recruit' }],
    },
    {
      id: 'recruit_confess',
      speaker: 'Mirelle Quill',
      text: 'Then we rewrite in blood and pigment. East arch — a blot-wraith guards the vault stair. Defeat it, and the Ledger will listen.',
      choices: [{ text: '(Continue)', effect: 'end_recruit' }],
    },
    {
      id: 'leave',
      speaker: 'Mirelle Quill',
      text: 'Then drown on your own schedule. The Ledger does not wait.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
    {
      id: 'after',
      speaker: 'Mirelle Quill',
      text: 'The east arch waits. Ink does not tire.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  dockhand: [
    {
      id: 'start',
      speaker: 'Dockhand Brin',
      text: 'Body came in on the morning tide — fingers still clenched on parchment. Ashen Ledger work. You look like the sort who ends up as ink.',
      choices: [
        { text: 'Where was the page headed?', next: 'where' },
        { text: 'Say nothing. Walk on.', effect: 'end' },
      ],
    },
    {
      id: 'where',
      speaker: 'Dockhand Brin',
      text: "Toward Quill's stall by the lantern bridge. She reads forgeries the way priests read omens.",
      choices: [{ text: 'Understood.', effect: 'end' }],
    },
  ],
};

export const NPCS = [
  { id: 'mirelle', name: 'Mirelle Quill', color: 0x6a4a8a, x: -3, z: -2, dialogueId: 'mirelle', hint: 'Talk to Mirelle' },
  { id: 'brin', name: 'Dockhand Brin', color: 0x4a6a5a, x: 4, z: 1, dialogueId: 'dockhand', hint: 'Talk to Brin' },
  { id: 'wraith', name: 'Blot-Wraith', color: 0x2a1018, x: 3, z: -4, dialogueId: '', hint: 'Engage Blot-Wraith', combat: true },
] as const;
