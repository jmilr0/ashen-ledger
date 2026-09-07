export type Screen = 'title' | 'hub' | 'dialogue' | 'combat' | 'party' | 'inventory';

export type JobId = 'clerk' | 'sergeant' | 'convers' | 'guide' | 'surgeon';

export type ChestCarrier = 'clerk' | 'sergeant' | 'convers';

export type MoldFate = '' | 'given_viscount' | 'drowned' | 'kept';

export type CombatEncounter = 'ambush' | 'ferry';

export interface Stats {
  hp: number;
  maxHp: number;
  atk: number;
  def: number;
}

export interface PartyMember {
  id: JobId;
  name: string;
  role: string;
  stats: Stats;
  recruited: boolean;
  /** Soft-fail for rest of Act I map. */
  outForAct?: boolean;
  bleeding?: boolean;
  bleedTicks?: number;
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

export type FormationSlot = 'frontL' | 'frontR' | 'rearL' | 'rearR' | 'loft';

export interface Combatant {
  id: string;
  name: string;
  hp: number;
  maxHp: number;
  atk: number;
  def: number;
  isPlayer: boolean;
  memberId?: JobId;
  slot?: FormationSlot;
  holding?: boolean;
  bleeding?: boolean;
  bleedTicks?: number;
  downed?: boolean;
  wavering?: boolean;
  badgesExposed?: boolean;
}
