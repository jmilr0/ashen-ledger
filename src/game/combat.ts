import type { Combatant, CombatEncounter, JobId, PartyMember } from './types';

export type CombatActionId =
  | 'hold'
  | 'thrust'
  | 'shove'
  | 'club'
  | 'cut_rope'
  | 'kick_latch'
  | 'brace_wagon'
  | 'bolt'
  | 'slip'
  | 'point'
  | 'call_out'
  | 'staff'
  | 'show_seal'
  | 'stabilize'
  | 'drag';

const ALLY_ORDER: JobId[] = ['sergeant', 'convers', 'guide', 'clerk', 'surgeon'];

export interface CombatOptions {
  encounter: CombatEncounter;
  sealIntact: boolean;
  hasLoft?: boolean;
  shoveWater?: boolean;
  pilgrimTrust?: number;
  /** 'rtwp' (default) or 'rounds' debug fallback. */
  mode?: 'rtwp' | 'rounds';
}

/** Formation lane combat — jobs, not fantasy spells. */
export class CombatSession {
  allies: Combatant[];
  enemies: Combatant[];
  log: string[] = [];
  turn: 'player' | 'enemy' = 'player';
  over = false;
  victory = false;
  encounter: CombatEncounter;
  activeAllyId: JobId | null = null;
  badgesExposed = false;
  sealShownThisFight = false;
  sealIntact: boolean;
  hasLoft: boolean;
  shoveWater: boolean;
  ropeCut = false;
  /** Ferry win when Convers cuts rope while Sergeant held this round or last. */
  sergeantHeldThisRound = false;
  /** Front +1 def from Brace wagon; cleared at round end like Hold. */
  wagonBraced = false;
  /** Ferry: all River Watch down — Cut rope no longer needs Hold. */
  ferryWatchCleared = false;
  guideBoltHintShown = false;
  round = 1;
  /** RTwP: clock stopped while true. */
  paused = true;
  mode: 'rtwp' | 'rounds' = 'rtwp';
  /** Selected portrait under pause (reuse as activeAllyId for UI). */
  selectedAllyId: JobId | null = null;
  private holdRemain = 0;
  private braceRemain = 0;
  private bleedAcc = 0;
  private skirmishTime = 0;

  constructor(party: PartyMember[], opts: CombatOptions) {
    this.encounter = opts.encounter;
    this.sealIntact = opts.sealIntact;
    this.hasLoft = !!opts.hasLoft;
    this.shoveWater = !!opts.shoveWater;
    this.mode = opts.mode === 'rounds' ? 'rounds' : 'rtwp';
    this.paused = this.mode === 'rtwp';

    const available = party.filter((p) => p.recruited && !p.outForAct);
    this.allies = ALLY_ORDER.map((id) => available.find((p) => p.id === id))
      .filter((p): p is PartyMember => !!p)
      .map((p) => this.makeAlly(p));

    if (opts.encounter === 'ambush' || opts.encounter === 'priory_yard') {
      const yard = opts.encounter === 'priory_yard';
      this.enemies = [
        {
          id: yard ? 'picket_a' : 'bandit_a',
          name: yard ? 'Hugues Picket' : 'Badge Captain',
          hp: yard ? 16 : 18,
          maxHp: yard ? 16 : 18,
          atk: 7,
          def: 3,
          isPlayer: false,
          slot: 'frontL',
        },
        {
          id: yard ? 'picket_b' : 'bandit_b',
          name: yard ? 'Yard Blade' : 'Borrowed-Badge Thug',
          hp: 14,
          maxHp: 14,
          atk: 6,
          def: 2,
          isPlayer: false,
          slot: 'frontR',
        },
      ];
      this.log.push(
        yard
          ? 'Priory yard scuffle. Same jobs — clear the pickets.'
          : 'Borrowed-badge ambush on the wet road. Formation — Point then Call out if you can.'
      );
    } else {
      // ferry + hold_door (ferry pattern: Hold then Cut)
      const door = opts.encounter === 'hold_door';
      this.enemies = [
        {
          id: door ? 'nave_guard' : 'ferry_guard',
          name: door ? 'Nave Guard' : 'River Watch',
          hp: 16,
          maxHp: 16,
          atk: 6,
          def: 3,
          isPlayer: false,
          slot: 'frontL',
        },
        {
          id: door ? 'loft_blade' : 'ferry_thug',
          name: door ? 'Loft Blade' : 'Toll Blade',
          hp: 12,
          maxHp: 12,
          atk: 5,
          def: 2,
          isPlayer: false,
          slot: 'frontR',
        },
      ];
      const stress =
        (opts.pilgrimTrust ?? 2) <= 0
          ? ' Column is scattered — start stressed.'
          : '';
      this.log.push(
        door
          ? 'Nave door under pressure. Sergeant Holds; Convers Cuts the sheep-gate latch (Cut rope).' + stress
          : 'Ferry rope under pressure. Sergeant Holds; Convers must Cut rope to free the crossing.' + stress
      );
    }

    this.activeAllyId = this.nextAllyId(null);
    this.selectedAllyId = this.activeAllyId;
    if (this.mode === 'rtwp') {
      this.log.push('PAUSED — Space to resume. Queue one order per ally.');
      for (const a of this.allies) {
        a.order = null;
        a.recoverUntil = 0;
      }
      for (const e of this.enemies) {
        e.recoverUntil = 0.8 + Math.random() * 0.6;
      }
    }
  }

