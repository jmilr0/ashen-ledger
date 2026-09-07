export type Screen = 'title' | 'hub' | 'dialogue' | 'combat' | 'party' | 'inventory';

export interface Stats {
  hp: number;
  maxHp: number;
  mp: number;
  maxMp: number;
  atk: number;
  def: number;
}

export interface PartyMember {
  id: string;
  name: string;
  role: string;
  stats: Stats;
  recruited: boolean;
}

export interface Item {
  id: string;
  name: string;
  description: string;
  qty: number;
}

export interface DialogueChoice {
  text: string;
  next?: string;
  effect?: string;
}

export interface DialogueNode {
  id: string;
  speaker: string;
  text: string;
  choices?: DialogueChoice[];
}

export interface SaveData {
  version: 1;
  party: PartyMember[];
  inventory: Item[];
  flags: Record<string, boolean | string | number>;
  playerX: number;
  playerZ: number;
  storyBeat: string;
}

export interface Combatant {
  id: string;
  name: string;
  hp: number;
  maxHp: number;
  atk: number;
  def: number;
  isPlayer: boolean;
  memberId?: string;
}
