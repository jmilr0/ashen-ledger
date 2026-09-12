export type Screen = 'title' | 'hub' | 'dialogue' | 'combat' | 'party' | 'inventory' | 'journal' | 'help' | 'epilogue';

export type JobId = 'clerk' | 'sergeant' | 'convers' | 'guide' | 'surgeon';

export type ChestCarrier = 'clerk' | 'sergeant' | 'convers';

export type MoldFate = '' | 'given_viscount' | 'drowned' | 'kept';

export type CombatEncounter = 'ambush' | 'ferry' | 'hold_door' | 'priory_yard';

export type MapZone = 'act1_road' | 'corbieres' | 'act3_close';

/** Portrait / select order: 1=guide … 5=surgeon */
export const SELECT_ORDER: JobId[] = ['guide', 'sergeant', 'convers', 'clerk', 'surgeon'];

export interface Stats {
  hp: number;
  maxHp: number;
  atk: number;
  def: number;
}

/** Hub equip — hand weapon / body armor (docs/stats-equip-sheet.md). */
export interface EquipSlots {
  hand?: string;
  body?: string;
}

export interface PartyMember {
  id: JobId;
  name: string;
  role: string;
  stats: Stats;
  /** Job base ATK/DEF before gear (persisted so refreshEquip is stable). */
  baseAtk: number;
  baseDef: number;
  equip: EquipSlots;
  recruited: boolean;
  /** Soft-fail for rest of Act I map. */
  outForAct?: boolean;
  bleeding?: boolean;
  bleedTicks?: number;
}

export type ItemSlot = 'hand' | 'body' | 'consumable' | 'quest';

export interface Item {
  id: string;
  name: string;
  description: string;
  qty: number;
  slot?: ItemSlot;
  atkBonus?: number;
  defBonus?: number;
  /** Soft job preference — toast if mismatched, still allow. */
  preferJobs?: JobId[];
}

/** World prop RMB: inspect / loot / use (docs/stats-equip-sheet.md). */
export type InteractKind = 'inspect' | 'loot' | 'use';

export interface WorldInteractable {
  id: string;
  kind: InteractKind;
  label: string;
  hint: string;
  /** Optional inventory grant on loot (once). */
  lootItemId?: string;
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

export type JournalStatus = 'active' | 'done' | 'failed' | 'locked';

export interface JournalEntry {
  id: string;
  title: string;
  body: string;
  status: JournalStatus;
  sort: number;
}

export interface SaveData {
  version: 1;
  party: PartyMember[];
  inventory: Item[];
  flags: Record<string, boolean | string | number>;
  playerX: number;
  playerZ: number;
  storyBeat: string;
  controlledId?: JobId;
  mapZone?: MapZone;
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
  /** RTwP: queued job action while paused / awaiting recover. */
  order?: string | null;
  /** RTwP: seconds until next action can fire. */
  recoverUntil?: number;
}

export interface NpcDef {
  id: string;
  name: string;
  color: number;
  x: number;
  z: number;
  dialogueId: string;
  hint: string;
  combat?: boolean;
}