  togglePause(): void {
    if (this.over || this.mode !== 'rtwp') return;
    this.paused = !this.paused;
    this.log.push(this.paused ? 'PAUSED — Space to resume.' : 'LIVE.');
  }

  selectAlly(id: JobId): void {
    const a = this.allies.find((x) => x.memberId === id && x.hp > 0 && !x.downed);
    if (!a) return;
    this.selectedAllyId = id;
    this.activeAllyId = id;
  }

  /** Queue (or replace) an order for a living ally. Does not spend until live clock. */
  setOrder(job: JobId, action: CombatActionId): void {
    if (this.over) return;
    if (this.mode === 'rounds') {
      this.activeAllyId = job;
      this.act(action);
      return;
    }
    const ally = this.allies.find((a) => a.memberId === job && a.hp > 0 && !a.downed);
    if (!ally) return;
    this.selectedAllyId = job;
    this.activeAllyId = job;
    const allowed = this.actionsFor(job).find((x) => x.id === action && x.enabled);
    if (!allowed) {
      this.log.push(`${ally.name} cannot ${action} now.`);
      return;
    }
    ally.order = action;
    this.log.push(`${ally.name} ordered: ${allowed.label}.`);
  }

  /**
   * RTwP live tick. No-op when paused, over, or rounds mode.
   * TODO(GD feel-pass): tune recover / Hold duration once pause+portraits clickable.
   */
  update(dt: number): void {
    if (this.over || this.mode !== 'rtwp' || this.paused) return;
    this.skirmishTime += dt;
    this.holdRemain = Math.max(0, this.holdRemain - dt);
    this.braceRemain = Math.max(0, this.braceRemain - dt);
    if (this.holdRemain <= 0) {
      for (const a of this.allies) a.holding = false;
      this.sergeantHeldThisRound = false;
    }
    if (this.braceRemain <= 0) this.wagonBraced = false;

    for (const a of this.allies) {
      if (a.hp <= 0 || a.downed) continue;
      a.recoverUntil = Math.max(0, (a.recoverUntil ?? 0) - dt);
      if (a.order && (a.recoverUntil ?? 0) <= 0 && a.memberId) {
        const order = a.order as CombatActionId;
        a.order = null;
        this.executeFor(a.memberId, order);
        if (this.over) return;
        a.recoverUntil = this.recoverFor(a.memberId, order);
      }
    }

    for (const e of this.enemies) {
      if (e.hp <= 0 || e.downed) continue;
      e.recoverUntil = Math.max(0, (e.recoverUntil ?? 0) - dt);
      if ((e.recoverUntil ?? 0) <= 0) {
        this.enemyPulse(e);
        if (this.over) return;
        e.recoverUntil = 1.6 + Math.random() * 0.5;
      }
    }

    this.bleedAcc += dt;
    if (this.bleedAcc >= 2.5) {
      this.bleedAcc = 0;
      this.bleedTicks();
      this.checkEnd();
    }
  }

  private recoverFor(job: JobId, action: CombatActionId): number {
    if (action === 'hold') return 0.9;
    if (job === 'sergeant') return 1.2;
    if (job === 'surgeon') return 1.5;
    return 1.4;
  }

  /** Run one job action without advancing the round wizard. */
  private executeFor(job: JobId, action: CombatActionId): void {
    const prev = this.activeAllyId;
    const prevTurn = this.turn;
    this.activeAllyId = job;
    this.turn = 'player';
    // Temporarily bypass afterPlayerAction round gate via flag
    this._rtwpExecute = true;
    this.act(action);
    this._rtwpExecute = false;
    this.activeAllyId = this.selectedAllyId ?? prev;
    this.turn = prevTurn;
  }

  private _rtwpExecute = false;

  private enemyPulse(foe: Combatant): void {
    if (foe.wavering) {
      this.log.push(`${foe.name} wavers and skips the swing.`);
      foe.wavering = false;
      return;
    }
    const targets = this.living('allies');
    if (!targets.length) {
      this.checkEnd();
      return;
    }
    const front = targets.filter((t) => t.slot === 'frontL' || t.slot === 'frontR');
    const pool = front.length ? front : targets;
    const ally = pool[Math.floor(Math.random() * pool.length)];
    let def = ally.def;
    if (ally.slot === 'frontL' || ally.slot === 'frontR') def += this.frontDefBonus();
    const d = this.dmg(foe.atk, def);
    ally.hp = Math.max(0, ally.hp - d);
    this.log.push(`${foe.name} cuts for ${d}. ${ally.name}: ${ally.hp}/${ally.maxHp}`);
    if (ally.hp <= 0) {
      ally.downed = true;
      this.log.push(`${ally.name} is downed.`);
      this.paused = true;
      this.log.push('PAUSED — ally downed.');
    } else if (Math.random() < 0.35) {
      const was = ally.bleeding;
      ally.bleeding = true;
      ally.bleedTicks = ally.bleedTicks ?? 0;
      this.log.push(`${ally.name} is bleeding.`);
      if (!was) {
        this.paused = true;
        this.log.push('PAUSED — new bleeding.');
      }
    }
    this.checkEnd();
  }

  private makeAlly(p: PartyMember): Combatant {
    const slot = this.defaultSlot(p.id);
    return {
      id: `ally-${p.id}`,
      name: p.name,
      hp: p.stats.hp,
      maxHp: p.stats.maxHp,
      atk: p.stats.atk,
      def: p.stats.def,
      isPlayer: true,
      memberId: p.id,
      slot,
      bleeding: !!p.bleeding,
      bleedTicks: p.bleedTicks ?? 0,
      downed: p.stats.hp <= 0,
      holding: false,
    };
  }

  private defaultSlot(id: JobId): Combatant['slot'] {
    switch (id) {
      case 'sergeant':
        return 'frontL';
      case 'convers':
        return 'frontR';
      case 'clerk':
        return 'rearL';
      case 'surgeon':
        return 'rearR';
      case 'guide':
        return this.hasLoft ? 'loft' : 'rearL';
    }
  }

  living(side: 'allies' | 'enemies'): Combatant[] {
    return this[side].filter((c) => c.hp > 0 && !c.downed);
  }

  private orderedLivingAllies(): Combatant[] {
    return ALLY_ORDER.map((id) => this.allies.find((a) => a.memberId === id && a.hp > 0 && !a.downed)).filter(
      (a): a is Combatant => !!a
    );
  }

  private nextAllyId(after: JobId | null): JobId | null {
    const living = this.orderedLivingAllies();
    if (!living.length) return null;
    if (!after) return living[0].memberId ?? null;
    const idx = living.findIndex((a) => a.memberId === after);
    if (idx < 0 || idx >= living.length - 1) return null;
    return living[idx + 1].memberId ?? null;
  }

  activeAlly(): Combatant | null {
    if (!this.activeAllyId) return null;
    return this.allies.find((a) => a.memberId === this.activeAllyId && a.hp > 0 && !a.downed) ?? null;
  }

  actionsFor(job: JobId): { id: CombatActionId; label: string; enabled: boolean }[] {
    const a =
      this.allies.find((x) => x.memberId === job && x.hp > 0 && !x.downed) ?? null;
    if (!a) return [];
    // Rounds mode: only the active ally may act.
    if (this.mode === 'rounds') {
      const cur = this.activeAlly();
      if (!cur || cur.memberId !== job) return [];
    }
    const inLoft = a.slot === 'loft';
    const flankOk = this.hasLoft || inLoft;
    switch (job) {
      case 'sergeant':
        return [
          { id: 'hold', label: 'Hold line', enabled: true },
          { id: 'thrust', label: 'Thrust', enabled: this.living('enemies').length > 0 },
          {
            id: 'shove',
            label: this.shoveWater ? 'Shove (into water)' : 'Shove',
            enabled: this.living('enemies').length > 0,
          },
        ];
      case 'convers':
        return [
          { id: 'club', label: 'Club', enabled: this.living('enemies').length > 0 },
          {
            id: 'cut_rope',
            label: this.encounter === 'hold_door' ? 'Open sheep-gate' : 'Cut rope',
            enabled: (this.encounter === 'ferry' || this.encounter === 'hold_door') && !this.ropeCut,
          },
          {
            id: 'kick_latch',
            label: 'Kick latch',
            enabled: this.encounter === 'ambush',
          },
          { id: 'brace_wagon', label: 'Brace wagon', enabled: true },
        ];
      case 'guide': {
        const boltOk = flankOk && this.living('enemies').length > 0;
        if (!flankOk && !this.guideBoltHintShown) {
          this.guideBoltHintShown = true;
          this.log.push(`${a.name} has no loft angle yet.`);
        }
        return [
          { id: 'bolt', label: 'Bolt', enabled: boltOk },
          { id: 'slip', label: 'Slip → loft', enabled: this.hasLoft && !inLoft },
          { id: 'point', label: 'Point (expose badges)', enabled: this.encounter === 'ambush' && !this.badgesExposed },
        ];
      }
      case 'clerk':
        return [
          {
            id: 'call_out',
            label: 'Call out',
            enabled: this.badgesExposed && this.living('enemies').some((e) => !e.wavering),
          },
          { id: 'staff', label: 'Staff', enabled: this.living('enemies').length > 0 },
          {
            id: 'show_seal',
            label: 'Show seal',
            enabled: this.sealIntact && !this.sealShownThisFight,
          },
        ];
      case 'surgeon': {
        const someoneBleeding = this.allies.some((x) => x.bleeding && !x.downed);
        return [
          {
            id: 'stabilize',
            // No-op when nobody bleeding: label Tend kit so the softlock fix doesn't look broken.
            label: someoneBleeding ? 'Stabilize' : 'Tend kit',
            enabled: true,
          },
          {
            id: 'drag',
            label: 'Drag',
            enabled: this.allies.some((x) => x.downed || x.hp <= 0),
          },
        ];
      }
    }
  }

  private dmg(atk: number, def: number): number {
    return Math.max(1, atk - def + Math.floor(Math.random() * 3));
  }

  private frontDefBonus(): number {
    const sarge = this.allies.find((a) => a.memberId === 'sergeant');
    let bonus = sarge?.holding ? 2 : 0;
    if (this.wagonBraced) bonus += 1;
    return bonus;
  }

  private afterPlayerAction(): void {
    this.checkEnd();
    if (this.over) return;
    if (this._rtwpExecute || this.mode === 'rtwp') {
      // Duration-based Hold/Brace under RTwP
      const actor = this.activeAlly();
      if (actor?.holding) {
        this.holdRemain = 3;
        this.sergeantHeldThisRound = true;
      }
      if (this.wagonBraced) this.braceRemain = 3;
      // Auto-pause when ferry rope becomes cuttable
      if (
        this.encounter === 'ferry' &&
        !this.ropeCut &&
        (this.sergeantHeldThisRound || this.ferryWatchCleared)
      ) {
        /* stay as-is; player already paused often */
      }
      return;
    }
    const next = this.nextAllyId(this.activeAllyId);
    if (next) {
      this.activeAllyId = next;
      this.turn = 'player';
      return;
    }
    this.turn = 'enemy';
    this.enemyPhase();
    if (!this.over) {
      this.bleedTicks();
      this.checkEnd();
    }
    if (!this.over) {
      // clear Hold + Brace at end of full round after enemy+bleed
      for (const a of this.allies) a.holding = false;
      this.sergeantHeldThisRound = false;
      this.wagonBraced = false;
      this.round += 1;
      this.turn = 'player';
      this.activeAllyId = this.nextAllyId(null);
    }
  }

  act(action: CombatActionId, targetId?: string): void {
    if (this.over) return;
    if (this.mode === 'rtwp' && !this._rtwpExecute) {
      // UI buttons queue orders while paused (or replace while live)
      const job = this.selectedAllyId ?? this.activeAllyId;
      if (!job) return;
      this.setOrder(job, action);
      return;
    }
    if (this.turn !== 'player' && !this._rtwpExecute) return;
    const actor = this.activeAlly();
    if (!actor || !actor.memberId) return;
    const job = actor.memberId;
    const allowed = this.actionsFor(job).find((x) => x.id === action && x.enabled);
    if (!allowed) {
      this.log.push(`${actor.name} cannot ${action} now.`);
      return;
    }

    const foe =
      this.enemies.find((e) => e.id === targetId && e.hp > 0) ?? this.living('enemies')[0];

    switch (action) {
      case 'hold': {
        actor.holding = true;
        this.sergeantHeldThisRound = true;
        this.holdRemain = this.mode === 'rtwp' ? 3 : 0;
        this.log.push(`${actor.name} Holds the front line.`);
        break;
      }
      case 'thrust': {
        if (!foe) return;
        const d = this.dmg(actor.atk, foe.def);
        foe.hp = Math.max(0, foe.hp - d);
        this.log.push(`${actor.name} Thrusts for ${d}. ${foe.name}: ${foe.hp}/${foe.maxHp}`);
        if (foe.hp <= 0) foe.downed = true;
        break;
      }
      case 'shove': {
        if (!foe) return;
        if (this.shoveWater && Math.random() < 0.45) {
          foe.hp = 0;
          foe.downed = true;
          this.log.push(`${actor.name} Shoves ${foe.name} into the water.`);
        } else {
          const d = this.dmg(Math.max(2, actor.atk - 2), foe.def);
          foe.hp = Math.max(0, foe.hp - d);
          this.log.push(`${actor.name} Shoves ${foe.name} for ${d}.`);
          if (foe.hp <= 0) foe.downed = true;
        }
        break;
      }
      case 'club': {
        if (!foe) return;
        const d = this.dmg(actor.atk, foe.def);
        foe.hp = Math.max(0, foe.hp - d);
        this.log.push(`${actor.name} Clubs for ${d}. ${foe.name}: ${foe.hp}/${foe.maxHp}`);
        if (foe.hp <= 0) foe.downed = true;
        break;
      }
      case 'cut_rope': {
        if (!this.sergeantHeldThisRound && !this.ferryWatchCleared) {
          this.log.push('Rope frays — need Sergeant Hold before Cut rope lands clean.');
          // still spend the action; partial progress
          break;
        }
        this.ropeCut = true;
        this.log.push(
          this.ferryWatchCleared && !this.sergeantHeldThisRound
            ? `${actor.name} Cuts the ferry rope — watch down, crossing frees.`
            : `${actor.name} Cuts the ferry rope under Sergeant Hold — crossing frees.`
        );
        this.victory = true;
        this.over = true;
        return;
      }
      case 'kick_latch': {
        this.log.push(`${actor.name} Kicks a scrub latch — one flank opens.`);
        this.hasLoft = true;
        break;
      }
      case 'brace_wagon': {
        this.wagonBraced = true;
        this.braceRemain = this.mode === 'rtwp' ? 3 : 0;
        this.log.push(
          this.mode === 'rtwp'
            ? `${actor.name} Braces the wagon — front hardens briefly.`
            : `${actor.name} Braces the wagon — front hardens this round.`
        );
        break;
      }
      case 'bolt': {
        if (!foe) return;
        const d = this.dmg(actor.atk + 1, foe.def);
        foe.hp = Math.max(0, foe.hp - d);
        this.log.push(`${actor.name} looses a Bolt for ${d}. ${foe.name}: ${foe.hp}/${foe.maxHp}`);
        if (foe.hp <= 0) foe.downed = true;
        break;
      }
      case 'slip': {
        actor.slot = 'loft';
        this.log.push(`${actor.name} Slips to the loft.`);
        break;
      }
      case 'point': {
        this.badgesExposed = true;
        for (const e of this.enemies) e.badgesExposed = true;
        this.log.push(`${actor.name} Points — borrowed badges flash wrong. Clerk can Call out.`);
        if (this.mode === 'rtwp') {
          this.paused = true;
          this.log.push('PAUSED — badges exposed.');
        }
        break;
      }
      case 'call_out': {
        const target = this.living('enemies').find((e) => e.badgesExposed) ?? this.living('enemies')[0];
        if (!target) break;
        target.wavering = true;
        this.log.push(`${actor.name} Calls out the false badge — ${target.name} wavers (skips next attack).`);
        break;
      }
      case 'staff': {
        if (!foe) return;
        const d = this.dmg(Math.max(2, actor.atk - 2), foe.def);
        foe.hp = Math.max(0, foe.hp - d);
        this.log.push(`${actor.name} pokes with Staff for ${d}.`);
        if (foe.hp <= 0) foe.downed = true;
        break;
      }
      case 'show_seal': {
        this.sealShownThisFight = true;
        for (const e of this.living('enemies')) e.wavering = true;
        this.log.push(`${actor.name} Shows the intact seal — foes hesitate this round.`);
        break;
      }
      case 'stabilize': {
        const bleed = this.allies.find((x) => x.bleeding && !x.downed);
        if (!bleed) {
          this.log.push(`${actor.name} tends the kit — no one needs the iron.`);
          break;
        }
        bleed.bleeding = false;
        bleed.bleedTicks = 0;
        this.log.push(`${actor.name} Stabilizes ${bleed.name} — bleeding stopped.`);
        break;
      }
      case 'drag': {
        const down = this.allies.find((x) => x.downed || x.hp <= 0);
        if (!down) break;
        down.slot = 'rearR';
        down.downed = true;
        this.log.push(`${actor.name} Drags ${down.name} to the rear.`);
        break;
      }
    }

    this.afterPlayerAction();
  }

  private enemyPhase(): void {
    for (const foe of [...this.living('enemies')]) {
      if (foe.wavering) {
        this.log.push(`${foe.name} wavers and skips the swing.`);
        foe.wavering = false;
        continue;
      }
      const targets = this.living('allies');
      if (!targets.length) break;
      // prefer front rank
      const front = targets.filter((t) => t.slot === 'frontL' || t.slot === 'frontR');
      const pool = front.length ? front : targets;
      const ally = pool[Math.floor(Math.random() * pool.length)];
      let def = ally.def;
      if (ally.slot === 'frontL' || ally.slot === 'frontR') def += this.frontDefBonus();
      const d = this.dmg(foe.atk, def);
      ally.hp = Math.max(0, ally.hp - d);
      this.log.push(`${foe.name} cuts for ${d}. ${ally.name}: ${ally.hp}/${ally.maxHp}`);
      if (ally.hp <= 0) {
        ally.downed = true;
        this.log.push(`${ally.name} is downed.`);
      } else if (Math.random() < 0.35) {
        ally.bleeding = true;
        ally.bleedTicks = ally.bleedTicks ?? 0;
        this.log.push(`${ally.name} is bleeding.`);
      }
    }
  }

  private bleedTicks(): void {
    for (const a of this.allies) {
      if (!a.bleeding || a.downed) continue;
      a.bleedTicks = (a.bleedTicks ?? 0) + 1;
      this.log.push(`${a.name} bleeds (tick ${a.bleedTicks}/2).`);
      if (a.bleedTicks >= 2) {
        a.downed = true;
        a.hp = 0;
        this.log.push(`${a.name} is out for the Act — bleeding went untreated.`);
      }
    }
  }

  private checkEnd(): void {
    if (this.encounter === 'ferry' || this.encounter === 'hold_door') {
      if (this.ropeCut) {
        this.over = true;
        this.victory = true;
        return;
      }
      // Kill-all stresses/opens Cut but does not end the fight — victory is ropeCut only.
      if (!this.living('enemies').length && !this.ferryWatchCleared) {
        this.ferryWatchCleared = true;
        this.log.push('River watch down — rope still binds the crossing. Cut it.');
      }
      if (!this.living('allies').length) {
        this.over = true;
        this.victory = false;
        this.log.push('Formation collapses in the mud.');
      }
      return;
    }
    if (!this.living('enemies').length) {
      this.over = true;
      this.victory = true;
      this.log.push('Ambush broken. Borrowed badges lie in the mud.');
    } else if (!this.living('allies').length) {
      this.over = true;
      this.victory = false;
      this.log.push('Formation collapses in the mud.');
    }
  }

  applyToParty(party: PartyMember[]): void {
    for (const a of this.allies) {
      const m = party.find((p) => p.id === a.memberId);
      if (!m) continue;
      m.stats.hp = Math.max(0, a.hp);
      m.bleeding = !!a.bleeding;
      m.bleedTicks = a.bleedTicks ?? 0;
      if ((a.bleedTicks ?? 0) >= 2 || (a.downed && (a.bleedTicks ?? 0) >= 2)) {
        m.outForAct = true;
        m.bleeding = false;
      }
      if (a.downed && m.stats.hp <= 0 && !m.outForAct) {
        // downed but not out — limp at 1 hp after fight if surgeon present
        const surg = party.find((p) => p.id === 'surgeon' && !p.outForAct);
        if (surg) m.stats.hp = Math.max(1, Math.floor(m.stats.maxHp * 0.25));
        else m.stats.hp = 1;
      }
    }
  }
}
